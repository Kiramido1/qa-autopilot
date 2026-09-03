# Defects

> Gate 14 — one entry per confirmed REAL_APPLICATION_BUG, in the format from `references/reporting.md#defect-report-format`.
> Severity uses the rubric in `references/reporting.md#severity-rubric`; do not inflate without evidence.
> Never include credentials or secrets in evidence. Delete the EXAMPLE entry after use; full example in
> `assets/examples/demo-app-engagement/qa-artifacts/defects.md`.

## BUG-001 (EXAMPLE)
```
BUG ID:        BUG-001
TITLE:         Dashboard shows the item list captured at login; items created afterwards are missing until re-login
SEVERITY:      High — blocked workflow (user cannot see what they just created); workaround exists (re-login); no data loss
PRIORITY:      P1
FEATURE:       F-002 item creation
ENVIRONMENT:   local, chrome 151 headless, build demo-app@stale-dashboard (git 425eb02f0930)

PRECONDITIONS: logged in as test_user

STEPS TO REPRODUCE:
1. Sign in, open /dashboard
2. Create an item "Item X"
3. Observe the table (and GET /api/items)

EXPECTED: "Item X" appears in the table (API returns it)
ACTUAL:   toast confirms creation, API returns the item (id 8), table still shows ids 1, 2, 7

EVIDENCE:
- Screenshot: runs/20260903-132200/artifacts/ITEM-001/attempt1-screenshot.png
- API response: runs/20260903-132200/artifacts/ITEM-001/items-after-create.json (200, item present)
- Page source: runs/20260903-132200/artifacts/ITEM-001/attempt1-page_source.html (item absent)
- Repeat: run 20260903-132400 failed 5/5 deterministically

ROOT CAUSE:  dashboard() renders STALE_SNAPSHOT captured in login() (app.py) instead of the live store
IMPACT:      every user, every create/delete until re-login
REGRESSION RISK: dashboard route → F-002, F-003, F-004
AFFECTED COMPONENTS: app.py dashboard(), login()

RECOMMENDATION: read visible_items(user) on every request; remove the snapshot
REGRESSION TEST:  ITEM-001 (exists), ITEM-002
```

## BUG-00N
```
BUG ID:
TITLE:
SEVERITY:      Critical / High / Medium / Low (rubric in references/reporting.md)
PRIORITY:      P0 / P1 / P2 / P3
FEATURE:
ENVIRONMENT:   (env, browser, build/commit)

PRECONDITIONS:

STEPS TO REPRODUCE:
1.
2.
3.

EXPECTED:
ACTUAL:

EVIDENCE:
- Screenshot:
- Logs:
- API request/response:
- URL:
- Database evidence (where appropriate):

ROOT CAUSE:
IMPACT:
REGRESSION RISK:
AFFECTED COMPONENTS:

RECOMMENDATION:
REGRESSION TEST:  (test id added / to add)
```
