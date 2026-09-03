# Execution report

> Gate 13/21 — phases in `references/gates.md#gate-13`, required contents in `references/reporting.md#execution-report`.
> The runner generates `reports/<run-id>/execution-report.md`, `report.json` and `junit.xml` per run; this file is
> the consolidated view. A test is PASSED only if it actually ran and passed. FAIL → retry PASS is FLAKY.
> Every FAIL/ERROR/FLAKY gets a category from `references/failure-triage.md`. Delete EXAMPLE rows after use;
> full example in `assets/examples/demo-app-engagement/qa-artifacts/execution-report.md`.

## Runs included
| Run id | Selection | Browser | Environment | Total | Passed | Failed | Errors | Flaky | Skipped | Duration |
|---|---|---|---|---|---|---|---|---|---|---|
| EXAMPLE 20260903-132200 | all | chrome 151 headless | local, build demo-app@stale-dashboard | 14 | 12 | 0 | 2 | 0 | 0 | 30.7s |

## Coverage achieved
- Features / roles / journeys / APIs / pages / states / negative paths / boundaries / authorization paths / cross-feature / browsers:

## Confirmed application defects
- BUG-ID → title → severity → see defects.md <!-- EXAMPLE: BUG-001 → dashboard shows stale item list → High -->

## Automation defects (fixed / open)
- Test id → root cause → fix → rerun result <!-- EXAMPLE: AUTH-003 → asserted on the whole URL, redirect carries ?next=/dashboard → compare path only → PASS -->

## Environment / infrastructure failures
-

## Flaky tests under investigation
- Test id → frequency (`--repeat 5`) → suspected cause

## Remaining risks
-
