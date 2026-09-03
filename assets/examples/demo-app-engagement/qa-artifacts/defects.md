# Defects

> Gate 14 — one entry per confirmed REAL_APPLICATION_BUG, in the format from `references/reporting.md`.
> Severity from the rubric; every line of evidence is a path under `../runs/`.

## BUG-001
```
BUG ID:        BUG-001
TITLE:         Dashboard renders the item list captured at login; items created or deleted afterwards are missing until re-login
SEVERITY:      High — core workflow (create / delete item) wrong for every user; results silently persisted while the UI contradicts them; workaround (log out and in again) exists but is not obvious
PRIORITY:      P1
FEATURE:       F-002 item creation, F-003 item deletion (both symptoms, one cause)
ENVIRONMENT:   local, Chrome 151.0.7922.173 headless (chromedriver 151), build demo-app@stale-dashboard (git 425eb02f0930, dirty)

PRECONDITIONS: logged in as qa.user@example.test; DEMO_BUGS=stale-dashboard

STEPS TO REPRODUCE:
1. Sign in, open /dashboard (table shows ids 1, 2)
2. Type "Item X" in the New item field, click Create
3. Observe the table; call GET /api/items with the browser's cookies

EXPECTED: "Item X" appears in the table and in the API response
          (source: verified implementation on the unflagged build — app.py:164-173 redirects to dashboard(), which renders visible_items(user); confirmed by run verify-demo)
ACTUAL:   toast "Item \"Item X\" created" is shown; GET /api/items returns the item (id 8); the table still lists ids 1, 2 and 7

EVIDENCE:
- Screenshot:          runs/20260903-132200/artifacts/ITEM-001/attempt1-screenshot.png
- Page source:         runs/20260903-132200/artifacts/ITEM-001/attempt1-page_source.html (rows 1, 2, 7; no id 8)
- API request/response: runs/20260903-132200/artifacts/ITEM-001/items-after-create.json (200, item id 8 present)
- URL:                 http://127.0.0.1:5000/dashboard (attempt1-url.txt)
- Console / network:   attempt1-browser_console.json (no errors); attempt1-network.json (only favicon.ico 404)
- Repeat frequency:    runs/20260903-132400 — failed 5/5 deterministically; runs/20260903-132300 — ERROR on both diagnostic attempts
- Second symptom:      runs/20260903-132200/artifacts/ITEM-002/ (deleted row still rendered)

ROOT CAUSE:  app.py:158-160 — dashboard() prefers STALE_SNAPSHOT[email] (captured in login(), app.py:140-141) over visible_items(user)
IMPACT:      every user, every create/delete after login; data is correct in the store, wrong on screen
REGRESSION RISK: dashboard() is the only render path for F-002, F-003 and F-004 — a fix there touches all three
AFFECTED COMPONENTS: app.py dashboard(), login(); DASHBOARD template unchanged

RECOMMENDATION: render visible_items(user) on every request; delete STALE_SNAPSHOT
REGRESSION TEST:  ITEM-001 (create → API → table) and ITEM-002 (delete → row gone → API) already guard it; both PASS on the fixed build (run verify-demo)
```
