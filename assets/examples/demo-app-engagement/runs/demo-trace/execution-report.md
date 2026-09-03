# Execution report — run demo-trace

- Started: 2026-09-03T11:15:46.341649+00:00
- Finished: 2026-09-03T11:15:49.087604+00:00 (2.746s)
- Environment: local — base_url=http://127.0.0.1:5094 api_base_url=http://127.0.0.1:5094
- Application build: build_id=demo-app, git=425eb02f0930, branch=main, dirty
- Browser: chrome (headless=True) — chrome 151.0.7922.173, driver 151.0.7922.173 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id demo-trace --test ITEM-001 --a11y --trace`
- Options: retries=0 repeat=1 timeout=300.0s a11y=True

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| ITEM-001 | items | P0 | PASS | 2.733s |  |

## Failures requiring triage

None.
## Observations (non-failing)

- ITEM-001 · a11y: {"violations": 2, "summary": {"moderate": 2}, "file": "attempt1-a11y.json"}

## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
