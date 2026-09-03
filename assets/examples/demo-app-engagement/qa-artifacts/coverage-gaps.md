# Coverage gaps

> Gate 21 — coverage across dimensions, never "number of tests". Includes what was deliberately not read or not
> automated, and why. Observations from `--a11y` are recorded here as observations, not as compliance.

| Dimension | Covered | Not covered | Why | Risk | Plan |
|---|---|---|---|---|---|
| Features | F-001..F-005 (all) | — | — | — | — |
| User roles | user (all journeys), admin (as item owner in API-003), anonymous | admin's own UI journeys (admin sees *all* items on the dashboard) | admin differs from user only in `visible_items`; covered at the API by API-004's complement not being asserted | Medium | add API-005: admin list contains other owners' items |
| User journeys | login → dashboard → me; create → API → table; seed → delete → API; logout → direct URL; cancel dialog | first-time user with zero items (empty state) | seed data gives every account items; needs a third account or `POST /api/reset` + deletes | Low | add a fixture account with no items |
| APIs | 9 / 13 routes | `POST /items`, `POST /items/<id>/delete` directly (only via UI), `POST /api/reset`, `GET /` | form routes are exercised through the UI tests; reset is a test hook | Low | direct form-route tests only if the UI tests are ever removed |
| Pages | `/login`, `/dashboard` | — | — | — | — |
| States | success toast, deleted, cancelled, error banner (API-002 at the API) | `item-error` banner in the UI, `items-empty` | server validation is proven at the API; the banner is a render of the same message | Low | one UI case for the 51-char name |
| Negative paths | wrong password, anonymous access, 0/51/whitespace names, IDOR | unknown item id via the UI (404 path `app.py:249`) | reachable only by crafting a form action | Low | API-006: `DELETE /api/items/9999` → 404 |
| Boundary conditions | name length 0/1/50/51, whitespace | unicode, HTML markup, quotes, very long (5000) inputs (`SPECIAL_INPUTS`) | time-boxed; `validate_name` only checks length, so these test rendering/escaping (`|e` filter, `app.py:114`) | Medium | API-007 + one UI check that the name renders escaped |
| Authorization paths | object-level delete (API-003), list scoping (API-004), anonymous (API-001, AUTH-003) | vertical escalation (user → admin) | the app has no role-changing endpoint | — | n/a |
| Cross-feature flows | create → delete on the same item (ITEM-001 cleanup + ITEM-002) | — | — | — | — |
| Browsers | Chrome 151 (all), Firefox 140 (AUTH-001/002, ITEM-001), Chrome mobile emulation (ENV-002, AUTH-001) | Edge, Safari; full suite on Firefox | not installed on the runner / not in the demo's support matrix | Low | CI runs the full suite on Chrome and Firefox (`.github/workflows/qa.yml`) |
| Regression | targeted + full after the BUG-001 fix (`verify-demo`) | — | — | — | — |
| Unread code (sampling) | `app.py` read in full (261 lines, size S) | — | — | — | — |
| Accessibility (observations) | axe-core on `/dashboard` (`demo-trace`): 2 moderate — `landmark-one-main`, `region` | keyboard navigation, focus management in the dialog | manual checks not performed | Low | observation only; no compliance claim |
| Security-aware (Gate 18) | IDOR (API-003), anonymous (API-001), session invalidation (AUTH-004) | open-redirect via `next=//host` (`app.py:143`), unauthenticated `/api/reset` | recorded in recon as findings; not exploited | Medium (real product) | file as defects in a real engagement |

## Accepted risks
- Unicode / markup inputs untested → accepted by the engagement owner → until the next iteration (planned API-007).
- No Edge/Safari → accepted (demo support matrix) → indefinitely.
- Session expiry unspecified (TC-AUTH-900) → needs product confirmation before any test exists.
