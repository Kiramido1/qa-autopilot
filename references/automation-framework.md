# Automation framework — Gates 5 to 12

How to build the Python + Selenium automation layer. The bundled skeleton
(`assets/framework-skeleton/`, installed with `scripts/scaffold_qa.py`) already implements the
core of this; adapt it to the repository instead of rebuilding it, and never copy it blindly
into a project whose structure calls for something different.

Contents
- [Gate 5 — Architecture](#gate-5--architecture)
- [Gate 6 — Page objects & components](#gate-6--page-objects--components)
- [Gate 7 — Locator engineering](#gate-7--locator-engineering)
- [Gate 8 — Synchronization](#gate-8--synchronization)
- [Gate 9 — Test data](#gate-9--test-data)
- [Gate 10 — Custom test runner](#gate-10--custom-test-runner)
- [Gate 11 — Selenium implementation](#gate-11--selenium-implementation)
- [Gate 12 — Integration testing](#gate-12--integration-testing)

---

## Gate 5 — Architecture

Python + Selenium. No pytest. No unittest unless truly unavoidable (it is not, the runner exists).

```
qa/
├── config/        settings.py (env vars / .env / CLI precedence) · environments.py
├── core/          driver.py · base_page.py · waits.py · assertions.py · logger.py
│                  screenshots.py · artifacts.py · exceptions.py · registry.py · context.py
├── pages/         one Page Object per page
├── components/    navbar · modal · table · date picker · dropdown · pagination · toast · uploader
├── flows/         multi-page journeys (authentication, user management, checkout...)
├── integration/   api_client.py — requests-based backend checks
├── tests/         smoke/ · regression/ · e2e/ · integration/
├── data/          factories.py (unique + boundary data) · fixtures.py (static reference data)
├── reports/       generated per run (git-ignored)
└── run_tests.py   custom runner
```

Design it before implementing it: decide which pages, components and flows the feature
inventory needs, and which checks belong in `integration/` instead of the browser. Write that
mapping down (it becomes the "Automation" column of the traceability matrix).

Install the skeleton: `python <skill>/scripts/scaffold_qa.py <repo> --with-artifacts`. Existing
files are never overwritten, so it is safe on a repo that already has a `qa/` directory.

---

## Gate 6 — Page objects & components

Each page owns its locators, its UI actions, its page-specific synchronization and its readiness
check (`ready_locator` on `BasePage`). Pages return elements, text and state; they do not decide
whether the application is correct — business assertions live in tests and flows, so a page
stays reusable across positive and negative cases.

Components encapsulate reusable UI elements (navbar, sidebar, data table, date picker, modal,
dropdown, pagination, toast, file uploader) scoped to a root element (`BaseComponent`). A locator
that appears in two files is a maintenance bug: move it to the component that owns it.

Flows compose pages into journeys ("log in as admin, create a user, verify it in the table") so
tests read as business steps and page changes are absorbed in one place.

---

## Gate 7 — Locator engineering

Priority, highest first:

1. `data-testid`
2. stable `id`
3. stable `name`
4. accessible/semantic attributes (`role`, `aria-label`, label text)
5. stable CSS selectors
6. relative XPath
7. text-based selectors, only when the text is the thing under test

Avoid: absolute XPath · generated CSS classes (`css-1x2y3z`, `sc-...`) · random IDs ·
position-based selectors (`div:nth-child(4)`) · deep DOM chains · styling-dependent selectors.

Verify each locator against the rendered DOM (page source or dev tools), not the source
template — frameworks rewrite attributes. When nothing stable exists, recommend a test attribute
to the developers and record it in the recon notes:

```html
<button data-testid="submit-login">
```
instead of relying on
```xpath
/html/body/div[2]/div[1]/button
```

---

## Gate 8 — Synchronization

Never `time.sleep()` as the normal synchronization mechanism: it is either too short (flaky) or
too long (slow, and it hides the real wait that was needed).

Use the named explicit waits in `core/waits.py` and wait for meaningful states: element visible ·
clickable · present · absent · URL change · title change · page readiness · loading indicator
disappearance · text appearance · attribute change · number of elements · frame availability ·
alert presence.

Use sensible timeouts (default 10s, configurable via `QA_TIMEOUT`). Avoid very large timeouts;
they turn a real failure into a slow failure. The implicit wait is forced to 0 by the driver
factory so every wait is deliberate and shows up in the traceback with its name and the URL at
the time — that is what separates a SYNCHRONIZATION_FAILURE from a real defect.

---

## Gate 9 — Test data

Deterministic and isolated: unique users, unique emails, unique entities, role-specific accounts,
valid data, invalid data, boundary data, cleanup, reusable factories (`data/factories.py`).

Pattern: Arrange → Act → Assert → Cleanup. Register cleanup with `ctx.add_cleanup(...)` right
after creating a record, so it runs (LIFO) even when the assertion fails. Tests must be
independently executable, in any order; a test that needs a record another test created is
coupled and will fail on selection.

Prefer creating preconditions through the API (`ctx.api`) over clicking through the UI: faster,
and a failure in setup is then clearly a TEST_DATA_FAILURE rather than a feature failure.

Credentials come from environment variables / `.env` (never committed). Never point tests at
production data; verify the target environment before any destructive operation.

---

## Gate 10 — Custom test runner

Bundled as `run_tests.py`. Responsibilities: discovery · selection · tags · priorities · feature
filtering · setup · teardown · logging · screenshot capture · failure artifacts · exit codes ·
reports · optional diagnostic retries.

```bash
python run_tests.py --smoke
python run_tests.py --regression
python run_tests.py --e2e
python run_tests.py --integration
python run_tests.py --feature authentication
python run_tests.py --priority P0
python run_tests.py --test test_login_invalid_credentials      # or --test AUTH-002
python run_tests.py --browser firefox --headed
python run_tests.py --regression --retries 1                   # diagnostic only
```

Exit codes: 0 all passed · 1 any FAIL/ERROR/FLAKY · 2 configuration error · 3 nothing selected.
A failed test always yields a non-zero exit code; a FAIL that passes on retry is reported as
FLAKY (with every attempt recorded), never as PASS. Parallel execution is not built in; add it
with `concurrent.futures` per module once the suite is stable and data isolation is proven.

Tests are plain functions registered with the decorator:

```python
@test(id="USR-004", feature="user-management", priority="P1", tags=("regression",))
def test_deactivated_user_cannot_log_in(ctx):
    ...
```

`browser=False` marks API-only tests so no driver is started for them.

---

## Gate 11 — Selenium implementation

Implement incrementally and run after each step:

1. environment validation (ENV-* tests)
2. browser startup
3. authentication
4. critical smoke flows
5. core business workflows
6. negative flows
7. authorization
8. edge cases
9. cross-feature workflows
10. full regression

Use Selenium capabilities as needed: WebDriver · WebElement · explicit waits · expected
conditions · Actions (hover, drag, keyboard) · frames (`waits.frame`) · windows/tabs
(`driver.switch_to.window`) · alerts (`waits.alert`) · file uploads (`send_keys` on the file
input) · downloads (assert on `settings.downloads_dir`) · JavaScript only when necessary.

Do not use JavaScript to bypass normal user behavior (clicking hidden buttons, setting form
values directly, dismissing a modal the user would have to close). If JavaScript is required —
scrolling, reading a property the DOM does not expose — document why in the page object.

---

## Gate 12 — Integration testing

Use direct HTTP requests (`integration/api_client.py`) where they give stronger, faster
validation than the browser:

```
Selenium → real browser → frontend → API → backend → database     (E2E: cross-system behavior)
Python requests → API → backend → database                         (integration: isolated backend behavior)
```

Good integration checks: API contract validation · authentication behavior · authorization
(role × endpoint × object) · data creation · data consistency after a UI action · error
responses · state transitions.

Do not duplicate expensive UI tests when an API test provides stronger isolation, and when a UI
test fails, use the same client to ask the backend what it actually returned — that answer
usually decides between REAL_APPLICATION_BUG and AUTOMATION_BUG. Attach the exchange with
`ctx.attach("response.json", ctx.api.last_exchange())`; secrets in headers are redacted
automatically.
