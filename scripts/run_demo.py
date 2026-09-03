#!/usr/bin/env python3
"""Start the bundled demo app, run the framework skeleton against it, stop the app.

    python scripts/run_demo.py                      # full suite
    python scripts/run_demo.py --smoke              # any run_tests.py arguments pass through
    python scripts/run_demo.py --bugs stale-dashboard --test ITEM-001   # inject a demo defect

Environment variables QA_* are respected (e.g. QA_BROWSER=firefox,
QA_CHROMEDRIVER_PATH for offline machines). Exit code = the runner's exit code.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEMO_APP = SKILL_ROOT / "assets" / "demo-app" / "app.py"
SKELETON = SKILL_ROOT / "assets" / "framework-skeleton"


def wait_for(url: str, seconds: float = 20.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(0.25)
    return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=int(os.environ.get("DEMO_PORT", "5000")))
    parser.add_argument("--bugs", default="", help="DEMO_BUGS value for the demo app (e.g. stale-dashboard)")
    parser.add_argument("--keep-running", action="store_true", help="leave the demo app up after the run")
    args, runner_args = parser.parse_known_args(argv)

    base_url = f"http://127.0.0.1:{args.port}"
    env = {
        **os.environ,
        "DEMO_PORT": str(args.port),
        "DEMO_BUGS": args.bugs,
    }
    app = subprocess.Popen([sys.executable, str(DEMO_APP)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        if not wait_for(f"{base_url}/api/health"):
            print(f"demo app did not start on {base_url} (is Flask installed? pip install -r {DEMO_APP.parent / 'requirements.txt'})")
            return 2
        qa_env = {
            **env,
            "QA_BASE_URL": base_url,
            "QA_API_BASE_URL": base_url,
            "QA_API_HEALTH_PATH": "/api/health",
            "QA_BUILD_ID": env.get("QA_BUILD_ID") or f"demo-app{'@' + args.bugs if args.bugs else ''}",
        }
        qa_env.setdefault("QA_TEST_USER_EMAIL", "qa.user@example.test")
        qa_env.setdefault("QA_TEST_USER_PASSWORD", "Password123!")
        qa_env.setdefault("QA_ADMIN_EMAIL", "qa.admin@example.test")
        qa_env.setdefault("QA_ADMIN_PASSWORD", "Password123!")
        print(f"demo app up at {base_url} (bugs: {args.bugs or 'none'}); running: run_tests.py {' '.join(runner_args)}")
        return subprocess.call([sys.executable, str(SKELETON / "run_tests.py"), *runner_args], env=qa_env, cwd=str(SKELETON))
    finally:
        if not args.keep_running:
            app.terminate()
            try:
                app.wait(timeout=5)
            except subprocess.TimeoutExpired:
                app.kill()


if __name__ == "__main__":
    sys.exit(main())
