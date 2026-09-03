# Regression report

> Gates 15 / 16 — change → affected components → features → journeys → tests → required regression.

## Change under analysis
- Source (PR / diff / fix): fix for BUG-001 — remove the `STALE_SNAPSHOT` read in `dashboard()` (equivalently: run the build without `DEMO_BUGS=stale-dashboard`).
- Changed files / functions / endpoints / migrations: `app.py` `dashboard()` (158-160) and `login()` (140-141); no endpoint signatures, no migrations.

## Blast radius
| Changed code | Affected component | Affected feature | Affected journey | Tests | Priority |
|---|---|---|---|---|---|
| `app.py` `dashboard()` | dashboard page: items table, toast, error banner | F-002 create, F-003 delete, F-004 scoping (what the table shows per role) | login → dashboard; create → table; delete → table | ITEM-001, ITEM-002, ITEM-003, AUTH-001 (asserts on the dashboard), AUTH-004 (dashboard must *not* render) | P0/P1 |
| `app.py` `login()` | session creation | F-001 authentication | every authenticated journey | AUTH-001, AUTH-002, AUTH-004, API-001 (unchanged path, shared decorator) | P0/P1 |
| shared: `visible_items()` is now called on every render | API and UI list scoping | F-004 | admin vs user view | API-004, API-003 | P0/P2 |

Method (Gate 16): `grep -n "STALE_SNAPSHOT\|visible_items" app.py` → callers `dashboard()`, `login()`, `api_items()`; routes that reach them → `/dashboard`, `/login`, `/api/items`; looked up in `traceability-matrix.md` → the test ids above.

## Regression executed
| Scope (targeted / full) | Run id | Result | Notes |
|---|---|---|---|
| targeted — the blast-radius set (`--feature items --feature authentication`) | `verify-demo` (whole suite; the S-sized app makes full = targeted + 3 ENV tests) | 14/14 PASS in 10.7 s | ITEM-001 and ITEM-002 now PASS; no test was changed between the failing and the passing run |
| cross-browser on the P0 journeys | `demo-firefox` | 3/3 PASS | AUTH-001, AUTH-002, ITEM-001 on Firefox 140 |
| responsive | `demo-mobile` | 2/2 PASS | ENV-002, AUTH-001 with iPhone 12 Pro emulation |

## New regression candidates (from defects)
- BUG-001 → ITEM-001 and ITEM-002 already exist and failed on the defect; no new test needed. Kept in `--regression` and `--e2e`.

## Conclusion
- **Safe to merge** — evidence: the two tests that failed deterministically on the defective build (0/5 in `20260903-132400`) pass on the fixed build (`verify-demo`), the rest of the blast-radius set is green, and the assertions are unchanged between the two runs (`git diff` of `qa/tests/` is empty).
