# Regression report

> Gates 15/16 — method in `references/gates.md#gate-15` and `#gate-16`. Change → affected components → features
> → journeys → tests → required regression. Delete EXAMPLE rows after use; full example in
> `assets/examples/demo-app-engagement/qa-artifacts/regression-report.md`.

## Change under analysis
- Source (PR / diff / fix): <!-- EXAMPLE: fix for BUG-001 (remove STALE_SNAPSHOT read in dashboard()) -->
- Changed files / functions / endpoints / migrations:

## Blast radius
| Changed code | Affected component | Affected feature | Affected journey | Tests | Priority |
|---|---|---|---|---|---|
| EXAMPLE app.py dashboard() | dashboard page, items table | F-002, F-003, F-004 | create item, delete item, login → dashboard | ITEM-001..003, AUTH-001 | P0/P1 |

## Regression executed
| Scope (targeted / full) | Run id | Result | Notes |
|---|---|---|---|
| EXAMPLE targeted `--feature items` | verify-demo | 14/14 PASS | run against the fixed build |

## New regression candidates (from defects)
- BUG-ID → test id

## Conclusion
- Safe to merge / not safe — evidence:
