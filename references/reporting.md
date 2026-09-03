# Reporting — Gate 21, coverage model, change safety

## The artifact set

Every engagement produces these, using the templates in `assets/artifact-templates/`
(installed with `scripts/scaffold_qa.py <repo> --with-artifacts`):

```
qa-artifacts/
├── environment-map.md        Gate 0
├── repository-recon.md       Gate 1
├── feature-inventory.md      Gate 2
├── test-strategy.md          Gate 3
├── traceability-matrix.md    Gate 3 (updated through Gate 13)
├── test-cases.md             Gate 4
├── execution-report.md       Gate 13 / 21
├── defects.md                Gate 14
├── regression-report.md      Gates 15 / 16
└── coverage-gaps.md          Gate 21
```

Write them as you go, not at the end: each gate's exit criterion is checked against its
artifact, and a report written from memory after the fact loses the evidence.

## Execution report

Must contain: total tests · passed · failed · skipped · flaky · duration · coverage · defects ·
automation defects · environment failures · remaining risks.

The runner generates `reports/<run-id>/execution-report.md` and `report.json` per run with
totals, per-test results, every attempt and the evidence paths. The consolidated
`qa-artifacts/execution-report.md` summarizes the runs that matter (phases A–F, targeted and
full regression) and replaces every `UNCLASSIFIED` with a category and its evidence.

Report skips explicitly with their reason. A skipped P0 is a coverage gap, not a pass.

## Defect report format

For every confirmed application defect:

```
BUG ID:
TITLE:
SEVERITY:
PRIORITY:
FEATURE:
ENVIRONMENT:

PRECONDITIONS:

STEPS TO REPRODUCE:
1.
2.
3.

EXPECTED:
ACTUAL:

EVIDENCE:
- Screenshot
- Logs
- API response
- URL
- Database evidence where appropriate

ROOT CAUSE:
IMPACT:
REGRESSION RISK:
AFFECTED COMPONENTS:

RECOMMENDATION:
```

Severity reflects impact; do not inflate it without evidence. Where useful, add which layer
owns the fix (frontend, backend, both) with the evidence that decides it — e.g. the endpoint
exists in the API docs and returns the right data but the UI never calls it.

## Coverage model

Measure coverage across: features · user roles · user journeys · APIs · pages · states ·
negative paths · boundary conditions · authorization paths · cross-feature flows · browser
coverage · regression coverage.

Never define coverage only as "number of automated tests". 1000 weak tests can provide less
confidence than 100 high-quality tests. Record what is not covered and why in
`coverage-gaps.md`; an honest gap list is worth more than an inflated pass count.

## Change safety

Never modify production data. Before destructive operations verify: environment · target
database · target user · scope. Use disposable test data wherever possible.

Never expose credentials or secrets in reports (the API client redacts auth headers; settings
are written with `redacted()`). Never commit secrets into source control — `.env` is
git-ignored in the skeleton; keep it that way.
