# Execution report — run 20260903-132200

- Started: 2026-09-03T10:21:34.684953+00:00
- Finished: 2026-09-03T10:22:05.359996+00:00 (30.675s)
- Environment: local — base_url=http://127.0.0.1:5000 api_base_url=http://127.0.0.1:5000
- Application build: build_id=demo-app@stale-dashboard, git=425eb02f0930, branch=main, dirty
- Browser: chrome (headless=True) — chrome 151.0.7922.173, driver 151.0.7922.173 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id 20260903-132200`
- Options: retries=0 repeat=1 timeout=300.0s a11y=False

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 14 | 12 | 0 | 2 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| API-001 | authentication | P0 | PASS | 0.004s |  |
| API-003 | items | P0 | PASS | 0.019s |  |
| API-002 | items | P1 | PASS | 0.021s |  |
| API-004 | items | P2 | PASS | 0.006s |  |
| AUTH-001 | authentication | P0 | PASS | 0.952s |  |
| AUTH-002 | authentication | P1 | PASS | 0.921s |  |
| AUTH-003 | authentication | P1 | PASS | 0.606s |  |
| AUTH-004 | authentication | P1 | PASS | 2.15s |  |
| ENV-001 | environment | P0 | PASS | 0.001s |  |
| ENV-002 | environment | P0 | PASS | 0.683s |  |
| ENV-003 | environment | P1 | PASS | 0.004s |  |
| ITEM-001 | items | P0 | ERROR | 11.545s | TimeoutException: Message: table row containing 'Item 20260903132140-el19js' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)  |
| ITEM-002 | items | P1 | ERROR | 11.306s | TimeoutException: Message: table row containing 'Seeded 20260903132140-z0wgk9' gone (waited 10.0s; url=http://127.0.0.1:5000/dashboard)  |
| ITEM-003 | items | P2 | PASS | 2.438s |  |

## Failures requiring triage

### ITEM-001 — test_create_item_appears_in_table_and_api (ERROR)

Classification: **UNCLASSIFIED** — classify with evidence before reporting (see failure-triage reference).

- Attempt 1: ERROR in 11.545s — TimeoutException: Message: table row containing 'Item 20260903132140-el19js' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt1-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt1-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt1-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt1-browser_console.json`
  - network: `artifacts/ITEM-001/attempt1-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt1-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`

### ITEM-002 — test_delete_item_via_confirm_dialog (ERROR)

Classification: **UNCLASSIFIED** — classify with evidence before reporting (see failure-triage reference).

- Attempt 1: ERROR in 11.306s — TimeoutException: Message: table row containing 'Seeded 20260903132140-z0wgk9' gone (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-002/attempt1-exception.txt`
  - screenshot: `artifacts/ITEM-002/attempt1-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-002/attempt1-page_source.html`
  - browser_console: `artifacts/ITEM-002/attempt1-browser_console.json`
  - network: `artifacts/ITEM-002/attempt1-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-002/attempt1-context.json`

## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
