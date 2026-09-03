#!/usr/bin/env python3
"""Custom QA test runner — Python + Selenium, no pytest / unittest.

Examples:
  python run_tests.py --list
  python run_tests.py --smoke
  python run_tests.py --regression --browser firefox --headed
  python run_tests.py --feature authentication --priority P0 P1
  python run_tests.py --test AUTH-001 --test AUTH-002
  python run_tests.py --regression --retries 1        # diagnostic re-runs only

Retries never turn a failure into a pass: FAIL -> retry PASS is reported as
FLAKY, with every attempt kept in the report.

Exit codes:
  0  every selected test passed (SKIPs are listed, not hidden)
  1  at least one FAIL, ERROR or FLAKY result
  2  usage or configuration error
  3  no test matched the selection
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

QA_ROOT = Path(__file__).resolve().parent
if str(QA_ROOT) not in sys.path:
    sys.path.insert(0, str(QA_ROOT))

try:
    import selenium  # noqa: F401
    import requests  # noqa: F401
except ImportError as missing:
    print(f"Missing dependency: {missing}. Run: pip install -r {QA_ROOT / 'requirements.txt'}")
    sys.exit(2)

from config.settings import load_settings  # noqa: E402
from core.artifacts import RunArtifacts  # noqa: E402
from core.context import TestContext  # noqa: E402
from core.exceptions import AssertionFailure, ConfigurationError, TestSkipped  # noqa: E402
from core.logger import configure_logging  # noqa: E402
from core.registry import PRIORITIES, TESTS, TestCase  # noqa: E402

TAG_FLAGS = ("smoke", "regression", "e2e", "integration")
STATUSES = ("PASS", "FAIL", "ERROR", "FLAKY", "SKIP")
PROBLEM_STATUSES = ("FAIL", "ERROR", "FLAKY")


# --------------------------------------------------------------------------- CLI
def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the QA automation suite.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    selection = parser.add_argument_group("selection")
    for flag in TAG_FLAGS:
        selection.add_argument(f"--{flag}", action="store_true", help=f"select tests tagged '{flag}'")
    selection.add_argument("--tag", action="append", default=[], metavar="TAG", help="select by tag (repeatable)")
    selection.add_argument("--exclude-tag", action="append", default=[], metavar="TAG", help="drop tests with this tag")
    selection.add_argument("--feature", action="append", default=[], metavar="NAME", help="select by feature (repeatable)")
    selection.add_argument("--priority", nargs="+", choices=PRIORITIES, default=[], metavar="P0", help="e.g. --priority P0 P1")
    selection.add_argument("--test", action="append", default=[], metavar="ID_OR_NAME", help="select by test id or function name")
    selection.add_argument("--list", action="store_true", help="print the selected tests and exit")

    environment = parser.add_argument_group("environment")
    environment.add_argument("--env", help="named environment from config/environments.py")
    environment.add_argument("--base-url")
    environment.add_argument("--api-base-url")
    environment.add_argument("--browser", choices=("chrome", "firefox", "edge"))
    mode = environment.add_mutually_exclusive_group()
    mode.add_argument("--headed", action="store_true")
    mode.add_argument("--headless", action="store_true")
    environment.add_argument("--reports-dir")

    execution = parser.add_argument_group("execution")
    execution.add_argument("--retries", type=int, default=0, help="diagnostic re-runs for FAIL/ERROR (result becomes FLAKY, never PASS)")
    execution.add_argument("--fail-fast", action="store_true", help="stop after the first FAIL/ERROR")
    execution.add_argument("--run-id", help="custom run id (default: timestamp)")
    execution.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def headless_override(args: argparse.Namespace):
    if args.headless:
        return True
    if args.headed:
        return False
    return None


# --------------------------------------------------------------------------- discovery / selection
def discover(tests_dir: Path) -> list[TestCase]:
    TESTS.clear()
    if not tests_dir.exists():
        raise ConfigurationError(f"tests directory not found: {tests_dir}")
    for path in sorted(tests_dir.rglob("test_*.py")):
        module_name = ".".join(path.relative_to(QA_ROOT).with_suffix("").parts)
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as error:  # noqa: BLE001
            raise ConfigurationError(f"cannot import {path.relative_to(QA_ROOT)}: {type(error).__name__}: {error}") from error
    return list(TESTS)


def select(tests: list[TestCase], args: argparse.Namespace) -> list[TestCase]:
    wanted_tags = {t.lower() for t in args.tag} | {flag for flag in TAG_FLAGS if getattr(args, flag)}
    excluded_tags = {t.lower() for t in args.exclude_tag}
    features = {f.lower() for f in args.feature}
    names = {n.lower() for n in args.test}

    selected = []
    for case in tests:
        tags = set(case.tags)
        if wanted_tags and not (tags & wanted_tags):
            continue
        if excluded_tags & tags:
            continue
        if features and case.feature.lower() not in features:
            continue
        if args.priority and case.priority not in args.priority:
            continue
        if names and case.id.lower() not in names and case.name.lower() not in names:
            continue
        selected.append(case)
    return sorted(selected, key=lambda c: (PRIORITIES.index(c.priority), c.id))


def print_selection(tests: list[TestCase]) -> None:
    if not tests:
        print("No tests matched the selection.")
        return
    width = max(len(t.id) for t in tests)
    for case in tests:
        browser = "browser" if case.needs_browser else "no-browser"
        print(f"{case.id:<{width}}  {case.priority}  {case.feature:<18} {case.name:<45} [{', '.join(case.tags)}] ({browser})")
    print(f"\n{len(tests)} test(s) selected")


# --------------------------------------------------------------------------- execution
def run_attempt(case: TestCase, settings, artifacts: RunArtifacts, log, attempt: int) -> dict:
    ctx = TestContext(case, settings, artifacts, log)
    started = time.perf_counter()
    status, message, error, evidence = "PASS", "", None, {}
    try:
        case.func(ctx)
    except TestSkipped as skipped:
        status, message = "SKIP", str(skipped)
    except AssertionFailure as failure:
        status, message, error = "FAIL", str(failure), failure
    except Exception as unexpected:  # noqa: BLE001 - every unexpected error is evidence, not noise
        status, message, error = "ERROR", f"{type(unexpected).__name__}: {unexpected}", unexpected

    if error is not None:
        try:
            evidence = artifacts.capture_failure(case.id, ctx.driver_if_created, error, attempt, ctx.evidence_context())
        except Exception as capture_error:  # noqa: BLE001
            log.warning("could not capture evidence for %s: %r", case.id, capture_error)
    ctx.finish(log)

    return {
        "attempt": attempt,
        "status": status,
        "message": message,
        "duration_s": round(time.perf_counter() - started, 3),
        "evidence": evidence,
        "attachments": list(ctx.attachments),
    }


def run_test(case: TestCase, settings, artifacts: RunArtifacts, log, retries: int) -> dict:
    attempts = [run_attempt(case, settings, artifacts, log, 1)]
    final = attempts[0]["status"]
    if final in ("FAIL", "ERROR") and retries > 0:
        for number in range(2, retries + 2):
            log.info("diagnostic retry %d/%d for %s", number - 1, retries, case.id)
            attempts.append(run_attempt(case, settings, artifacts, log, number))
            if attempts[-1]["status"] == "PASS":
                final = "FLAKY"
                break
            final = attempts[-1]["status"]

    if final == "FLAKY":
        message = f"initial {attempts[0]['status']}, passed on attempt {len(attempts)} — investigate, do not trust"
    else:
        message = attempts[-1]["message"]

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
        "attempts": attempts,
    }


# --------------------------------------------------------------------------- reporting
def totals_of(results: list[dict]) -> dict:
    return {status: sum(1 for r in results if r["status"] == status) for status in STATUSES}


def render_markdown(run: dict, totals: dict, results: list[dict]) -> str:
    lines = [f"# Execution report — run {run['run_id']}", ""]
    lines += [
        f"- Started: {run['started']}",
        f"- Finished: {run['finished']} ({run['duration_s']}s)",
        f"- Environment: {run['environment']['env_name']} — base_url={run['environment']['base_url']} api_base_url={run['environment']['api_base_url'] or '-'}",
        f"- Browser: {run['environment']['browser']} (headless={run['environment']['headless']}) — Selenium {run['selenium']} / Python {run['python']}",
        f"- Selection: {run['selection']}",
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
        lines.append(f"| {r['id']} | {r['feature']} | {r['priority']} | {r['status']} | {r['duration_s']}s | {message} |")

    problems = [r for r in results if r["status"] in PROBLEM_STATUSES]
    lines += ["", "## Failures requiring triage", ""]
    if not problems:
        lines.append("None.")
    for r in problems:
        lines += [f"### {r['id']} — {r['name']} ({r['status']})", "", f"Classification: **{r['classification']}** — classify with evidence before reporting (see failure-triage reference).", ""]
        for attempt in r["attempts"]:
            summary = attempt["message"].splitlines()[0] if attempt["message"] else ""
            lines.append(f"- Attempt {attempt['attempt']}: {attempt['status']} in {attempt['duration_s']}s" + (f" — {summary}" if summary else ""))
            for kind, value in attempt["evidence"].items():
                lines.append(f"  - {kind}: `{value}`")
            for attachment in attempt["attachments"]:
                lines.append(f"  - attachment: `{attachment}`")
        lines.append("")

    skipped = [r for r in results if r["status"] == "SKIP"]
    if skipped:
        lines += ["## Skipped", ""]
        lines += [f"- {r['id']}: {r['message']}" for r in skipped]
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
    return totals


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        settings = load_settings(
            env_name=args.env,
            base_url=args.base_url,
            api_base_url=args.api_base_url,
            browser=args.browser,
            headless=headless_override(args),
            reports_dir=args.reports_dir,
        )
        tests = discover(QA_ROOT / "tests")
    except ConfigurationError as error:
        print(f"Configuration error: {error}")
        return 2

    selected = select(tests, args)
    if args.list:
        print_selection(selected)
        return 0 if selected else 3
    if not selected:
        print("No tests matched the selection.")
        return 3

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    artifacts = RunArtifacts(settings.reports_dir, run_id)
    log = configure_logging(artifacts.root / "run.log", args.verbose)
    started = datetime.now(timezone.utc)
    log.info(
        "run %s — %d test(s) | env=%s base_url=%s browser=%s headless=%s",
        run_id, len(selected), settings.env_name, settings.base_url, settings.browser, settings.headless,
    )

    results: list[dict] = []
    for case in selected:
        log.info("── %s %s [%s · %s]", case.id, case.name, case.priority, case.feature)
        result = run_test(case, settings, artifacts, log, args.retries)
        results.append(result)
        first_line = result["message"].splitlines()[0] if result["message"] else ""
        log.info("[%s] %s (%.2fs)%s", result["status"], case.id, result["duration_s"], f" — {first_line}" if first_line else "")
        if args.fail_fast and result["status"] in ("FAIL", "ERROR"):
            log.warning("--fail-fast: stopping after %s", case.id)
            break

    finished = datetime.now(timezone.utc)
    run = {
        "run_id": run_id,
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "duration_s": round((finished - started).total_seconds(), 3),
        "environment": settings.redacted(),
        "selection": " ".join(argv if argv is not None else sys.argv[1:]),
        "python": sys.version.split()[0],
        "selenium": selenium.__version__,
        "reports_dir": str(artifacts.root),
    }
    totals = write_reports(artifacts, run, results)

    log.info(
        "summary: %d total | %d pass | %d fail | %d error | %d flaky | %d skip — reports in %s",
        len(results), totals["PASS"], totals["FAIL"], totals["ERROR"], totals["FLAKY"], totals["SKIP"], artifacts.root,
    )
    return 1 if any(r["status"] in PROBLEM_STATUSES for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
