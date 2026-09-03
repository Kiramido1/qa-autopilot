# QA automation suite (Python + Selenium, custom runner)

Generated from the `selenium-qa-automation` skill. No pytest, no unittest:
`run_tests.py` discovers, selects, executes and reports on its own.

## Setup

```bash
cd qa
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # fill in URLs and test accounts, never commit it
python run_tests.py --list
```

Chrome, Firefox or Edge must be installed. Selenium Manager fetches the matching
driver automatically; for offline CI point `QA_CHROMEDRIVER_PATH` /
`QA_GECKODRIVER_PATH` at local binaries.

## Running

```bash
python run_tests.py --smoke                              # tagged smoke
python run_tests.py --regression --browser firefox --headed
python run_tests.py --feature authentication --priority P0 P1
python run_tests.py --test AUTH-001 --test AUTH-002
python run_tests.py --e2e --retries 1                    # diagnostic retries only
```

Exit codes: `0` all passed (skips are listed) · `1` any FAIL / ERROR / FLAKY ·
`2` configuration error · `3` nothing selected. A test that fails and then
passes on retry is reported as **FLAKY**, never as PASS.

Every run writes `reports/<run-id>/` with `execution-report.md`, `report.json`,
`run.log` and per-test evidence (screenshot, page source, URL, browser console,
traceback, context) under `artifacts/<test-id>/`.

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
`require_credentials(role)`, `add_cleanup(fn, ...)`, `attach(name, content)`
and `screenshot(name)`. `browser=False` in the decorator marks tests that never
start a browser (API / integration checks).

## Layout

```
qa/
├── run_tests.py          custom runner (discovery, selection, retries, reports, exit codes)
├── config/               settings.py (env vars / .env) · environments.py (named envs)
├── core/                 driver · waits · base_page · assertions · artifacts · registry · context
├── pages/                Page Objects (locators + actions + readiness)
├── components/           reusable UI fragments (toast, modal, table...)
├── flows/                multi-page user journeys
├── integration/          api_client.py — requests-based checks with redacted evidence
├── data/                 factories.py (unique/boundary data) · fixtures.py (static reference data)
├── tests/                smoke/ · regression/ · e2e/ · integration/
└── reports/              generated, git-ignored
```

`pages/login_page.py`, `components/toast.py`, `flows/authentication.py` and
`tests/regression/test_login_example.py` are examples: replace their locators
and expectations with what the real application does.
