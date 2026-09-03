# Traceability matrix

> Generated 2026-09-03 11:28 UTC by `run_tests.py --traceability` from `test-cases.md`, the @test registry, run `20260903-132200` and the classifications in `execution-report.md`.
> Do not edit by hand — regenerate after adding test cases or running the suite.

| Feature | Behavior / rule | Test case | Automation id · file | Last result (run) | Notes |
|---|---|---|---|---|---|
| environment | Settings provide a base URL | TC-ENV-001 | `ENV-001` · tests/smoke/test_environment.py | PASS (20260903-132200) |  |
| environment | The browser starts and renders the application | TC-ENV-002 | `ENV-002` · tests/smoke/test_environment.py | PASS (20260903-132200) |  |
| environment | The API health endpoint answers | TC-ENV-003 | `ENV-003` · tests/smoke/test_environment.py | PASS (20260903-132200) |  |
| authentication | Valid credentials reach the dashboard and the backend recognises the browser session | TC-AUTH-001 | `AUTH-001` · tests/regression/test_login_example.py | PASS (20260903-132200) |  |
| authentication | Wrong password shows an error and stays on the login page | TC-AUTH-002 | `AUTH-002` · tests/regression/test_login_example.py | PASS (20260903-132200) |  |
| authentication | Direct URL access to the dashboard without a session redirects to login | TC-AUTH-003 | `AUTH-003` · tests/regression/test_login_example.py | PASS (20260903-132200) |  |
| authentication | Logout invalidates the session | TC-AUTH-004 | `AUTH-004` · tests/regression/test_login_example.py | PASS (20260903-132200) |  |
| authentication | A protected endpoint rejects anonymous requests | TC-API-001 | `API-001` · tests/integration/test_api_example.py | PASS (20260903-132200) |  |
| items | Item name boundaries: 1 and 50 accepted, 0 / 51 / whitespace rejected | TC-API-002 | `API-002` · tests/integration/test_api_example.py | PASS (20260903-132200) |  |
| items | A user cannot delete another user's item (IDOR) | TC-API-003 | `API-003` · tests/integration/test_api_example.py | PASS (20260903-132200) |  |
| items | A regular user only sees their own items | TC-API-004 | `API-004` · tests/integration/test_api_example.py | PASS (20260903-132200) |  |
| items | Creating an item through the UI persists it and shows it in the table | TC-ITEM-001 | `ITEM-001` · tests/e2e/test_items_example.py | ERROR (20260903-132200) | REAL_APPLICATION_BUG |
| items | Confirming the delete dialog removes the row and the backend no longer returns the item | TC-ITEM-002 | `ITEM-002` · tests/e2e/test_items_example.py | ERROR (20260903-132200) | REAL_APPLICATION_BUG |
| items | Cancelling the delete dialog changes nothing | TC-ITEM-003 | `ITEM-003` · tests/e2e/test_items_example.py | PASS (20260903-132200) |  |
| authentication | Email is trimmed and lower-cased before lookup | TC-AUTH-005 | — | — | not automated |
| authentication | Session expiry after inactivity | TC-AUTH-900 | — | — | not automated |
| items | Concurrent creation from two tabs | TC-ITEM-900 | — | — | not automated |

## Summary

- Test cases: 17 · automated: 14 · not automated: 3
- Registered tests: 14 · without a test case: 0
- Results from run: 20260903-132200

## Uncovered behaviors

- TC-AUTH-005 — Email is trimmed and lower-cased before lookup → no automation id declared
- TC-AUTH-900 — Session expiry after inactivity → no automation id declared
- TC-ITEM-900 — Concurrent creation from two tabs → no automation id declared
