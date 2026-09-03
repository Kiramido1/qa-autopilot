# Execution report — run demo-firefox

- Started: 2026-09-03T11:15:32.272051+00:00
- Finished: 2026-09-03T11:15:42.141035+00:00 (9.869s)
- Environment: local — base_url=http://127.0.0.1:5092 api_base_url=http://127.0.0.1:5092
- Application build: build_id=demo-app, git=425eb02f0930, branch=main, dirty
- Browser: firefox (headless=True) — firefox 140.14.0, driver 0.33.0 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id demo-firefox --test AUTH-001 --test AUTH-002 --test ITEM-001`
- Options: retries=0 repeat=1 timeout=300.0s a11y=False

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 3 | 3 | 0 | 0 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| AUTH-001 | authentication | P0 | PASS | 2.913s |  |
| AUTH-002 | authentication | P1 | PASS | 2.876s |  |
| ITEM-001 | items | P0 | PASS | 4.066s |  |

## Failures requiring triage

None.
## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
