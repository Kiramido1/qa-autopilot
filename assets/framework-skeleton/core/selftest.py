"""`run_tests.py --selftest`: exercises the runner itself without a browser or
an application, so runner regressions are caught before they hide test
results. Every check prints PASS/FAIL; the exit code is 1 on any failure.

Covered: PASS/FAIL/ERROR/SKIP/FLAKY mapping · exit codes · cleanup after
failure · module and session hooks (and their failure modes) · per-test
watchdog · --repeat frequency · --rerun-failed selection · relative evidence
paths · attachment redaction · JUnit output · --parallel worker path ·
duplicate-id detection · traceability generation (incl. classifications from the execution report).
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import textwrap
import traceback
from pathlib import Path

from config.settings import load_settings
from core.engine import RunOptions, discover, execute, ids_from_report, select
from core.exceptions import ConfigurationError
from core.logger import configure_logging

SUITE = {
    "session_hooks.py": """
        def setup_session(session):
            session.store["token"] = "session-value"
            session.add_cleanup(lambda: (session.settings.reports_dir / "session-cleanup.marker").write_text("ok"))

        def teardown_session(session):
            (session.settings.reports_dir / "session-teardown.marker").write_text("ok")
    """,
    "test_statuses.py": """
        import threading
        from pathlib import Path
        from core.assertions import assert_equal, assert_true
        from core.registry import test

        def setup_module(module):
            module.store["seeded"] = 42
            module.add_cleanup(lambda: (module.settings.reports_dir / "module-cleanup.marker").write_text("ok"))

        def teardown_module(module):
            (module.settings.reports_dir / "module-teardown.marker").write_text("ok")

        @test(id="ST-001", feature="selftest", priority="P0", tags=("smoke",), browser=False)
        def test_pass(ctx):
            assert_equal(ctx.module.store["seeded"], 42, "module store not visible")
            assert_equal(ctx.session.store["token"], "session-value", "session store not visible")

        @test(id="ST-002", feature="selftest", priority="P1", tags=("regression",), browser=False)
        def test_fail(ctx):
            ctx.add_cleanup(lambda: (ctx.settings.reports_dir / "cleanup-after-failure.marker").write_text("ok"))
            ctx.attach("secret.json", {"user": "qa", "password": "hunter2", "nested": {"api_key": "k"}})
            assert_equal(1, 2, "one is not two")

        @test(id="ST-003", feature="selftest", priority="P2", tags=("regression",), browser=False)
        def test_error(ctx):
            raise RuntimeError("boom")

        @test(id="ST-004", feature="selftest", priority="P3", tags=("regression",), browser=False)
        def test_skip(ctx):
            ctx.skip("precondition missing on purpose")

        @test(id="ST-005", feature="selftest", priority="P1", tags=("regression",), browser=False)
        def test_intermittent(ctx):
            marker = ctx.settings.reports_dir / "intermittent.counter"
            count = int(marker.read_text()) if marker.exists() else 0
            marker.write_text(str(count + 1))
            assert_true(count % 2 == 1, f"fails on odd attempts (attempt {count + 1})")

        @test(id="ST-006", feature="selftest", priority="P2", tags=("slow",), browser=False)
        def test_hangs(ctx):
            threading.Event().wait(20)
    """,
    "test_broken_module.py": """
        from core.registry import test

        def setup_module(module):
            raise RuntimeError("cannot seed")

        @test(id="ST-101", feature="selftest", priority="P2", tags=("regression",), browser=False)
        def test_never_runs(ctx):
            pass
    """,
}

DUPLICATE = """
    from core.registry import test

    @test(id="ST-001", feature="selftest", priority="P0", browser=False)
    def test_duplicate(ctx):
        pass
"""

TEST_CASES_MD = """# Test cases

## TC-ST-001 — runner reports a passing test
- Feature: selftest | Priority: P0 | Risk: Low
- Automation strategy: API — test id in code: `ST-001`

## TC-ST-002 — runner reports a failing assertion
- Feature: selftest | Priority: P1 | Risk: Low
- Automation strategy: API — test id in code: `ST-002`

## TC-ST-900 — not automated yet
- Feature: selftest | Priority: P3 | Risk: Low
- Automation strategy: manual
"""


class Checks:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition, detail: str = "") -> None:
        ok = bool(condition)
        self.results.append((name, ok, detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))

    @property
    def failed(self) -> int:
        return sum(1 for _, ok, _ in self.results if not ok)


def _write_suite(root: Path) -> Path:
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "__init__.py").write_text("")
    for name, source in SUITE.items():
        (tests_dir / name).write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
    return tests_dir


def run_selftest(qa_root: Path, verbose: bool = False) -> int:
    print("Runner self-test (no browser, no application)")
    checks = Checks()
    tmp = Path(tempfile.mkdtemp(prefix="qa-selftest-"))
    try:
        _run_checks(checks, qa_root, tmp, verbose)
    except Exception:  # noqa: BLE001
        checks.check("self-test completed without an internal error", False, traceback.format_exc())
    finally:
        logging.getLogger("qa").handlers.clear()
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(checks.results)
    print(f"\n{total - checks.failed}/{total} checks passed")
    return 1 if checks.failed else 0


def _run_checks(checks: Checks, qa_root: Path, tmp: Path, verbose: bool) -> None:
    tests_dir = _write_suite(tmp)
    reports = tmp / "reports"
    settings = load_settings(
        reports_dir=str(reports), base_url="http://selftest.invalid", api_base_url="http://selftest.invalid", test_timeout=2.0
    )
    log = configure_logging(reports / "selftest.log", verbose, console=verbose)

    # -- discovery & selection -------------------------------------------------
    tests = discover(tests_dir, qa_root)
    checks.check(
        "discovery finds every registered test",
        {t.id for t in tests} == {"ST-001", "ST-002", "ST-003", "ST-004", "ST-005", "ST-006", "ST-101"},
        str(sorted(t.id for t in tests)),
    )
    ordered = [t.id for t in select(tests)]
    checks.check("selection orders P0 first", ordered[0] == "ST-001" and ordered.index("ST-004") > ordered.index("ST-003"), str(ordered))
    checks.check("selection by tag", [t.id for t in select(tests, tags=["smoke"])] == ["ST-001"])
    checks.check("selection by id and name", [t.id for t in select(tests, names=["st-003", "test_skip"])] == ["ST-003", "ST-004"])
    checks.check("selection by priority", {t.priority for t in select(tests, priorities=["P0", "P1"])} == {"P0", "P1"})
    checks.check("empty selection stays empty", select(tests, tags=["nope"]) == [])

    # -- main run: statuses, hooks, evidence, junit -----------------------------
    main_cases = select(tests, exclude_tags=["slow"])
    options = RunOptions(retries=1, timeout=2.0, verbose=verbose)
    code, report = execute(settings, qa_root, tests_dir, main_cases, options, log, "selftest-main", "selftest", parallel=1)
    by_id = {r["id"]: r for r in report["results"]}
    checks.check("exit code 1 when anything failed", code == 1, str(code))
    checks.check("PASS status", by_id["ST-001"]["status"] == "PASS", by_id["ST-001"]["message"])
    checks.check(
        "FAIL status with expected/actual",
        by_id["ST-002"]["status"] == "FAIL" and "expected: 2" in by_id["ST-002"]["message"],
        by_id["ST-002"]["message"],
    )
    checks.check(
        "ERROR status for unexpected exception", by_id["ST-003"]["status"] == "ERROR" and "RuntimeError" in by_id["ST-003"]["message"]
    )
    checks.check("SKIP status with reason", by_id["ST-004"]["status"] == "SKIP" and "precondition" in by_id["ST-004"]["message"])
    checks.check(
        "FLAKY when a retry passes (never PASS)",
        by_id["ST-005"]["status"] == "FLAKY" and len(by_id["ST-005"]["attempts"]) == 2,
        by_id["ST-005"]["message"],
    )
    checks.check("retried FAIL keeps every attempt", [a["status"] for a in by_id["ST-002"]["attempts"]] == ["FAIL", "FAIL"])
    checks.check(
        "problem results start UNCLASSIFIED",
        all(by_id[i]["classification"] == "UNCLASSIFIED" for i in ("ST-002", "ST-003", "ST-005"))
        and by_id["ST-001"]["classification"] is None,
    )
    checks.check(
        "setup_module failure marks its tests ERROR",
        by_id["ST-101"]["status"] == "ERROR" and "setup_module failed" in by_id["ST-101"]["message"],
        by_id["ST-101"]["message"],
    )
    checks.check("hook failure recorded in run metadata", any("setup_module" in h["hook"] for h in report["run"]["hook_errors"]))
    checks.check("cleanup runs after a failed test", (reports / "cleanup-after-failure.marker").exists())
    checks.check(
        "module teardown and cleanups run", (reports / "module-teardown.marker").exists() and (reports / "module-cleanup.marker").exists()
    )
    checks.check(
        "session teardown and cleanups run",
        (reports / "session-teardown.marker").exists() and (reports / "session-cleanup.marker").exists(),
    )

    run_root = reports / "selftest-main"
    evidence = by_id["ST-002"]["attempts"][0]["evidence"]
    checks.check(
        "evidence paths are relative to the run directory",
        evidence.get("exception", "").startswith("artifacts/") and (run_root / evidence["exception"]).is_file(),
        str(evidence),
    )
    attachment = by_id["ST-002"]["attempts"][0]["attachments"][0]
    content = json.loads((run_root / attachment).read_text(encoding="utf-8"))
    checks.check(
        "attachments are relative and redacted",
        attachment.startswith("artifacts/")
        and content["password"] == "<redacted>"
        and content["nested"]["api_key"] == "<redacted>"
        and content["user"] == "qa",
        str(content),
    )
    checks.check(
        "report.json, execution-report.md, junit.xml written",
        all((run_root / f).is_file() for f in ("report.json", "execution-report.md", "junit.xml")),
    )
    junit = (run_root / "junit.xml").read_text(encoding="utf-8")
    checks.check(
        "junit counts: tests=6 failures=2 errors=2 skipped=1",
        'tests="6"' in junit and 'failures="2"' in junit and 'errors="2"' in junit and 'skipped="1"' in junit,
        junit[:300],
    )
    checks.check("junit marks FLAKY as a failure", 'type="FLAKY"' in junit)
    markdown = (run_root / "execution-report.md").read_text(encoding="utf-8")
    checks.check(
        "markdown report lists failures for triage",
        "## Failures requiring triage" in markdown and "ST-002" in markdown and "Application build" in markdown,
    )
    checks.check("run metadata records build info and options", "build" in report["run"] and report["run"]["options"]["retries"] == 1)

    # -- rerun-failed -------------------------------------------------------------
    rerun = ids_from_report(run_root / "report.json")
    checks.check("--rerun-failed selects FAIL/ERROR/FLAKY ids", set(rerun) == {"ST-002", "ST-003", "ST-005", "ST-101"}, str(rerun))

    # -- watchdog -------------------------------------------------------------
    hang = select(tests, names=["ST-006"])
    code, report = execute(
        settings, qa_root, tests_dir, hang, RunOptions(timeout=1.0, verbose=verbose), log, "selftest-timeout", "selftest", parallel=1
    )
    result = report["results"][0]
    checks.check(
        "watchdog turns a hung test into ERROR", result["status"] == "ERROR" and "TestTimeout" in result["message"], result["message"]
    )
    checks.check("watchdog fires near the limit (< 6s for a 20s hang)", result["duration_s"] < 6, str(result["duration_s"]))

    # -- repeat ------------------------------------------------------------------
    (reports / "intermittent.counter").unlink(missing_ok=True)
    code, report = execute(
        settings,
        qa_root,
        tests_dir,
        select(tests, names=["ST-005"]),
        RunOptions(repeat=4, verbose=verbose),
        log,
        "selftest-repeat",
        "selftest",
        parallel=1,
    )
    result = report["results"][0]
    checks.check(
        "--repeat reports FLAKY with pass frequency",
        result["status"] == "FLAKY" and result["frequency"] == {"pass": 2, "fail": 2, "error": 0, "skip": 0, "total": 4},
        str(result["frequency"]),
    )
    code, report = execute(
        settings,
        qa_root,
        tests_dir,
        select(tests, names=["ST-001"]),
        RunOptions(repeat=3, verbose=verbose),
        log,
        "selftest-repeat-pass",
        "selftest",
        parallel=1,
    )
    checks.check(
        "--repeat all-pass stays PASS with exit 0",
        code == 0 and report["results"][0]["status"] == "PASS" and report["results"][0]["frequency"]["pass"] == 3,
    )
    code, report = execute(
        settings,
        qa_root,
        tests_dir,
        select(tests, names=["ST-002"]),
        RunOptions(repeat=2, verbose=verbose),
        log,
        "selftest-repeat-fail",
        "selftest",
        parallel=1,
    )
    checks.check(
        "--repeat deterministic failure stays FAIL",
        report["results"][0]["status"] == "FAIL" and "deterministically" in report["results"][0]["message"],
    )

    # -- all green ----------------------------------------------------------------
    code, report = execute(
        settings,
        qa_root,
        tests_dir,
        select(tests, names=["ST-001"]),
        RunOptions(verbose=verbose),
        log,
        "selftest-green",
        "selftest",
        parallel=1,
    )
    checks.check("exit code 0 when everything passed", code == 0 and report["totals"]["PASS"] == 1)

    # -- parallel -----------------------------------------------------------------
    for marker in ("cleanup-after-failure.marker", "module-teardown.marker", "session-teardown.marker"):
        (reports / marker).unlink(missing_ok=True)
    (reports / "intermittent.counter").unlink(missing_ok=True)
    try:
        code, report = execute(
            settings,
            qa_root,
            tests_dir,
            main_cases,
            RunOptions(retries=1, timeout=2.0, verbose=verbose),
            log,
            "selftest-parallel",
            "selftest",
            parallel=2,
        )
        by_id = {r["id"]: r for r in report["results"]}
        statuses = {i: by_id[i]["status"] for i in ("ST-001", "ST-002", "ST-003", "ST-004", "ST-005", "ST-101")}
        checks.check(
            "--parallel produces the same statuses",
            statuses == {"ST-001": "PASS", "ST-002": "FAIL", "ST-003": "ERROR", "ST-004": "SKIP", "ST-005": "FLAKY", "ST-101": "ERROR"},
            str(statuses),
        )
        checks.check(
            "--parallel keeps worker logs and hooks",
            (reports / "selftest-parallel" / "workers").is_dir()
            and (reports / "session-teardown.marker").exists()
            and (reports / "module-teardown.marker").exists(),
        )
    except Exception as error:  # noqa: BLE001
        checks.check("--parallel worker path runs", False, repr(error))

    # -- duplicate ids ----------------------------------------------------------------
    duplicate = tests_dir / "test_duplicate.py"
    duplicate.write_text(textwrap.dedent(DUPLICATE).strip() + "\n", encoding="utf-8")
    try:
        discover(tests_dir, qa_root)
        checks.check("duplicate test ids are rejected at discovery", False)
    except ConfigurationError as error:
        checks.check("duplicate test ids are rejected at discovery", "Duplicate test id" in str(error), str(error))
    finally:
        duplicate.unlink()
        discover(tests_dir, qa_root)

    # -- session cookie sanitization (Firefox 154+ rejects SameSite=None without Secure) ----------
    from core.session import sanitize_cookie

    firefox_cookie = {
        "name": "session",
        "value": "x",
        "path": "/",
        "domain": "127.0.0.1",
        "secure": False,
        "httpOnly": True,
        "sameSite": "None",
        "expiry": 1.0,
    }
    cleaned = sanitize_cookie(firefox_cookie)
    checks.check(
        "session reuse drops SameSite=None on insecure cookies and keeps Lax/Strict",
        "sameSite" not in cleaned
        and cleaned["expiry"] == 1
        and sanitize_cookie({**firefox_cookie, "sameSite": "Lax"})["sameSite"] == "Lax"
        and "sameSite" in sanitize_cookie({**firefox_cookie, "secure": True}),
        str(cleaned),
    )

    # -- traceability --------------------------------------------------------------------
    from core.traceability import build_matrix

    artifacts = tmp / "qa-artifacts"
    artifacts.mkdir()
    (artifacts / "test-cases.md").write_text(TEST_CASES_MD, encoding="utf-8")
    matrix = build_matrix(discover(tests_dir, qa_root), artifacts / "test-cases.md", reports, qa_root, "selftest-main")
    checks.check(
        "traceability links cases to automation and results",
        "`ST-001`" in matrix and "PASS (selftest-main)" in matrix and "FAIL (selftest-main)" in matrix,
        matrix[:400],
    )
    checks.check(
        "traceability lists unautomated cases and orphan tests",
        "TC-ST-900" in matrix and "not automated" in matrix and "automation without a test case" in matrix,
    )
    checks.check("traceability shows UNCLASSIFIED until the execution report classifies", "UNCLASSIFIED" in matrix)
    (artifacts / "execution-report.md").write_text(
        "# Execution report\n\n## Confirmed application defects\n- ST-002 `selftest-main`: FAIL at assert_equal.\n"
        "  Evidence: attempt1-exception.txt. Classification: **REAL_APPLICATION_BUG** — BUG-001.\n",
        encoding="utf-8",
    )
    matrix = build_matrix(discover(tests_dir, qa_root), artifacts / "test-cases.md", reports, qa_root, "selftest-main")
    checks.check(
        "traceability picks up classifications from execution-report.md",
        "| REAL_APPLICATION_BUG |" in matrix and "| UNCLASSIFIED |" not in matrix.split("TC-ST-002")[1].split("\n")[0],
        matrix[-700:],
    )
