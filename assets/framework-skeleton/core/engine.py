"""Execution engine behind run_tests.py: discovery, selection, hooks, the
per-test watchdog, diagnostic retries / repeat runs, evidence and reports.

Kept separate from the CLI so --parallel workers and --selftest can drive it
without re-parsing arguments.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import time
import traceback
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import selenium

from core.artifacts import RunArtifacts
from core.buildinfo import app_build_info
from core.context import ModuleContext, SessionContext, TestContext
from core.exceptions import AssertionFailure, ConfigurationError, TestSkipped, TestTimeout
from core.junit import write_junit
from core.registry import MODULES, PRIORITIES, TESTS, TestCase, register_module, reset

STATUSES = ("PASS", "FAIL", "ERROR", "FLAKY", "SKIP")
PROBLEM_STATUSES = ("FAIL", "ERROR", "FLAKY")
SESSION_HOOKS_FILE = "session_hooks.py"


@dataclass
class RunOptions:
    retries: int = 0  # diagnostic re-runs of FAIL/ERROR; result becomes FLAKY, never PASS
    repeat: int = 1  # run every selected test N times and report pass frequency
    timeout: float = 300.0  # per-test watchdog in seconds; 0 disables
    fail_fast: bool = False
    a11y: bool = False  # axe-core observations after every browser test
    verbose: bool = False


# --------------------------------------------------------------------------- discovery / selection
def discover(tests_dir: Path, qa_root: Path) -> list[TestCase]:
    reset()
    if not tests_dir.exists():
        raise ConfigurationError(f"tests directory not found: {tests_dir}")
    for path in sorted(tests_dir.rglob("test_*.py")):
        module_name = _module_name(path, tests_dir, qa_root)
        module = _import(path, module_name)
        register_module(module)
    return list(TESTS)


def load_session_hooks(tests_dir: Path, qa_root: Path) -> tuple[Optional[Callable], Optional[Callable]]:
    path = tests_dir / SESSION_HOOKS_FILE
    if not path.is_file():
        return None, None
    module = _import(path, _module_name(path, tests_dir, qa_root))
    return getattr(module, "setup_session", None), getattr(module, "teardown_session", None)


def _module_name(path: Path, tests_dir: Path, qa_root: Path) -> str:
    try:
        return ".".join(path.relative_to(qa_root).with_suffix("").parts)
    except ValueError:
        return "external." + ".".join(path.relative_to(tests_dir).with_suffix("").parts)


def _import(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConfigurationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:  # noqa: BLE001
        raise ConfigurationError(f"cannot import {path}: {type(error).__name__}: {error}") from error
    return module


def select(
    tests: Iterable[TestCase],
    tags: Iterable[str] = (),
    exclude_tags: Iterable[str] = (),
    features: Iterable[str] = (),
    priorities: Iterable[str] = (),
    names: Iterable[str] = (),
) -> list[TestCase]:
    wanted_tags = {t.lower() for t in tags}
    excluded = {t.lower() for t in exclude_tags}
    wanted_features = {f.lower() for f in features}
    wanted_priorities = set(priorities)
    wanted_names = {n.lower() for n in names}

    selected = []
    for case in tests:
        case_tags = set(case.tags)
        if wanted_tags and not (case_tags & wanted_tags):
            continue
        if excluded & case_tags:
            continue
        if wanted_features and case.feature.lower() not in wanted_features:
            continue
        if wanted_priorities and case.priority not in wanted_priorities:
            continue
        if wanted_names and case.id.lower() not in wanted_names and case.name.lower() not in wanted_names:
            continue
        selected.append(case)
    return sorted(selected, key=lambda c: (PRIORITIES.index(c.priority), c.id))


def ids_from_report(report_path: Path, statuses: Iterable[str] = PROBLEM_STATUSES) -> list[str]:
    """Test ids with a FAIL/ERROR/FLAKY result in a previous report.json (for --rerun-failed)."""
    if not report_path.is_file():
        raise ConfigurationError(f"report not found: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    wanted = set(statuses)
    return [r["id"] for r in report.get("results", []) if r.get("status") in wanted]


def group_by_module(cases: list[TestCase]) -> list[tuple[str, list[TestCase]]]:
    """Modules ordered by their most urgent test, tests inside keep P0-first order."""
    groups: dict[str, list[TestCase]] = {}
    for case in cases:
        groups.setdefault(case.module, []).append(case)
    return sorted(groups.items(), key=lambda item: min((PRIORITIES.index(c.priority), c.id) for c in item[1]))


# --------------------------------------------------------------------------- execution
class Runner:
    def __init__(self, settings, artifacts: RunArtifacts, log, options: RunOptions):
        self.settings = settings
        self.artifacts = artifacts
        self.log = log
        self.options = options
        self.hook_errors: list[dict] = []
        self.stopped = False

    # ---- whole run ------------------------------------------------------
    def run(self, cases: list[TestCase], session_hooks=(None, None), session_store: Optional[dict] = None) -> list[dict]:
        session = SessionContext(self.settings, self.artifacts, self.log, session_store)
        setup_session, teardown_session = session_hooks
        if setup_session is not None:
            error = self._call_hook("setup_session", setup_session, session)
            if error is not None:
                return [self._hook_failure_result(case, "setup_session", error) for case in cases]
        try:
            results = self.run_modules(cases, session)
        finally:
            if teardown_session is not None:
                self._call_hook("teardown_session", teardown_session, session)
            session.run_cleanups(self.log)
        return results

    def run_modules(self, cases: list[TestCase], session: SessionContext) -> list[dict]:
        results: list[dict] = []
        for module_name, module_cases in group_by_module(cases):
            if self.stopped:
                break
            results.extend(self.run_module(module_name, module_cases, session))
        return results

    def run_module(self, module_name: str, cases: list[TestCase], session: SessionContext) -> list[dict]:
        hooks = MODULES.get(module_name)
        module_ctx = ModuleContext(module_name, session, self.log)
        if hooks is not None and hooks.setup is not None:
            error = self._call_hook(f"setup_module[{module_name}]", hooks.setup, module_ctx)
            if error is not None:
                module_ctx.run_cleanups(self.log)
                return [self._hook_failure_result(case, "setup_module", error) for case in cases]
        results: list[dict] = []
        try:
            for case in cases:
                self.log.info("── %s %s [%s · %s]", case.id, case.name, case.priority, case.feature)
                result = self.run_test(case, session, module_ctx)
                results.append(result)
                first_line = result["message"].splitlines()[0] if result["message"] else ""
                self.log.info(
                    "[%s] %s (%.2fs)%s", result["status"], case.id, result["duration_s"], f" — {first_line}" if first_line else ""
                )
                if self.options.fail_fast and result["status"] in ("FAIL", "ERROR"):
                    self.log.warning("--fail-fast: stopping after %s", case.id)
                    self.stopped = True
                    break
        finally:
            if hooks is not None and hooks.teardown is not None:
                self._call_hook(f"teardown_module[{module_name}]", hooks.teardown, module_ctx)
            module_ctx.run_cleanups(self.log)
        return results

    # ---- one test -------------------------------------------------------
    def run_test(self, case: TestCase, session: SessionContext, module_ctx: Optional[ModuleContext]) -> dict:
        repeat = max(1, self.options.repeat)
        if repeat > 1:
            attempts = [self.run_attempt(case, session, module_ctx, number) for number in range(1, repeat + 1)]
            final, message, frequency = _summarize_repeat(attempts)
        else:
            frequency = None
            attempts = [self.run_attempt(case, session, module_ctx, 1)]
            final = attempts[0]["status"]
            if final in ("FAIL", "ERROR") and self.options.retries > 0:
                for number in range(2, self.options.retries + 2):
                    self.log.info("diagnostic retry %d/%d for %s", number - 1, self.options.retries, case.id)
                    attempts.append(self.run_attempt(case, session, module_ctx, number))
                    if attempts[-1]["status"] == "PASS":
                        final = "FLAKY"
                        break
                    final = attempts[-1]["status"]
            if final == "FLAKY":
                message = f"initial {attempts[0]['status']}, passed on attempt {len(attempts)} — investigate, do not trust"
            else:
                message = attempts[-1]["message"]

        browser = next((a["browser"] for a in attempts if a.get("browser")), None)
        observations: dict = {}
        for attempt in attempts:
            observations.update(attempt.get("observations") or {})
        return {
            "id": case.id,
            "name": case.name,
            "feature": case.feature,
            "priority": case.priority,
            "tags": list(case.tags),
            "module": case.module,
            "needs_browser": case.needs_browser,
            "status": final,
            "message": message,
            "classification": "UNCLASSIFIED" if final in PROBLEM_STATUSES else None,
            "duration_s": round(sum(a["duration_s"] for a in attempts), 3),
            "frequency": frequency,
            "browser": browser,
            "observations": observations or None,
            "attempts": attempts,
        }

    def run_attempt(self, case: TestCase, session: SessionContext, module_ctx: Optional[ModuleContext], attempt: int) -> dict:
        ctx = TestContext(case, self.settings, self.artifacts, self.log, session, module_ctx)
        outcome: dict = {}

        def invoke() -> None:
            try:
                case.func(ctx)
                outcome.update(status="PASS", message="", error=None)
            except TestSkipped as skipped:
                outcome.update(status="SKIP", message=str(skipped), error=None)
            except AssertionFailure as failure:
                outcome.update(status="FAIL", message=str(failure), error=failure)
            except Exception as unexpected:  # noqa: BLE001 - every unexpected error is evidence, not noise
                outcome.update(status="ERROR", message=f"{type(unexpected).__name__}: {unexpected}", error=unexpected)

        started = time.perf_counter()
        worker = threading.Thread(target=invoke, name=f"test-{case.id}-{attempt}", daemon=True)
        worker.start()
        worker.join(self.options.timeout if self.options.timeout and self.options.timeout > 0 else None)

        evidence: dict = {}
        if worker.is_alive():
            limit = self.options.timeout
            message = f"TestTimeout: exceeded {limit}s; the watchdog quit the driver to unblock the run"
            error = TestTimeout(message)
            evidence = self._capture_with_deadline(ctx, case, error, attempt, seconds=15)
            ctx.abort(message)
            worker.join(3)  # a browser test raises as soon as its driver is gone; a hung socket may not
            if worker.is_alive():
                self.log.warning("%s: test thread still running after abort; result recorded as ERROR", case.id)
            status = "ERROR"
        else:
            status, message, error = outcome["status"], outcome["message"], outcome["error"]
            if error is not None:
                try:
                    evidence = self.artifacts.capture_failure(case.id, ctx.driver_if_created, error, attempt, ctx.evidence_context())
                except Exception as capture_error:  # noqa: BLE001
                    self.log.warning("could not capture evidence for %s: %r", case.id, capture_error)

        if self.options.a11y and ctx.driver_if_created is not None and status in ("PASS", "FAIL"):
            try:
                ctx.a11y_scan(f"attempt{attempt}-a11y.json")
            except Exception as a11y_error:  # noqa: BLE001
                self.log.warning("a11y scan failed for %s: %r", case.id, a11y_error)

        ctx.finish(self.log)
        return {
            "attempt": attempt,
            "status": status,
            "message": message,
            "duration_s": round(time.perf_counter() - started, 3),
            "evidence": evidence,
            "attachments": list(ctx.attachments),
            "trace": list(ctx.trace_files) or None,
            "observations": ctx.observations or None,
            "browser": ctx.browser_info,
        }

    def _capture_with_deadline(self, ctx: TestContext, case: TestCase, error: BaseException, attempt: int, seconds: float) -> dict:
        """Evidence from a hung browser may itself hang; give it a bounded budget."""
        box: dict = {}

        def capture() -> None:
            try:
                box["evidence"] = self.artifacts.capture_failure(case.id, ctx.driver_if_created, error, attempt, ctx.evidence_context())
            except Exception as capture_error:  # noqa: BLE001
                box["error"] = repr(capture_error)

        thread = threading.Thread(target=capture, daemon=True)
        thread.start()
        thread.join(seconds)
        if "evidence" in box:
            return box["evidence"]
        path = self.artifacts.test_dir(case.id) / f"attempt{attempt}-exception.txt"
        path.write_text(
            f"{error}\n\n(evidence capture did not complete within {seconds}s: {box.get('error', 'browser unresponsive')})",
            encoding="utf-8",
        )
        return {"exception": self.artifacts.relative(path)}

    # ---- hooks ----------------------------------------------------------
    def _call_hook(self, name: str, hook: Callable, context) -> Optional[str]:
        try:
            hook(context)
            return None
        except Exception as error:  # noqa: BLE001
            detail = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            path = self.artifacts.root / "hooks" / f"{_safe(name)}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(detail, encoding="utf-8")
            summary = f"{name.split('[')[0]} failed: {type(error).__name__}: {error}"
            self.log.error("%s: %s (traceback: %s)", name, summary, self.artifacts.relative(path))
            self.hook_errors.append({"hook": name, "error": summary, "traceback": self.artifacts.relative(path)})
            return summary

    def _hook_failure_result(self, case: TestCase, hook: str, error: str) -> dict:
        message = f"HookError: {error}"
        return {
            "id": case.id,
            "name": case.name,
            "feature": case.feature,
            "priority": case.priority,
            "tags": list(case.tags),
            "module": case.module,
            "needs_browser": case.needs_browser,
            "status": "ERROR",
            "message": message,
            "classification": "UNCLASSIFIED",
            "duration_s": 0.0,
            "frequency": None,
            "browser": None,
            "observations": None,
            "attempts": [
                {
                    "attempt": 1,
                    "status": "ERROR",
                    "message": message,
                    "duration_s": 0.0,
                    "evidence": {},
                    "attachments": [],
                    "trace": None,
                    "observations": None,
                    "browser": None,
                }
            ],
        }


def _summarize_repeat(attempts: list[dict]) -> tuple[str, str, dict]:
    total = len(attempts)
    counts = {status: sum(1 for a in attempts if a["status"] == status) for status in ("PASS", "FAIL", "ERROR", "SKIP")}
    frequency = {**{k.lower(): v for k, v in counts.items()}, "total": total}
    if counts["SKIP"] == total:
        return "SKIP", attempts[-1]["message"], frequency
    if counts["PASS"] == total:
        return "PASS", f"passed {total}/{total}", frequency
    last_problem = next((a for a in reversed(attempts) if a["status"] in ("FAIL", "ERROR")), attempts[-1])
    if counts["PASS"] == 0:
        status = "FAIL" if counts["FAIL"] >= counts["ERROR"] else "ERROR"
        return status, f"failed {total}/{total} deterministically — {last_problem['message']}", frequency
    return "FLAKY", f"passed {counts['PASS']}/{total} — non-deterministic; investigate the cause, do not trust either outcome", frequency


def _safe(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in value)


# --------------------------------------------------------------------------- reporting
def totals_of(results: list[dict]) -> dict:
    return {status: sum(1 for r in results if r["status"] == status) for status in STATUSES}


def build_run_metadata(
    settings,
    run_id: str,
    started: datetime,
    finished: datetime,
    selection: str,
    options: RunOptions,
    parallel: int,
    results: list[dict],
    hook_errors: list[dict],
    reports_root: Path,
) -> dict:
    browser = next((r["browser"] for r in results if r.get("browser")), None)
    return {
        "run_id": run_id,
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "duration_s": round((finished - started).total_seconds(), 3),
        "environment": settings.redacted(),
        "build": app_build_info(settings.app_repo, settings.build_id),
        "browser": browser,
        "selection": selection,
        "options": asdict(options),
        "parallel": parallel,
        "python": sys.version.split()[0],
        "selenium": selenium.__version__,
        "reports_dir": str(reports_root),
        "hook_errors": hook_errors,
    }


def render_markdown(run: dict, totals: dict, results: list[dict]) -> str:
    env = run["environment"]
    build = run.get("build") or {}
    browser = run.get("browser") or {}
    browser_line = f"{env['browser']} (headless={env['headless']})"
    if browser.get("version"):
        browser_line += f" — {browser.get('name')} {browser['version']}" + (
            f", driver {browser['driver_version']}" if browser.get("driver_version") else ""
        )
    if env.get("mobile_device"):
        browser_line += f" — mobile emulation: {env['mobile_device']}"
    if env.get("remote_url"):
        browser_line += f" — remote: {env['remote_url']}"
    build_line = ", ".join(
        part
        for part in (
            f"build_id={build['build_id']}" if build.get("build_id") else "",
            f"git={build['git_sha'][:12]}" if build.get("git_sha") else "git=unknown",
            f"branch={build['git_branch']}" if build.get("git_branch") else "",
            "dirty" if build.get("git_dirty") else "",
        )
        if part
    )
    lines = [f"# Execution report — run {run['run_id']}", ""]
    lines += [
        f"- Started: {run['started']}",
        f"- Finished: {run['finished']} ({run['duration_s']}s)",
        f"- Environment: {env['env_name']} — base_url={env['base_url']} api_base_url={env['api_base_url'] or '-'}",
        f"- Application build: {build_line}",
        f"- Browser: {browser_line} — Selenium {run['selenium']} / Python {run['python']}",
        f"- Selection: `{run['selection']}`" + (f" — parallel={run['parallel']}" if run.get("parallel", 1) > 1 else ""),
        f"- Options: retries={run['options']['retries']} repeat={run['options']['repeat']} timeout={run['options']['timeout']}s a11y={run['options']['a11y']}",
        "",
        "## Totals",
        "",
        "| Total | Passed | Failed | Errors | Flaky | Skipped |",
        "|---|---|---|---|---|---|",
        f"| {len(results)} | {totals['PASS']} | {totals['FAIL']} | {totals['ERROR']} | {totals['FLAKY']} | {totals['SKIP']} |",
        "",
        "## Results",
        "",
        "| ID | Feature | Priority | Status | Duration | Message |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        message = r["message"].replace("\n", " ").replace("|", "\\|")[:160]
        freq = f" ({r['frequency']['pass']}/{r['frequency']['total']} passed)" if r.get("frequency") else ""
        lines.append(f"| {r['id']} | {r['feature']} | {r['priority']} | {r['status']}{freq} | {r['duration_s']}s | {message} |")

    problems = [r for r in results if r["status"] in PROBLEM_STATUSES]
    lines += ["", "## Failures requiring triage", ""]
    if not problems:
        lines.append("None.")
    for r in problems:
        lines += [
            f"### {r['id']} — {r['name']} ({r['status']})",
            "",
            f"Classification: **{r['classification']}** — classify with evidence before reporting (see failure-triage reference).",
            "",
        ]
        for attempt in r["attempts"]:
            summary = attempt["message"].splitlines()[0] if attempt["message"] else ""
            lines.append(
                f"- Attempt {attempt['attempt']}: {attempt['status']} in {attempt['duration_s']}s" + (f" — {summary}" if summary else "")
            )
            for kind, value in attempt["evidence"].items():
                lines.append(f"  - {kind}: `{value}`")
            for attachment in attempt["attachments"]:
                lines.append(f"  - attachment: `{attachment}`")
            if attempt.get("trace"):
                lines.append(f"  - trace: {len(attempt['trace'])} screenshots under `{attempt['trace'][0].rsplit('/', 1)[0]}/`")
        lines.append("")

    if run.get("hook_errors"):
        lines += ["## Hook failures", ""]
        lines += [f"- {h['hook']}: {h['error']} (`{h['traceback']}`)" for h in run["hook_errors"]]
        lines.append("")

    skipped = [r for r in results if r["status"] == "SKIP"]
    if skipped:
        lines += ["## Skipped", ""]
        lines += [f"- {r['id']}: {r['message']}" for r in skipped]
        lines.append("")

    observed = [r for r in results if r.get("observations")]
    if observed:
        lines += ["## Observations (non-failing)", ""]
        for r in observed:
            for name, value in r["observations"].items():
                lines.append(f"- {r['id']} · {name}: {json.dumps(value, default=str)}")
        lines.append("")

    lines += [
        "## Defects, automation defects, environment failures",
        "",
        "Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.",
        "",
        "## Remaining risks",
        "",
        "Fill in after triage (coverage gaps, untested areas, known flaky behavior).",
        "",
    ]
    return "\n".join(lines)


def write_reports(artifacts: RunArtifacts, run: dict, results: list[dict]) -> dict:
    totals = totals_of(results)
    report = {"run": run, "totals": totals, "results": results}
    (artifacts.root / "report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (artifacts.root / "execution-report.md").write_text(render_markdown(run, totals, results), encoding="utf-8")
    write_junit(artifacts.root / "junit.xml", run, results)
    return totals


# --------------------------------------------------------------------------- orchestration
def execute(
    settings,
    qa_root: Path,
    tests_dir: Path,
    cases: list[TestCase],
    options: RunOptions,
    log,
    run_id: str,
    selection: str = "",
    parallel: int = 1,
) -> tuple[int, dict]:
    """Run the selected cases and write the reports. Returns (exit_code, report)."""
    artifacts = RunArtifacts(settings.reports_dir, run_id)
    started = datetime.now(timezone.utc)
    log.info(
        "run %s — %d test(s) | env=%s base_url=%s browser=%s headless=%s parallel=%d",
        run_id,
        len(cases),
        settings.env_name,
        settings.base_url,
        settings.browser,
        settings.headless,
        parallel,
    )
    session_hooks = load_session_hooks(tests_dir, qa_root)
    if parallel > 1:
        from core.parallel import run_parallel

        results, hook_errors = run_parallel(settings, qa_root, tests_dir, cases, options, log, artifacts, session_hooks, parallel)
    else:
        runner = Runner(settings, artifacts, log, options)
        results = runner.run(cases, session_hooks)
        hook_errors = runner.hook_errors

    finished = datetime.now(timezone.utc)
    run = build_run_metadata(settings, run_id, started, finished, selection, options, parallel, results, hook_errors, artifacts.root)
    totals = write_reports(artifacts, run, results)
    log.info(
        "summary: %d total | %d pass | %d fail | %d error | %d flaky | %d skip — reports in %s",
        len(results),
        totals["PASS"],
        totals["FAIL"],
        totals["ERROR"],
        totals["FLAKY"],
        totals["SKIP"],
        artifacts.root,
    )
    exit_code = 1 if any(r["status"] in PROBLEM_STATUSES for r in results) or hook_errors else 0
    return exit_code, {"run": run, "totals": totals, "results": results}
