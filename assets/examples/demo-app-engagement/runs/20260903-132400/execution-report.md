# Execution report — run 20260903-132400

- Started: 2026-09-03T10:22:51.347731+00:00
- Finished: 2026-09-03T10:23:47.804367+00:00 (56.457s)
- Environment: local — base_url=http://127.0.0.1:5000 api_base_url=http://127.0.0.1:5000
- Application build: build_id=demo-app@stale-dashboard, git=425eb02f0930, branch=main, dirty
- Browser: chrome (headless=True) — chrome 151.0.7922.173, driver 151.0.7922.173 — Selenium 4.31.1 / Python 3.13.11
- Selection: `--run-id 20260903-132400 --test ITEM-001 --repeat 5`
- Options: retries=0 repeat=5 timeout=300.0s a11y=False

## Totals

| Total | Passed | Failed | Errors | Flaky | Skipped |
|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 0 | 0 |

## Results

| ID | Feature | Priority | Status | Duration | Message |
|---|---|---|---|---|---|
| ITEM-001 | items | P0 | ERROR (0/5 passed) | 56.441s | failed 5/5 deterministically — TimeoutException: Message: table row containing 'Item 20260903132337-rjfjba' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)  |

## Failures requiring triage

### ITEM-001 — test_create_item_appears_in_table_and_api (ERROR)

Classification: **UNCLASSIFIED** — classify with evidence before reporting (see failure-triage reference).

- Attempt 1: ERROR in 11.44s — TimeoutException: Message: table row containing 'Item 20260903132252-63lpo1' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt1-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt1-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt1-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt1-browser_console.json`
  - network: `artifacts/ITEM-001/attempt1-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt1-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`
- Attempt 2: ERROR in 11.241s — TimeoutException: Message: table row containing 'Item 20260903132303-gooznk' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt2-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt2-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt2-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt2-browser_console.json`
  - network: `artifacts/ITEM-001/attempt2-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt2-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`
- Attempt 3: ERROR in 11.247s — TimeoutException: Message: table row containing 'Item 20260903132314-m2g78a' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt3-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt3-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt3-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt3-browser_console.json`
  - network: `artifacts/ITEM-001/attempt3-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt3-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`
- Attempt 4: ERROR in 11.304s — TimeoutException: Message: table row containing 'Item 20260903132325-3s0vjk' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt4-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt4-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt4-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt4-browser_console.json`
  - network: `artifacts/ITEM-001/attempt4-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt4-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`
- Attempt 5: ERROR in 11.209s — TimeoutException: Message: table row containing 'Item 20260903132337-rjfjba' (waited 10.0s; url=http://127.0.0.1:5000/dashboard)
  - exception: `artifacts/ITEM-001/attempt5-exception.txt`
  - screenshot: `artifacts/ITEM-001/attempt5-screenshot.png`
  - url: `http://127.0.0.1:5000/dashboard`
  - page_source: `artifacts/ITEM-001/attempt5-page_source.html`
  - browser_console: `artifacts/ITEM-001/attempt5-browser_console.json`
  - network: `artifacts/ITEM-001/attempt5-network.json`
  - network_problems: `1`
  - context: `artifacts/ITEM-001/attempt5-context.json`
  - attachment: `artifacts/ITEM-001/items-after-create.json`

## Defects, automation defects, environment failures

Fill in after triage: every UNCLASSIFIED result above must become one of the failure categories with evidence.

## Remaining risks

Fill in after triage (coverage gaps, untested areas, known flaky behavior).
