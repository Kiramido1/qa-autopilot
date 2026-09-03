# Execution report — run 20260903-132300

- Started: 2026-09-03T11:15:50.133385+00:00
- Finished: 2026-09-03T11:16:35.372376+00:00 (45.239s)
- Environment: local — base_url=http://127.0.0.1:5095 api_base_url=http://127.0.0.1:5095
- Application build: build_id=demo-app@stale-dashboard, git=425eb02f0930, branch=main, dirty
- Browser: chrome (headless=True) — chrome 151.0.7922.173, driver 151.0.7922.173 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id 20260903-132300 --rerun-failed bug-check --retries 1`
- Options: retries=1 repeat=1 timeout=300.0s a11y=False

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 2 | 0 | 0 | 2 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| ITEM-001 | items | P0 | ERROR | 22.8s | TimeoutException: Message: table row containing 'Item 20260903141602-8xbpsj' (waited 10.0s; url=http://127.0.0.1:5095/dashboard)  |
| ITEM-002 | items | P1 | ERROR | 22.426s | TimeoutException: Message: table row containing 'Seeded 20260903141550-irddjo' gone (waited 10.0s; url=http://127.0.0.1:5095/dashboard)  |

## Failures requiring triage

### ITEM-001 — test_create_item_appears_in_table_and_api (ERROR)

Classification: **UNCLASSIFIED** — classify with evidence before reporting (see failure-triage reference).

- Attempt 1: ERROR in 11.506s — TimeoutException: Message: table row containing 'Item 20260903141551-g1gfeu' (waited 10.0s; url=http://127.0.0.1:5095/dashboard)
  - exception: `artifacts/ITEM-001/attempt1-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt1-screenshot.png`
  - url: `http://127.0.0.1:5095/dashboard`
  - page_source: `artifacts/ITEM-001/attempt1-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt1-browser_console.json`
  - network: `artifacts/ITEM-001/attempt1-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt1-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`
- Attempt 2: ERROR in 11.294s — TimeoutException: Message: table row containing 'Item 20260903141602-8xbpsj' (waited 10.0s; url=http://127.0.0.1:5095/dashboard)
  - exception: `artifacts/ITEM-001/attempt2-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt2-screenshot.png`
  - url: `http://127.0.0.1:5095/dashboard`
  - page_source: `artifacts/ITEM-001/attempt2-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt2-browser_console.json`
  - network: `artifacts/ITEM-001/attempt2-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt2-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`

### ITEM-002 — test_delete_item_via_confirm_dialog (ERROR)

Classification: **UNCLASSIFIED** — classify with evidence before reporting (see failure-triage reference).

- Attempt 1: ERROR in 11.262s — TimeoutException: Message: table row containing 'Seeded 20260903141550-irddjo' gone (waited 10.0s; url=http://127.0.0.1:5095/dashboard)
  - exception: `artifacts/ITEM-002/attempt1-exception.txt`
  - screenshot: `artifacts/ITEM-002/attempt1-screenshot.png`
  - url: `http://127.0.0.1:5095/dashboard`
  - page_source: `artifacts/ITEM-002/attempt1-page_source.html`
  - browser_console: `artifacts/ITEM-002/attempt1-browser_console.json`
  - network: `artifacts/ITEM-002/attempt1-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-002/attempt1-context.json`
- Attempt 2: ERROR in 11.164s — TimeoutException: Message: table row containing 'Seeded 20260903141550-irddjo' gone (waited 10.0s; url=http://127.0.0.1:5095/dashboard)
  - exception: `artifacts/ITEM-002/attempt2-exception.txt`
  - screenshot: `artifacts/ITEM-002/attempt2-screenshot.png`
  - url: `http://127.0.0.1:5095/dashboard`
  - page_source: `artifacts/ITEM-002/attempt2-page_source.html`
  - browser_console: `artifacts/ITEM-002/attempt2-browser_console.json`
  - network: `artifacts/ITEM-002/attempt2-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-002/attempt2-context.json`

## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
