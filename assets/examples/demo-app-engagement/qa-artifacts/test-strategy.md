# Test strategy

> Gate 3 deliverable. Risk-based: P0 catastrophic → P1 business-critical → P2 important → P3 secondary.

## Scope and priorities
- In scope: F-001 authentication, F-002 item creation, F-003 deletion with dialog, F-004 scoping/authorization, F-005 health — the whole app (size S, one entity, ~10 routes).
- Out of scope: load/performance, visual regression, penetration testing beyond the Gate 18 checks (IDOR, anonymous access), native mobile.
- Order of execution (Phase A env smoke → B P0 → C P1 → D regression → E cross-feature → F integration/API): A = ENV-001..003 executed first and green in run `20260903-132200` before anything else was trusted; B = API-001, API-003, AUTH-001, ENV-002, ITEM-001; C = API-002, AUTH-002..004, ITEM-002; D/E/F = the tagged sets (`--regression`, `--e2e`, `--integration`). Vertical slice first: AUTH-001 → ITEM-001 (login → create → API check → table) was implemented and run before any other test.

## Coverage areas
| Area | Approach (UI / API / both) | Why |
|---|---|---|
| Functional (happy, negative, boundary, invalid/missing/null/duplicate, state, multi-step, cross-feature) | both — create/delete journeys in the UI (ITEM-001..003), boundaries and invalid input via API (API-002) | UI proves the user-visible outcome; the API proves persistence and gives the length boundaries in 5 requests instead of 5 page round-trips |
| Authentication (login, logout, invalid creds, expiry, refresh, direct URL, persistence) | UI for login/logout/redirect (AUTH-001..004), API for anonymous rejection (API-001) | the login form is the user's entry point; `/api/me` is the cheapest proof that the backend recognises the browser's cookie (AUTH-001 checks both) |
| Authorization (each role × permission, UI + API, object-level, escalation) | API (API-003 object-level delete, API-004 list scoping) | the UI hides nothing by role, so the API is the only enforcement point; a 403 is stronger evidence than a missing button |
| Validation (min/max/just outside, required, formats, unicode, special chars, long, duplicates) | API (API-002: 0, 1, 50, 51, whitespace) | limits live in `validate_name` (app.py:77-82) shared by both routes; unicode/special characters deferred (gap) |
| State (initial, loading, empty, success, failure, partial, expired, deleted, disabled, completed) | UI: success toast, deleted row, cancelled dialog (ITEM-001..003); empty state seen only in code (`items-empty`, 111) | no loading/partial/expired states exist in a server-rendered app without expiry |
| Integration (browser → frontend → API → backend → DB → external) | both: every UI journey ends with an API read using the browser's cookies (`ctx.api.set_cookies_from_driver`) | that cross-check is what separated REAL_APPLICATION_BUG from SYNCHRONIZATION_FAILURE in ITEM-001 |
| Security-aware (IDOR, escalation, session invalidation, upload limits, data exposure) | API-003 (IDOR), AUTH-004 (session invalidated after logout), AUTH-003 (direct URL) | the three checks the app's surface allows; `/api/reset` being unauthenticated is recorded in recon, not tested |
| Accessibility-aware (labels, keyboard, focus, error messages) | `--a11y` observation run on ITEM-001 (run `demo-trace`) | observations only; no compliance claim |

## Environment and browsers
- Environments: local only (`http://127.0.0.1:5000`) — data strategy: unique names from `data/factories.py`, every created item deleted in `ctx.add_cleanup`, seeded item from `setup_module` removed in teardown; `POST /api/reset` available but not used by the suite so tests stay order-independent.
- Browser matrix (default Chrome; Firefox/Edge for critical regression when justified): Chrome 151 headless for all runs; Firefox for AUTH-001/AUTH-002 (run `demo-firefox`, 2/2 pass); Chrome mobile emulation "iPhone 12 Pro" for ENV-002 (run `demo-mobile`, pass). Edge not available on the runner.

## What is deliberately not automated (and why)
- Session expiry / refresh — the app never expires a session (no timestamp in `session`, app.py:139); nothing to assert. Recorded as TC-AUTH-900 "assumed expected — needs product confirmation".
- Password reset, registration — routes do not exist.
- Concurrent creation from two tabs — TC-ITEM-900; the in-memory store has no concurrency control worth exercising in a demo, and the runner's `--parallel` already creates items from several processes.
- Pagination / many records — no pagination exists; a list of 1000 rows would only test the browser.
- `DEMO_BUGS=idor` path — API-003 covers the ownership rule; running it with the flag on is a manual triage exercise, not a regression test of the real app.
