# Test cases

> Gate 4 deliverable. Risk-based scenarios, not one case per button. The `test id in code:` line is what
> `run_tests.py --traceability` parses; keep it exact. Expected results name their source (oracle rule):
> the verified implementation (`app.py:line`), or "assumed expected — needs product confirmation".

## TC-ENV-001 — Settings provide a base URL
- Feature: environment | Priority: P0 | Risk: Low
- Preconditions: `qa/.env` filled from `.env.example`
- Test data: none
- Steps:
  1. Load settings
- Expected result: `QA_BASE_URL` is set (source: framework requirement; nothing runs without it)
- Automation strategy: API (no browser) — test id in code: `ENV-001`

## TC-ENV-002 — The browser starts and renders the application
- Feature: environment | Priority: P0 | Risk: Low
- Preconditions: app running; Chrome/Firefox and a matching driver available
- Test data: none
- Steps:
  1. Open the base URL, wait for `document.readyState == complete`
  2. Screenshot `landing.png`
- Expected result: a `<body>` is rendered; anonymous users land on `/login` (source: `app.py:126-128` index redirect)
- Automation strategy: UI — test id in code: `ENV-002`

## TC-ENV-003 — The API health endpoint answers
- Feature: environment | Priority: P1 | Risk: Low
- Preconditions: app running
- Test data: none
- Steps:
  1. `GET /api/health`
- Expected result: status < 500, JSON `{"status": "ok", "bugs": [...]}` (source: `app.py:185-187`)
- Automation strategy: API — test id in code: `ENV-003`

## TC-AUTH-001 — Valid credentials reach the dashboard and the backend recognises the browser session
- Feature: authentication | Priority: P0 | Risk: Critical
- Preconditions: `test_user` account (`QA_TEST_USER_*`)
- Test data: the configured account
- Steps:
  1. Open `/login`, submit email + password
  2. Wait for the dashboard (`items-table` visible)
  3. Copy the browser cookies into the API client, `GET /api/me`
- Expected result: URL contains `/dashboard`; `/api/me` → 200; `user-name` in the navbar equals `me.name` (source: `app.py:135-143`, `202-206`)
- Automation strategy: both — test id in code: `AUTH-001`

## TC-AUTH-002 — Wrong password shows an error and stays on the login page
- Feature: authentication | Priority: P1 | Risk: High
- Preconditions: none
- Test data: `unique_email()` + a wrong password (an unknown account and a wrong password must behave the same — no user enumeration)
- Steps:
  1. Open `/login`, submit
- Expected result: `login-error` visible with "Invalid email or password"; URL still `/login` (source: `app.py:144-145`)
- Automation strategy: UI — test id in code: `AUTH-002`

## TC-AUTH-003 — Direct URL access to the dashboard without a session redirects to login
- Feature: authentication | Priority: P1 | Risk: High
- Preconditions: fresh browser (no cookies)
- Test data: none
- Steps:
  1. `GET /dashboard` in the browser
- Expected result: redirected to `/login?next=/dashboard`; assert on the **path** `/login` — the query string legitimately contains `/dashboard` (source: `app.py:53-59`)
- Automation strategy: UI — test id in code: `AUTH-003`

## TC-AUTH-004 — Logout invalidates the session
- Feature: authentication | Priority: P1 | Risk: High
- Preconditions: `test_user`
- Test data: the configured account
- Steps:
  1. Log in, click `logout-link`
  2. `GET /dashboard` again in the same browser
- Expected result: back on `/login`; the dashboard does not render (source: `app.py:148-151` `session.clear()`)
- Automation strategy: UI — test id in code: `AUTH-004`

## TC-API-001 — A protected endpoint rejects anonymous requests
- Feature: authentication | Priority: P0 | Risk: Critical
- Preconditions: none
- Test data: none
- Steps:
  1. `GET /api/me` without cookies
- Expected result: 401 JSON `{"error": "authentication required"}` (source: `app.py:62-68`)
- Automation strategy: API — test id in code: `API-001`

## TC-API-002 — Item name boundaries: 1 and 50 accepted, 0 / 51 / whitespace rejected
- Feature: items | Priority: P1 | Risk: High
- Preconditions: API login as `test_user`
- Test data: `boundary_strings(1, 50)` → `at_min`, `at_max`, `empty`, `above_max`, `whitespace`
- Steps:
  1. `POST /api/items` for each value; delete the ones that were created
- Expected result: 201 for 1 and 50 chars; 400 for empty, 51 chars and whitespace-only (source: `validate_name`, `app.py:77-82`; names are stripped before the check)
- Automation strategy: API — test id in code: `API-002`

## TC-API-003 — A user cannot delete another user's item (IDOR)
- Feature: items | Priority: P0 | Risk: Critical
- Preconditions: `admin` and `test_user` accounts
- Test data: an item created by the admin
- Steps:
  1. As admin, create an item; log out of the API client
  2. As test_user, `DELETE /api/items/<admin item id>`
  3. As admin, `GET /api/items`
- Expected result: step 2 → 403 `forbidden`; step 3 still lists the item (source: `_delete`, `app.py:248-255`)
- Automation strategy: API — test id in code: `API-003`

## TC-API-004 — A regular user only sees their own items
- Feature: items | Priority: P2 | Risk: High
- Preconditions: API login as `test_user`; seed data contains an admin-owned item
- Test data: seed data
- Steps:
  1. `GET /api/items`
- Expected result: every `owner` equals the user's email (source: `visible_items`, `app.py:71-74`)
- Automation strategy: API — test id in code: `API-004`

## TC-ITEM-001 — Creating an item through the UI persists it and shows it in the table
- Feature: items | Priority: P0 | Risk: High
- Preconditions: logged in as `test_user` (session reused via `login_once`)
- Test data: `unique_name("Item")`
- Steps:
  1. On `/dashboard`, type the name, click Create
  2. Read the toast; `GET /api/items` with the browser's cookies
  3. Wait for the table row with the name
- Expected result: toast names the item; API returns it; table shows it (source: `app.py:164-173` create → redirect → `dashboard()` renders `visible_items`)
- Automation strategy: both — test id in code: `ITEM-001`

## TC-ITEM-002 — Confirming the delete dialog removes the row and the backend no longer returns the item
- Feature: items | Priority: P1 | Risk: High
- Preconditions: an item seeded through the API in `setup_module`
- Test data: `unique_name("Seeded")`
- Steps:
  1. On `/dashboard`, click the row's Delete, confirm in `confirm-dialog`
  2. Wait for the row to disappear; `GET /api/items`
- Expected result: row gone; item id absent from the API list (source: `app.py:176-181`, `_delete`)
- Automation strategy: both — test id in code: `ITEM-002`

## TC-ITEM-003 — Cancelling the delete dialog changes nothing
- Feature: items | Priority: P2 | Risk: Medium
- Preconditions: logged in; at least one item visible
- Test data: the first row
- Steps:
  1. Click Delete, click Cancel
- Expected result: dialog hidden; the table lists the same names as before (source: `closeDialog()`, `app.py:119` — a **characterization test**: no requirement states it, the observed behavior is assumed expected)
- Automation strategy: UI — test id in code: `ITEM-003`

## TC-AUTH-005 — Email is trimmed and lower-cased before lookup
- Feature: authentication | Priority: P3 | Risk: Low
- Preconditions: none
- Test data: `"  QA.User@Example.test "`
- Steps:
  1. Log in with the padded, mixed-case email
- Expected result: login succeeds — **assumed expected — needs product confirmation** (observed in `app.py:135`; a product may instead want exact matching)
- Automation strategy: API (characterization) — not automated until confirmed

## TC-AUTH-900 — Session expiry after inactivity
- Feature: authentication | Priority: P2 | Risk: Medium
- Preconditions: —
- Test data: —
- Steps: —
- Expected result: **assumed expected — needs product confirmation**. The application implements no expiry (`session` carries no timestamp, `app.py:139`); nothing to assert until the product decides.
- Automation strategy: manual / not automated

## TC-ITEM-900 — Concurrent creation from two tabs
- Feature: items | Priority: P3 | Risk: Low
- Preconditions: —
- Test data: —
- Steps: —
- Expected result: both items persist with distinct ids (source: global counter `app.py:35`). Not automated: the in-memory store has no concurrency control worth exercising, and `--parallel` already creates items from several processes.
- Automation strategy: not automated (see coverage-gaps.md)

## Edge-case checklist per important feature
| Feature | empty | one | many | duplicate | rapid repeat | refresh mid-op | back/forward | multi-tab | expiry | network | delayed API | backend error | partial | race |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Items | `items-empty` row (seen in code, not automated — needs an account with no items) | ITEM-002 | gap | allowed by design (no unique constraint, `app.py:242`) | gap | server-rendered: refresh is a plain GET | gap | TC-ITEM-900 | n/a | gap | n/a (no async) | gap | n/a | TC-ITEM-900 |
| Auth | AUTH-002 (unknown user) | AUTH-001 | n/a | n/a | gap | n/a | gap | gap | TC-AUTH-900 | gap | n/a | gap | n/a | n/a |
