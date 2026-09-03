# Traceability matrix

> Derived, not hand-maintained: regenerate with `python run_tests.py --traceability` (reads `test-cases.md`,
> the `@test` registry, the latest `reports/<run-id>/report.json` and the classifications in
> `execution-report.md`). The generator overwrites this file.
> Format reference: `references/reporting.md#traceability`; example output in
> `assets/examples/demo-app-engagement/qa-artifacts/traceability-matrix.md`.

| Feature | Behavior / rule | Test case | Automation id · file | Last result (run) | Notes |
|---|---|---|---|---|---|
| EXAMPLE items | Creating an item through the UI persists it and shows it in the table | TC-ITEM-001 | `ITEM-001` · tests/e2e/test_items_example.py | ERROR (20260903-132200) | REAL_APPLICATION_BUG → BUG-001 |

## Summary
- Test cases: · automated: · not automated:
- Registered tests: · without a test case:

## Uncovered behaviors
- Behavior → why not covered → plan:
