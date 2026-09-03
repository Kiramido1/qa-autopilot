# Test cases

> Gate 4 deliverable — case and edge-case checklist in `references/gates.md#gate-4`. Risk-based scenarios, not
> one case per button. Priorities: P0 catastrophic/critical workflow · P1 business-critical/high-risk · P2
> important normal · P3 low-risk. Keep the `test id in code:` line exact — `--traceability` parses it.
> Where no requirement exists, write "assumed expected — needs product confirmation" and mark the test a
> characterization test. Delete the EXAMPLE section after use; full example in
> `assets/examples/demo-app-engagement/qa-artifacts/test-cases.md`.

## TC-ITEM-001 — Creating an item through the UI persists it and shows it in the table (EXAMPLE)
- Feature: items | Priority: P0 | Risk: High
- Preconditions: logged in as test_user (session reused via `login_once`)
- Test data: `unique_name("Item")`
- Steps:
  1. Open /dashboard, type the name, click Create
  2. Read the toast; GET /api/items with the browser's cookies
  3. Wait for the table row with the name
- Expected result: toast names the item; API returns it; table shows it
- Automation strategy: both (UI + API evidence) — test id in code: `ITEM-001`

## TC-AUTH-001 — <title>
- Feature: | Priority: | Risk:
- Preconditions:
- Test data:
- Steps:
  1.
  2.
- Expected result:
- Automation strategy: UI (Selenium) / API (requests) / both — test id in code: `AUTH-001`

## Edge-case checklist per important feature
empty data · one record · many records · duplicates · rapid repeated actions · refresh mid-operation · back/forward navigation · multiple tabs · session expiry · network failure · delayed API · backend error · partial failure · race conditions · concurrent actions
