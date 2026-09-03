# Repository reconnaissance

> Gate 1 deliverable. Verify behavior in the implementation, not in names, comments or docs.
> Exit criterion: you can explain the architecture and the major business flows.

Scope: `assets/demo-app/app.py` (260 lines, single Flask module). Everything below cites it.

## Architecture (text diagram)
```
Browser → Jinja templates rendered server-side (LAYOUT/LOGIN/DASHBOARD, app.py:85-119)
        → Flask routes (form routes app.py:126-181, JSON API app.py:184-239)
        → in-memory store ITEMS (app.py:36) + STALE_SNAPSHOT (app.py:37, only with the stale-dashboard flag)
No database, no external integrations, no background jobs.
```

## Frontend map
| Page / route | Components | Forms & validation | States (loading/empty/error) | Roles |
|---|---|---|---|---|
| `/login` (LOGIN, 92-98) | form `login-form`, inputs `login-email`, `login-password`, button `login-submit` | HTML `required` on both fields; server compares plaintext password (137) | error banner `login-error` role=alert (93) | anonymous |
| `/dashboard` (DASHBOARD, 100-119) | nav `user-name`/`user-role`/`logout-link`; toast `toast` role=status; create form `item-form`; table `items-table` with `item-row[data-item-id]`, `item-name-cell`, `item-delete-<id>`; dialog `confirm-dialog` role=dialog with `modal-confirm`/`modal-cancel` | `item-name` has `maxlength` = MAX_NAME (106) — client hint only; server re-validates (167) | empty state row `items-empty` (111); error banner `item-error` (104) | user, admin |

- Routing / state management / API client: full page round-trips; no JS state beyond the dialog open/close (116-119). Toast and error are one-shot session values popped on render (161).
- Toasts, modals, tables, filters, pagination, uploads, downloads: toast ✔, modal ✔ (native `<div role=dialog>` toggled with `hidden`), table ✔ (4 columns: ID, Name, Owner, Actions), no filters, no pagination, no uploads/downloads.

## Backend map
| Route | Method | Auth | Roles | Request schema | Response schema | Errors |
|---|---|---|---|---|---|---|
| `/` (126) | GET | none | any | — | 302 → `/dashboard` or `/login` | — |
| `/login` (131) | GET/POST | none | any | form `email`, `password`, `next` | 302 to `next` (only if it starts with `/`, 143) or `/dashboard` | re-render with "Invalid email or password" (144) |
| `/logout` (148) | GET | none | any | — | clears session, 302 `/login` | — |
| `/dashboard` (154) | GET | `login_required` (53-59) | user, admin | — | HTML | anonymous → 302 `/login?next=/dashboard` (57) |
| `/items` (164) | POST | `login_required` | user, admin | form `name` | 302 `/dashboard` with toast or error in session | validation message via `item-error` |
| `/items/<id>/delete` (176) | POST | `login_required` | user, admin | — | 302 `/dashboard` | "Could not delete item (403/404)" (180) |
| `/api/health` (185) | GET | none | any | — | `{"status","bugs"}` | — |
| `/api/login` (190) | POST | none | any | JSON `email`, `password` | `{"email","name","role"}` | 401 `invalid credentials` (196) |
| `/api/me` (202) | GET | `api_auth` (62-68) | user, admin | — | `{"email","name","role"}` | 401 JSON (66) |
| `/api/items` (209) | GET | `api_auth` | user, admin | — | list of `{id,name,owner}` scoped by `visible_items` (71-74) | 401 |
| `/api/items` (215) | POST | `api_auth` | user, admin | JSON `name` | 201 `{id,name,owner}` | 400 with `validate_name` message (219-221) |
| `/api/items/<id>` (225) | DELETE | `api_auth` | user, admin | — | 204 | 403 `forbidden` / 404 `not found` (231) |
| `/api/reset` (234) | POST | **none** | any | — | reseeds store | — (test hook; would be a security finding in a real app) |

- Middleware, background jobs, transactions: two decorators only — `login_required` redirects HTML clients, `api_auth` returns 401 JSON. No transactions (dict mutation).

## Database map
| Entity | Key fields / constraints | Relationships | State fields | Soft delete / audit |
|---|---|---|---|---|
| Item (`_create` 242-245) | `id` from a global counter (35), `name` 1–50 chars after strip (77-82), `owner` = creator's email | owner → USERS key | none | hard delete (`del ITEMS[item_id]`, 254) |
| User (31-34) | email key, plaintext `password`, `name`, `role` ∈ {user, admin} | — | — | static |

- Important invariants: a non-admin only ever sees or deletes own items (`visible_items` 71-74, `_delete` 248-255); `name` is stripped before length check (80) and before storage (171, 222), so `"   "` is rejected as required.

## Integrations
| Integration | Purpose | Failure impact | Testability (mock / sandbox / live) |
|---|---|---|---|
| none | — | — | — |

## Authentication & authorization model
- Login / session / refresh / expiry: signed cookie session (`session["user"]`, 139/198); `session.clear()` on login and logout (138, 150, 197). No expiry, no refresh, no CSRF token.
- Roles and permissions (UI vs API enforcement): the UI never hides anything by role; enforcement is entirely server-side in `visible_items` and `_delete`. Both the form route (176-181) and the API route (225-231) call the same `_delete`, so UI and API cannot disagree — unless `DEMO_BUGS` contains `idor`, which removes the ownership check (252).

## Business rules (verified in code)
- Rule → where enforced (file:line) → how verified:
- Item name required, ≤ 50 chars after strip → `validate_name` app.py:77-82, called by both the form (167) and the API (219) → API-002 exercised 0/1/50/51/whitespace.
- User sees only own items; admin sees all → `visible_items` 71-74 → API-004.
- Only owner or admin may delete → `_delete` 252-253 → API-003 (403 expected, item must survive).
- Anonymous access to `/dashboard` redirects to `/login?next=/dashboard` → 57 → AUTH-003 (compare the path, the query carries `/dashboard`).
- Login snapshot (defect path): with `stale-dashboard`, `login()` stores `STALE_SNAPSHOT[email]` (140-141) and `dashboard()` prefers it over the live list (158-160) → ITEM-001 / ITEM-002 surfaced it.

## High-risk areas
- `dashboard()` list source (158-160): the only place where rendered state can diverge from stored state — Critical for F-002/F-003.
- `_delete` ownership check (252): four lines that decide object-level authorization for two routes — Critical.
- `/api/reset` (234) unauthenticated: acceptable for a demo, would be a P0 defect in a real product; noted, not filed.
- `next` redirect (142-143): open-redirect guard is a prefix check on `/` only; `//evil.test` would pass `startswith("/")` — Gate 18 observation, not in scope for this suite.

## Existing coverage vs gaps
- Covered: nothing before this engagement.
- Missing: everything; addressed by the 14 tests in `test-cases.md`, gaps in `coverage-gaps.md`.
