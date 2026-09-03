# Execution report — run verify-demo

- Started: 2026-09-03T11:15:20.569767+00:00
- Finished: 2026-09-03T11:15:31.222526+00:00 (10.653s)
- Environment: local — base_url=http://127.0.0.1:5091 api_base_url=http://127.0.0.1:5091
- Application build: build_id=demo-app, git=425eb02f0930, branch=main, dirty
- Browser: chrome (headless=True) — chrome 151.0.7922.173, driver 151.0.7922.173 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id verify-demo`
- Options: retries=0 repeat=1 timeout=300.0s a11y=False

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 14 | 14 | 0 | 0 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| API-001 | authentication | P0 | PASS | 0.003s |  |
| API-003 | items | P0 | PASS | 0.02s |  |
| API-002 | items | P1 | PASS | 0.021s |  |
| API-004 | items | P2 | PASS | 0.006s |  |
| AUTH-001 | authentication | P0 | PASS | 0.951s |  |
| AUTH-002 | authentication | P1 | PASS | 0.917s |  |
| AUTH-003 | authentication | P1 | PASS | 0.629s |  |
| AUTH-004 | authentication | P1 | PASS | 2.086s |  |
| ENV-001 | environment | P0 | PASS | 0.0s |  |
| ENV-002 | environment | P0 | PASS | 0.649s |  |
| ENV-003 | environment | P1 | PASS | 0.003s |  |
| ITEM-001 | items | P0 | PASS | 2.074s |  |
| ITEM-002 | items | P1 | PASS | 1.02s |  |
| ITEM-003 | items | P2 | PASS | 2.259s |  |

## Failures requiring triage

None.
## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
