#!/usr/bin/env python3
"""Custom QA test runner — Python + Selenium, no pytest / unittest.

Examples:
  python run_tests.py --list
  python run_tests.py --smoke
  python run_tests.py --regression --browser firefox --headed
  python run_tests.py --feature authentication --priority P0 P1
  python run_tests.py --test AUTH-001 --test AUTH-002
  python run_tests.py --regression --retries 1          # diagnostic re-runs only
  python run_tests.py --test AUTH-002 --repeat 5        # flakiness frequency
  python run_tests.py --rerun-failed 20260903-101500    # FAIL/ERROR/FLAKY of a previous run
  python run_tests.py --regression --parallel 4         # only once the suite is green sequentially
  python run_tests.py --selftest                        # runner self-check, no browser needed
  python run_tests.py --traceability                    # regenerate qa-artifacts/traceability-matrix.md

Retries never turn a failure into a pass: FAIL -> retry PASS is reported as
FLAKY, with every attempt kept in the report.

Exit codes:
  0  every selected test passed (SKIPs are listed, not hidden)
  1  at least one FAIL, ERROR or FLAKY result (or a hook failure)
  2  usage or configuration error
  3  no test matched the selection
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

QA_ROOT = Path(__file__).resolve().parent
if str(QA_ROOT) not in sys.path:
    sys.path.insert(0, str(QA_ROOT))

try:
    import requests  # noqa: F401
    import selenium  # noqa: F401
except ImportError as missing:
    print(f"Missing dependency: {missing}. Run: pip install -r {QA_ROOT / 'requirements.txt'}")
    sys.exit(2)

from config.settings import load_settings  # noqa: E402
from core.engine import RunOptions, discover, execute, ids_from_report, select  # noqa: E402
from core.exceptions import ConfigurationError  # noqa: E402
from core.logger import configure_logging  # noqa: E402
from core.registry import PRIORITIES, TestCase  # noqa: E402

TAG_FLAGS = ("smoke", "regression", "e2e", "integration")


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
    selection.add_argument("--rerun-failed", metavar="RUN_ID", help="select the FAIL/ERROR/FLAKY tests of a previous run")
    selection.add_argument("--list", action="store_true", help="print the selected tests and exit")

    environment = parser.add_argument_group("environment")
    environment.add_argument("--env", help="named environment from config/environments.py")
    environment.add_argument("--base-url")
    environment.add_argument("--api-base-url")
    environment.add_argument("--browser", choices=("chrome", "firefox", "edge"))
    mode = environment.add_mutually_exclusive_group()
    mode.add_argument("--headed", action="store_true")
    mode.add_argument("--headless", action="store_true")
    environment.add_argument("--remote-url", metavar="URL", help="Selenium Grid / cloud provider command executor (or QA_REMOTE_URL)")
    environment.add_argument("--device", metavar="NAME", help="Chrome mobile emulation device, e.g. 'iPhone 12 Pro' (or QA_MOBILE_DEVICE)")
    environment.add_argument("--reports-dir")

    execution = parser.add_argument_group("execution")
    execution.add_argument("--retries", type=int, default=0, help="diagnostic re-runs for FAIL/ERROR (result becomes FLAKY, never PASS)")
    execution.add_argument("--repeat", type=int, default=1, metavar="N", help="run each selected test N times and report pass frequency")
    execution.add_argument(
        "--timeout", type=float, metavar="SECONDS", help="per-test watchdog (default QA_TEST_TIMEOUT or 300; 0 disables)"
    )
    execution.add_argument("--parallel", type=int, default=1, metavar="N", help="module-level parallel workers (default 1)")
    execution.add_argument("--fail-fast", action="store_true", help="stop after the first FAIL/ERROR")
    execution.add_argument("--fresh-session", action="store_true", help="disable ctx.login_once() session reuse")
    execution.add_argument("--a11y", action="store_true", help="run axe-core after every browser test (observations only)")
    execution.add_argument("--trace", action="store_true", help="screenshot after every page action")
    execution.add_argument("--run-id", help="custom run id (default: timestamp)")
    execution.add_argument("-v", "--verbose", action="store_true")

    tools = parser.add_argument_group("tools")
    tools.add_argument("--selftest", action="store_true", help="run the runner's internal self-test suite (no browser, no app)")
    tools.add_argument("--traceability", action="store_true", help="regenerate qa-artifacts/traceability-matrix.md and exit")
    tools.add_argument("--artifacts-dir", default=None, help="qa-artifacts directory for --traceability (default: ../qa-artifacts)")
    tools.add_argument("--from-run", metavar="RUN_ID", help="use this run's report.json for --traceability (default: latest)")

    args = parser.parse_args(argv)
    if args.retries < 0 or args.repeat < 1 or args.parallel < 1:
        parser.error("--retries must be >= 0, --repeat and --parallel must be >= 1")
    if args.retries and args.repeat > 1:
        parser.error("--retries and --repeat are mutually exclusive (retries diagnose, repeat measures frequency)")
    return args


def headless_override(args: argparse.Namespace):
    if args.headless:
        return True
    if args.headed:
        return False
    return None


def print_selection(tests: list[TestCase]) -> None:
    if not tests:
        print("No tests matched the selection.")
        return
    width = max(len(t.id) for t in tests)
    for case in tests:
        browser = "browser" if case.needs_browser else "no-browser"
        print(f"{case.id:<{width}}  {case.priority}  {case.feature:<18} {case.name:<45} [{', '.join(case.tags)}] ({browser})")
    print(f"\n{len(tests)} test(s) selected")


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    args = parse_args(argv)
    if args.selftest:
        from core.selftest import run_selftest

        return run_selftest(QA_ROOT, verbose=args.verbose)

    try:
        settings = load_settings(
            env_name=args.env,
            base_url=args.base_url,
            api_base_url=args.api_base_url,
            browser=args.browser,
            headless=headless_override(args),
            reports_dir=args.reports_dir,
            remote_url=args.remote_url,
            mobile_device=args.device,
            test_timeout=args.timeout,
            a11y=True if args.a11y else None,
            trace=True if args.trace else None,
            fresh_session=True if args.fresh_session else None,
        )
        tests_dir = QA_ROOT / "tests"
        tests = discover(tests_dir, QA_ROOT)
        names = list(args.test)
        if args.rerun_failed:
            names += ids_from_report(settings.reports_dir / args.rerun_failed / "report.json")
            if not names:
                print(f"Run {args.rerun_failed} has no FAIL/ERROR/FLAKY results; nothing to re-run.")
                return 3
    except ConfigurationError as error:
        print(f"Configuration error: {error}")
        return 2

    if args.traceability:
        from core.traceability import build_matrix

        artifacts_dir = Path(args.artifacts_dir) if args.artifacts_dir else QA_ROOT.parent / "qa-artifacts"
        matrix = build_matrix(tests, artifacts_dir / "test-cases.md", settings.reports_dir, QA_ROOT, args.from_run)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        target = artifacts_dir / "traceability-matrix.md"
        target.write_text(matrix, encoding="utf-8")
        print(f"wrote {target}")
        return 0

    wanted_tags = list(args.tag) + [flag for flag in TAG_FLAGS if getattr(args, flag)]
    selected = select(tests, tags=wanted_tags, exclude_tags=args.exclude_tag, features=args.feature, priorities=args.priority, names=names)
    if args.list:
        print_selection(selected)
        return 0 if selected else 3
    if not selected:
        print("No tests matched the selection.")
        return 3

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    options = RunOptions(
        retries=args.retries,
        repeat=args.repeat,
        timeout=settings.test_timeout,
        fail_fast=args.fail_fast,
        a11y=settings.a11y,
        verbose=args.verbose,
    )
    log = configure_logging(settings.reports_dir / run_id / "run.log", args.verbose)
    selection_label = " ".join(argv if argv is not None else sys.argv[1:])
    try:
        exit_code, _ = execute(settings, QA_ROOT, tests_dir, selected, options, log, run_id, selection_label, args.parallel)
    except ConfigurationError as error:
        print(f"Configuration error: {error}")
        return 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
