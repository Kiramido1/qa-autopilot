# Feature inventory

> Gate 2 deliverable. Rank by business impact, security impact, data integrity, frequency of use,
> failure probability, complexity and dependency count — not by size.

| ID | Feature | Pages | Roles | Endpoints | Entities | Preconditions | Happy path | Negative paths | State transitions | Side effects | Risk (Critical/High/Medium/Low) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F-001 | Authentication (login, logout, protected pages) | `/login`, `/dashboard`, `/logout` | anonymous → user/admin | `POST /login`, `GET /logout`, `POST /api/login`, `GET /api/me` | User | account exists (app.py:31-34) | valid credentials → session cookie → dashboard shows `user-name` | wrong password → `login-error`, stay on `/login`; anonymous `/dashboard` → redirect; `/api/me` without cookie → 401 | anonymous ⇄ authenticated; logout clears session (150) | session cookie set/cleared; with `stale-dashboard` a snapshot is stored at login (141) | **Critical** |
| F-002 | Item creation (form + API) | `/dashboard` | user, admin | `POST /items`, `POST /api/items` | Item | authenticated | name → 201/toast → row in `items-table` | empty / whitespace / 51 chars → 400 or `item-error` | none → exists | store mutation (243-244), toast in session | **High** |
| F-003 | Item deletion via confirm dialog | `/dashboard` | user, admin (owner rule) | `POST /items/<id>/delete`, `DELETE /api/items/<id>` | Item | item exists and is owned (or admin) | Delete → dialog → confirm → row gone, 204 via API | cancel keeps row; other owner → 403; missing → 404 | exists → deleted (hard) | store mutation (254) | **High** |
| F-004 | Item list scoping and object-level authorization | `/dashboard` | user vs admin | `GET /api/items`, `DELETE /api/items/<id>` | Item, User | two accounts with items | user sees own items only; admin sees all | user deleting admin's item → 403 and item survives | — | none | **Critical** |
| F-005 | API health | — | any | `GET /api/health` | — | app up | 200 `{"status":"ok"}` | 5xx means backend unusable | — | none | Low |

## Risk rationale
- F-001 → Critical: every other feature depends on the session; a bypass exposes all items; login is the most frequent action. Failure probability is low (30 lines of code) but impact is total.
- F-002 → High: the core write path and the most frequent business action after login. Two entry points (form and API) share `validate_name` and `_create`, so a defect hits both; the rendering path (`dashboard()` 154-161) is where state can go stale — which is exactly what happened.
- F-003 → High: destructive, hard delete with no undo; involves the only client-side JS in the app (dialog 116-119), which adds a UI-layer failure mode the API does not have.
- F-004 → Critical although it is four lines (71-74, 252-253): security impact (cross-user data access and deletion) and data integrity dominate size. A `DEMO_BUGS=idor` flag exists precisely because this check is easy to break silently.
- F-005 → Low: no business behavior; it is the environment smoke signal (ENV-003), not a feature users touch.
