# Execution report

> Gates 13 / 21 — consolidated from the per-run reports under `../runs/`. A test is PASSED only if it actually
> ran and passed. Every FAIL/ERROR/FLAKY below carries a category from `references/failure-triage.md` and the
> evidence that decided it.

## Runs included
| Run id | Selection | Browser | Environment | Total | Passed | Failed | Errors | Flaky | Skipped | Duration |
|---|---|---|---|---|---|---|---|---|---|---|
| `20260903-132200` | all (phases A–F in one run; S-sized app) | chrome 151.0.7922.173 headless, driver 151 | local, build `demo-app@stale-dashboard` (git 425eb02f0930, dirty) | 14 | 12 | 0 | 2 | 0 | 0 | 30.7s |
| `20260903-132300` | `--rerun-failed` of the above, `--retries 1` | chrome 151 headless | same | 2 | 0 | 0 | 2 | 0 | 0 | 45.2s |
| `20260903-132400` | `--test ITEM-001 --repeat 5` | chrome 151 headless | same | 1 | 0 | 0 | 1 (0/5 passed) | 0 | 0 | 56.5s |
| `verify-demo` | all, against the build **without** the flag | chrome 151 headless | local, build `demo-app` | 14 | 14 | 0 | 0 | 0 | 0 | 10.7s |
| `demo-firefox` | `AUTH-001 AUTH-002 ITEM-001` | firefox 140.14.0 headless, geckodriver 0.33.0 | local, build `demo-app` | 3 | 3 | 0 | 0 | 0 | 0 | 9.9s |
| `demo-mobile` | `ENV-002 AUTH-001 --device "iPhone 12 Pro"` | chrome 151 mobile emulation | local, build `demo-app` | 2 | 2 | 0 | 0 | 0 | 0 | 2.1s |
| `demo-trace` | `ITEM-001 --a11y --trace` | chrome 151 headless | local, build `demo-app` | 1 | 1 | 0 | 0 | 0 | 0 | 2.7s |

Phase order inside `20260903-132200` (the runner sorts P0 first): A ENV-001/002/003 ✔ · B API-001, API-003,
AUTH-001, ENV-002, ITEM-001 (✗) · C API-002, AUTH-002/003/004, ITEM-002 (✗) · D/E/F are the tagged
subsets of the same 14 tests. Phase A was green before anything else was trusted (Gate 0 exit criterion).

## Coverage achieved
- Features: F-001 auth (AUTH-001..004, API-001), F-002 create (ITEM-001, API-002), F-003 delete (ITEM-002/003, API-003), F-004 scoping/IDOR (API-003/004), F-005 health (ENV-003) — every feature in the inventory has at least one executed test.
- Roles: user (all), admin (API-003 as the victim owner). Anonymous: AUTH-003, API-001.
- Journeys: login → dashboard → `/api/me` (AUTH-001); login → create → API → table (ITEM-001); seed via API → delete via dialog → API (ITEM-002); logout → direct URL (AUTH-004).
- APIs: 9 of 13 routes exercised; `POST /items`, `POST /items/<id>/delete` (reached through the UI), `/api/reset` and `/` are not called directly.
- Pages: `/login`, `/dashboard`. States: success toast, error banner (via API-002 only), cancelled dialog, deleted row. Empty state: not exercised.
- Negative paths: AUTH-002, AUTH-003, API-001, API-002 (3 rejects), API-003. Boundaries: API-002 (0/1/50/51/whitespace).
- Authorization: object-level (API-003), list scoping (API-004), anonymous (API-001, AUTH-003).
- Browsers: Chrome 151 (everything), Firefox 140 (3 tests), Chrome mobile emulation (2 tests).

## Confirmed application defects
- **BUG-001** → Dashboard renders the item list captured at login; items created or deleted afterwards do not appear until re-login → **High** → `defects.md`.
  - ITEM-001 `20260903-132200`: ERROR at `waits.until(table row containing 'Item …')` after 10 s on `/dashboard`.
    Evidence: `runs/20260903-132200/artifacts/ITEM-001/items-after-create.json` — `GET /api/items` → 200 **including** the new item (id 8, owner `qa.user@example.test`); `attempt1-page_source.html` — table rows are ids 1, 2 and 7 only; `attempt1-screenshot.png` — toast "Item … created" is visible above the stale table; `attempt1-browser_console.json` — no JS errors; `attempt1-network.json` — the only non-2xx request is the `favicon.ico` 404. The page had finished loading (readiness check passed before the wait). Classification: **REAL_APPLICATION_BUG** — the backend persisted the item, the UI never rendered it.
  - ITEM-002 `20260903-132200`: ERROR at `waits.until(table row containing 'Seeded …' gone)`. Evidence: `artifacts/ITEM-002/attempt1-page_source.html` still lists the seeded row after the confirm; `attempt1-context.json` → last API exchange `POST /api/items` 201 (the seed). Same root cause (the snapshot is read on every `dashboard()` render). Classification: **REAL_APPLICATION_BUG** — same defect, second symptom; not a separate bug.
  - Deterministic: `20260903-132300` (diagnostic retry) errored on both attempts for both tests; `20260903-132400` failed 5/5 with identical evidence. Not FLAKY.
  - Fixed build: `verify-demo` — ITEM-001 and ITEM-002 PASS, 14/14.

## Automation defects (fixed / open)
- **AUTH-003** (fixed before `20260903-132200`, during the vertical slice): the first version asserted `"/dashboard" not in current_url`; the URL at failure was `http://127.0.0.1:5000/login?next=/dashboard` — the redirect was correct and the assertion encoded a wrong assumption. Classification: **AUTOMATION_BUG**. Fix: compare `urlsplit(url).path == "/login"` (a *stronger* assertion, not a weaker one — the whole path is now checked, and the `?next=` behavior is documented in `test-cases.md`). Re-run: PASS in every run since.
- None open.

## Environment / infrastructure failures
- One discarded run before `20260903-132200`: every browser test ERROR `NoSuchDriverException` because Selenium Manager is missing from the Debian-packaged Selenium. Classification: **ENVIRONMENT_FAILURE**; fixed by `QA_CHROMEDRIVER_PATH=/usr/bin/chromedriver QA_CHROME_BINARY=/usr/bin/chromium` (recorded in `environment-map.md`). Google Chrome 152 is also installed but has no matching driver on this machine — Chromium 151 is used deliberately.

## Flaky tests under investigation
- None. ITEM-001 was measured (`--repeat 5` → 0/5) before being classified.

## Observations (non-failing)
- `demo-trace`: axe-core 4.10.2 on `/dashboard` reports 2 **moderate** violations — `landmark-one-main` (no `<main>` landmark) and `region` (content outside landmarks: `h1`, `label`, `#name`). Recorded in `coverage-gaps.md`; this is not a WCAG compliance statement. 7 per-action screenshots are under `artifacts/ITEM-001/trace/`.

## Remaining risks
- Gate 18: `POST /api/reset` is unauthenticated and the `next` redirect guard is a `startswith("/")` check (a `//host` value would pass). Both recorded in `repository-recon.md`; acceptable for a demo, P0 findings in a real product.
- Session expiry and password reset do not exist in the app — the corresponding cases are "needs product confirmation", not gaps in the suite.
- Only one browser ran the full suite; Firefox and mobile emulation covered the P0 journeys only.
