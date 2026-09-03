# QA automation suite (Python + Selenium, custom runner)

Generated from the `selenium-qa-automation` skill. No pytest, no unittest:
`run_tests.py` discovers, selects, executes and reports on its own, and
`--selftest` proves the runner itself (40 checks) before you trust a single result.

## Setup

```bash
cd qa
python -m venv .venv && source .venv/bin/activate   # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                # Windows: copy .env.example .env — fill in URLs and test accounts, never commit it
python run_tests.py --selftest                      # runner self-check, no browser needed
python run_tests.py --list
```

Chrome, Firefox or Edge must be installed. Selenium Manager fetches the
matching driver automatically; where it cannot (offline CI, Debian's packaged
Selenium) point `QA_CHROMEDRIVER_PATH` / `QA_GECKODRIVER_PATH` (and
`QA_CHROME_BINARY` if the browser is not on the default path) at local binaries.

## Running

```bash
python run_tests.py --smoke                              # Phase A: ENV-* tests, must be green before anything else
python run_tests.py --priority P0                        # Phase B
python run_tests.py --regression --browser firefox --headed
python run_tests.py --feature authentication --priority P0 P1
python run_tests.py --test AUTH-001 --test AUTH-002
python run_tests.py --e2e --retries 1                    # diagnostic retries: FAIL→PASS is FLAKY, never PASS
python run_tests.py --test ITEM-001 --repeat 5           # flakiness frequency (deterministic 5/5 or non-deterministic n/5)
python run_tests.py --rerun-failed 20260903-101500       # FAIL/ERROR/FLAKY tests of a previous run
python run_tests.py --regression --parallel 4            # module-level workers — only once the suite is green sequentially
python run_tests.py --test ITEM-001 --trace --a11y       # screenshot per action + axe-core observations
python run_tests.py --test ENV-002 --device "iPhone 12 Pro"
python run_tests.py --remote-url http://grid:4444/wd/hub --browser chrome --priority P0
python run_tests.py --traceability                       # regenerate ../qa-artifacts/traceability-matrix.md (cases + registry + last run + your classifications)
```

Exit codes: `0` all passed (skips are listed) · `1` any FAIL / ERROR / FLAKY or
hook failure · `2` configuration error · `3` nothing selected.

Every run writes `reports/<run-id>/`:

```
execution-report.md     totals, per-test results, failures with evidence links, observations
report.json             everything, machine-readable (input for --rerun-failed and --traceability)
junit.xml               for CI dashboards (FLAKY counts as a failure)
run.log                 the run log (workers/<module>.log in --parallel)
artifacts/<test-id>/    attemptN-screenshot.png · attemptN-page_source.html · attemptN-url.txt
                        attemptN-browser_console.json · attemptN-network.json (failed / non-2xx requests)
                        attemptN-exception.txt · attemptN-context.json (+ last API exchange)
                        attachments from ctx.attach() · trace/ (with --trace) · attemptN-a11y.json (with --a11y)
```

Evidence paths are relative to the run directory, so a report uploaded from
CI still points at files next to it. The run metadata records the browser and
driver version, the application's git SHA/branch (`QA_APP_REPO`, default: the
parent of `qa/`) and `QA_BUILD_ID` when set.

## Writing a test

```python
from core.assertions import assert_in
from core.registry import test
from pages.login_page import LoginPage


@test(id="AUTH-002", feature="authentication", priority="P1", tags=("regression", "negative"))
def test_login_with_invalid_password_shows_error(ctx):
    page = LoginPage(ctx.driver, ctx.settings).open()
    page.login("nobody@example.test", "wrong")
    assert_in("/login", ctx.driver.current_url, "left the login page with bad credentials")
```

`ctx` gives you `driver`, `waits`, `api`, `settings`, `log`, `skip(reason)`,
`require_credentials(role)`, `add_cleanup(fn, ...)`, `attach(name, content)`,
`screenshot(name)`, `login_once(role, login_fn)` (session reuse),
`a11y_scan()`, `observe(name, value)`, `ctx.session.store` and
`ctx.module.store`. `browser=False` in the decorator marks tests that never
start a browser (API / integration checks).

Hooks are plain functions: `setup_module(module)` / `teardown_module(module)`
in a test module, `setup_session(session)` / `teardown_session(session)` in
`tests/session_hooks.py`. Both contexts expose `settings`, `api`, `log`,
`store` and `add_cleanup`.

Locators: `core.locators.by_testid("login-submit")` (attribute name from
`QA_TESTID_ATTRIBUTE`), `by_role`, `by_label`, `by_text`. Components in
`components/`: `Table`, `Modal`, `NativeSelect`/`Listbox`, `Pagination`,
`FileUploader`, `Toast`.

## Layout

```
qa/
├── run_tests.py          CLI (selection, environment, execution modes, tools)
├── config/               settings.py (env vars / .env / CLI) · environments.py (named envs)
├── core/                 engine · driver · waits · base_page · assertions · artifacts · registry · context
│                         session (login_once) · redact · junit · traceability · a11y · trace · parallel · selftest
├── pages/                Page Objects (locators + actions + readiness)
├── components/           table · modal · dropdown · pagination · file_uploader · toast
├── flows/                multi-page user journeys
├── integration/          api_client.py — requests-based checks with redacted evidence
├── data/                 factories.py (unique/boundary data) · fixtures.py (static reference data)
├── tests/                smoke/ · regression/ · e2e/ · integration/ · session_hooks.py
└── reports/              generated, git-ignored
```

`pages/`, `flows/`, `components/toast.py` and everything under `tests/` are
examples that run green against the skill's bundled demo app
(`assets/demo-app/`). Replace their locators and expectations with what the
real application does.

## Windows notes

- Use `python` (not `python3`) and PowerShell paths: `.venv\Scripts\Activate.ps1`, `copy .env.example .env`.
- `--parallel` uses process spawning; keep test modules importable without side effects at import time.
- Chrome/Edge are found automatically; for Firefox set `QA_FIREFOX_BINARY` if it is not in `PATH`.
- `make` is optional — every target is a one-line `python run_tests.py ...` command shown above.

## Quality tooling

```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
mypy .
```
