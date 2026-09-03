# Automation framework — Gates 5 to 12

How to build the Python + Selenium automation layer. The bundled skeleton
(`assets/framework-skeleton/`, installed with `scripts/scaffold_qa.py`) implements everything
below; adapt it to the repository instead of rebuilding it. Its README documents every flag and
helper; `--selftest` proves the runner on any machine in a few seconds.

Contents
- [Gate 5 — Architecture](#gate-5--architecture)
- [Extending an existing suite (conflict rule)](#extending-an-existing-suite-conflict-rule)
- [Gate 6 — Page objects & components](#gate-6--page-objects--components)
- [Gate 7 — Locator engineering](#gate-7--locator-engineering)
- [Gate 8 — Synchronization](#gate-8--synchronization)
- [Gate 9 — Test data, hooks and sessions](#gate-9--test-data-hooks-and-sessions)
- [Gate 10 — Custom test runner](#gate-10--custom-test-runner)
- [Gate 11 — Selenium implementation](#gate-11--selenium-implementation)
- [Gate 12 — Integration testing](#gate-12--integration-testing)

---

## Gate 5 — Architecture

Python + Selenium. No pytest, no unittest — the bundled runner exists so that a retried failure can
never become a pass and every attempt keeps its evidence.

```
qa/
├── run_tests.py   CLI: selection · environment · execution modes · tools (--selftest, --traceability)
├── config/        settings.py (CLI > env vars > .env > environments.py) · environments.py
├── core/          engine (discovery, hooks, watchdog, retries/repeat, reports) · driver · waits ·
│                  base_page · assertions · artifacts (evidence) · registry (@test) · context (ctx) ·
│                  session (login_once) · redact · junit · traceability · a11y · trace · parallel · selftest
├── pages/         one Page Object per page (locators + actions + readiness)
├── components/    table · modal · dropdown · pagination · file_uploader · toast (+ base_component)
├── flows/         multi-page journeys (authentication, ...)
├── integration/   api_client.py — requests with redacted evidence
├── data/          factories.py (unique + boundary data) · fixtures.py (static reference data)
├── tests/         smoke/ · regression/ · e2e/ · integration/ · session_hooks.py
└── reports/       generated per run, git-ignored
```

Design before implementing: which pages, components and flows the feature inventory needs, and
which checks belong in `integration/` instead of the browser. Write that mapping in
`test-strategy.md` — it becomes the "Automation" column of the generated traceability matrix.

Install: `python <skill>/scripts/scaffold_qa.py <repo> --with-artifacts`. Existing files are never
overwritten, so it is safe on a repo that already has `qa/`.

---

## Extending an existing suite (conflict rule)

If the project already has a browser suite (pytest-selenium, Playwright, Cypress, WebdriverIO…),
**extend it**; do not install a second runner unless the user asks. What carries over regardless of
runner:

- the gates and artifacts (`qa-artifacts/` next to the existing suite),
- test ids in test names or markers so `test-cases.md` can reference them (write the matrix by
  hand in that case, or point `--traceability` at a `report.json` you generate from their results),
- evidence per failure (screenshot, page source, URL, console, API exchange) — add fixtures/hooks
  in their framework to capture what `core/artifacts.py` captures,
- the triage categories, the flaky policy (measure with their repeat/rerun mechanism), the
  severity rubric and the defect format.

Say in the environment map which runner is in use and why.

---

## Gate 6 — Page objects & components

Each page owns its locators, its UI actions, its page-specific synchronization and its readiness
check (`path` + `ready_locator` on `BasePage`; `open()` waits for both). Pages return elements, text
and state; business assertions live in tests and flows so a page stays reusable across positive and
negative cases.

Components (`BaseComponent`, scoped to a root locator) encapsulate reusable UI: `Table` (rows by
text, cell by header, sort, wait for row / row gone), `Modal` (confirm / cancel / close /
wait_until_gone), `NativeSelect` and `Listbox`, `Pagination`, `FileUploader` (send_keys on the real
file input), `Toast`. Subclass and override the locators for the UI library in use (MUI, AG Grid,
Ant…); keep the methods. A locator that appears in two files is a maintenance bug — move it to the
component that owns it.

Flows compose pages into journeys (`flows/authentication.login_as(ctx, role)`) so tests read as
business steps and page changes are absorbed in one place.

---

## Gate 7 — Locator engineering

Priority, highest first:

1. `data-testid` (attribute name configurable: `QA_TESTID_ATTRIBUTE=data-test|data-cy|data-qa`) — `by_testid("login-submit")`
2. stable `id`
3. stable `name`
4. accessible/semantic attributes — `by_role("button", "Sign in")`, `by_label("Email")`
5. stable CSS selectors
6. relative XPath
7. visible text — `by_text("Delete")`, only when the text is the thing under test

Avoid: absolute XPath · generated CSS classes (`css-1x2y3z`, `sc-…`) · random ids · positional
selectors (`div:nth-child(4)`) · deep DOM chains · styling-dependent selectors.

Verify each locator against the rendered DOM (page source from a run, or dev tools), not the source
template — frameworks rewrite attributes. When nothing stable exists, recommend a test attribute to
the developers and record it in the recon notes:

```html
<button data-testid="submit-login">          <!-- instead of /html/body/div[2]/div[1]/button -->
```

---

## Gate 8 — Synchronization

Never `time.sleep()` as the synchronization mechanism: too short is flaky, too long is slow, and
either hides which state was actually awaited.

Use the named explicit waits in `core/waits.py` and wait for meaningful states: `visible` ·
`clickable` · `present` · `absent` · `all_visible` · `count_at_least` · `text_present` ·
`attribute_equals` · `loading_gone` · `page_ready` · `url_contains` · `url_changes` ·
`title_contains` · `frame` · `alert`, or `until(condition, "what you are waiting for")`.

Every wait names its state; a timeout raises `TimeoutException("<state> (waited Ns; url=…)")`, so a
SYNCHRONIZATION_FAILURE is distinguishable from the application never producing the state. Default
10 s (`QA_TIMEOUT`); avoid very large timeouts — they turn a real failure into a slow failure. The
driver factory forces the implicit wait to 0 so every wait is deliberate. A per-test watchdog
(`--timeout`, default 300 s) quits the driver of a hung test so one stuck page cannot stall a run.

---

## Gate 9 — Test data, hooks and sessions

Deterministic and isolated: unique users/emails/entities from `data/factories.py`
(`unique_name`, `unique_email`, `boundary_values`, `boundary_strings`, `SPECIAL_INPUTS`), role-specific
accounts from `.env`, cleanup registered right after creation with `ctx.add_cleanup(...)` (LIFO,
runs even after failure). Tests must run independently and in any order.

Preconditions through the API, not the UI: `setup_module(module)` / `teardown_module(module)` in a
test module and `setup_session(session)` / `teardown_session(session)` in `tests/session_hooks.py`
receive a context with `api`, `settings`, `log`, `store` and `add_cleanup`; tests read
`ctx.module.store` / `ctx.session.store`. A hook failure marks its tests ERROR with the traceback
under `reports/<run>/hooks/` — it never turns into a silent skip.

Session reuse: `ctx.login_once(role, login_fn)` drives the real login UI once per role per run,
then injects cookies + web storage into later tests (cuts runtime, removes one class of
flakiness). `--fresh-session` disables it for tests that are *about* logging in.

Credentials come from environment variables / `.env` (never committed, never in reports — the
framework redacts headers, bodies and query strings). Never point tests at production data;
verify the target environment before any destructive operation.

---

## Gate 10 — Custom test runner

`run_tests.py` — discovery · selection (`--smoke/--regression/--e2e/--integration`, `--tag`,
`--exclude-tag`, `--feature`, `--priority`, `--test`, `--rerun-failed <run-id>`) · environment
(`--env`, `--base-url`, `--api-base-url`, `--browser`, `--headed/--headless`, `--remote-url`,
`--device`) · execution (`--retries` diagnostic → FLAKY, `--repeat N` frequency, `--timeout`,
`--parallel N`, `--fail-fast`, `--fresh-session`, `--a11y`, `--trace`, `--run-id`) · tools
(`--selftest`, `--traceability`, `--list`).

Exit codes: 0 all passed (skips listed) · 1 any FAIL/ERROR/FLAKY or hook failure · 2 configuration
error · 3 nothing selected. Per run: `execution-report.md`, `report.json`, `junit.xml`, `run.log`,
`artifacts/<test-id>/…` with paths relative to the run directory (CI uploads stay valid).

Tests are plain functions:

```python
@test(id="USR-004", feature="user-management", priority="P1", tags=("regression",))
def test_deactivated_user_cannot_log_in(ctx):
    ...
```

`browser=False` marks API-only tests (no driver). `ctx` provides `driver`, `waits`, `api`, `settings`,
`log`, `skip(reason)`, `require_credentials(role)`, `add_cleanup`, `attach(name, content)`,
`screenshot(name)`, `login_once`, `observe(name, value)`, `a11y_scan()`.

Parallelism is per module (`ProcessPoolExecutor`, one driver per process, merged report). Use it
only once the suite is green sequentially — a parallel run surfaces data coupling as failures that
look like application bugs.

---

## Gate 11 — Selenium implementation

Implement incrementally and run after each step:

1. environment validation (ENV-* tests, `--smoke`)
2. browser startup
3. authentication (`flows/authentication.py`)
4. the vertical slice: one P0 journey end to end with API evidence
5. critical smoke flows
6. core business workflows
7. negative flows
8. authorization (mostly `integration/`)
9. edge cases
10. cross-feature workflows
11. full regression, then `--parallel`

Use Selenium capabilities as needed: explicit waits · expected conditions · `ActionChains` (hover,
drag, keyboard) · frames (`waits.frame`) · windows/tabs (`driver.switch_to.window`) · alerts
(`waits.alert`) · file uploads (`FileUploader`, send_keys on the file input) · downloads (assert on
`settings.downloads_dir`) · JavaScript only when necessary.

Do not use JavaScript to bypass user behavior (clicking hidden buttons, setting form values,
dismissing a modal the user would have to close). If JavaScript is required — scrolling, reading a
property the DOM does not expose — document why in the page object (`BasePage.scroll_into_view`
is the one sanctioned case).

---

## Gate 12 — Integration testing

Use direct HTTP requests (`integration/api_client.py`, `ctx.api`) where they give stronger, faster
validation than the browser:

```
Selenium → real browser → frontend → API → backend → database     E2E: cross-system behavior
Python requests → API → backend → database                         integration: isolated backend behavior
```

Good integration checks: API contract · authentication behavior · authorization (role × endpoint ×
object) · data creation · data consistency after a UI action (`ctx.api.set_cookies_from_driver`) ·
error responses · state transitions · boundaries (five requests instead of five page round-trips).

When a UI test fails, ask the backend what it actually returned with the same client — that answer
usually decides between REAL_APPLICATION_BUG and AUTOMATION_BUG. Attach it:
`ctx.attach("response.json", ctx.api.last_exchange())`; the runner also stores the last exchange in
`attemptN-context.json` automatically. Secrets in headers, bodies and query strings are redacted.
