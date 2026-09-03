"""--parallel N: module-level parallelism with one process (and one driver at a
time) per worker. Results are merged into a single report by the parent.

Allowed only once the suite is green sequentially: parallel runs surface data
coupling between tests as failures that look like application bugs. Session
hooks run once in the parent; workers receive a copy of session.store.
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path


def run_parallel(settings, qa_root: Path, tests_dir: Path, cases, options, log, artifacts, session_hooks, workers: int):
    from core.context import SessionContext
    from core.engine import Runner, group_by_module

    session = SessionContext(settings, artifacts, log)
    parent = Runner(settings, artifacts, log, options)
    setup_session, teardown_session = session_hooks
    if setup_session is not None:
        error = parent._call_hook("setup_session", setup_session, session)
        if error is not None:
            return [parent._hook_failure_result(case, "setup_session", error) for case in cases], parent.hook_errors

    groups = group_by_module(cases)
    payloads = [
        {
            "qa_root": str(qa_root),
            "tests_dir": str(tests_dir),
            "module": module_name,
            "ids": [c.id for c in module_cases],
            "settings": _settings_overrides(settings),
            "options": asdict(options),
            "run_id": artifacts.run_id,
            "store": dict(session.store),
        }
        for module_name, module_cases in groups
    ]
    log.info("parallel: %d module(s) across %d worker(s)", len(payloads), workers)
    results: list[dict] = []
    hook_errors: list[dict] = list(parent.hook_errors)
    try:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for outcome in pool.map(run_module_worker, payloads):
                results.extend(outcome["results"])
                hook_errors.extend(outcome["hook_errors"])
                for line in outcome["log"]:
                    log.info("%s", line)
    finally:
        if teardown_session is not None:
            parent._call_hook("teardown_session", teardown_session, session)
        session.run_cleanups(log)
        hook_errors = hook_errors + [h for h in parent.hook_errors if h not in hook_errors]
    order = {case.id: index for index, case in enumerate(cases)}
    results.sort(key=lambda r: order.get(r["id"], len(order)))
    return results, hook_errors


def _settings_overrides(settings) -> dict:
    return {
        "env_name": settings.env_name,
        "base_url": settings.base_url,
        "api_base_url": settings.api_base_url,
        "browser": settings.browser,
        "headless": settings.headless,
        "reports_dir": str(settings.reports_dir),
        "test_timeout": settings.test_timeout,
        "a11y": settings.a11y,
        "trace": settings.trace,
        "fresh_session": settings.fresh_session,
        "remote_url": settings.remote_url,
        "mobile_device": settings.mobile_device,
    }


def run_module_worker(payload: dict) -> dict:
    qa_root = Path(payload["qa_root"])
    if str(qa_root) not in sys.path:
        sys.path.insert(0, str(qa_root))
    from config.settings import load_settings
    from core.artifacts import RunArtifacts
    from core.context import SessionContext
    from core.engine import Runner, RunOptions, discover
    from core.logger import configure_logging

    settings = load_settings(**payload["settings"])
    tests = discover(Path(payload["tests_dir"]), qa_root)
    wanted = set(payload["ids"])
    cases = [t for t in tests if t.id in wanted]
    artifacts = RunArtifacts(settings.reports_dir, payload["run_id"])
    log_file = artifacts.root / "workers" / f"{payload['module']}.log"
    options = RunOptions(**payload["options"])
    log = configure_logging(log_file, options.verbose, console=False)
    runner = Runner(settings, artifacts, log, options)
    session = SessionContext(settings, artifacts, log, payload["store"])
    results = runner.run_module(payload["module"], cases, session)
    session.run_cleanups(log)
    for handler in list(log.handlers):
        handler.flush()
        handler.close()
    lines = [f"[worker {payload['module']}] {r['status']} {r['id']} ({r['duration_s']}s)" for r in results]
    return {"results": results, "hook_errors": runner.hook_errors, "log": lines}
