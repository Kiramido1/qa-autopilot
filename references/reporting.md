# Reporting — Gate 21, severity rubric, coverage model, change safety

## The artifact set

Every engagement produces these, using the templates in `assets/artifact-templates/`
(installed with `scripts/scaffold_qa.py <repo> --with-artifacts`). A complete filled set is in
`assets/examples/demo-app-engagement/qa-artifacts/`.

```
qa-artifacts/
├── environment-map.md        Gate 0   (gates.md#gate-0)
├── repository-recon.md       Gate 1   (gates.md#gate-1)
├── feature-inventory.md      Gate 2   (gates.md#gate-2)
├── test-strategy.md          Gate 3   (gates.md#gate-3)
├── traceability-matrix.md    Gate 3, regenerated through Gate 13 (#traceability below)
├── test-cases.md             Gate 4   (gates.md#gate-4)
├── execution-report.md       Gate 13 / 21 (#execution-report below)
├── defects.md                Gate 14  (#defect-report-format below)
├── regression-report.md      Gates 15 / 16 (gates.md#gate-15, #gate-16)
└── coverage-gaps.md          Gate 21  (#coverage-model below)
```

Write them as you go, not at the end: each gate's exit criterion is checked against its
artifact, and a report written from memory after the fact loses the evidence. For an S-sized
repository (SKILL.md sizing rule) gates 1–4 may share one document; the headings stay.

## Traceability

The matrix is derived, not maintained: `python run_tests.py --traceability` regenerates
`qa-artifacts/traceability-matrix.md` from three sources that already exist —

- `test-cases.md`: sections `## TC-<AREA>-<n> — <title>` with `- Feature: … | Priority: … | Risk: …`
  and the exact phrase `test id in code: \`AUTH-001\``,
- the `@test(id=…)` registry (feature, priority, file),
- the latest `reports/<run-id>/report.json` (or `--from-run <id>`): last status per test,
- `execution-report.md`: the category you wrote for each FAIL/ERROR/FLAKY — any block (bullet or
  heading with its indented lines) that names the test id together with a triage category. Until
  then the matrix shows `UNCLASSIFIED`, which is the runner's honest default.

It lists test cases without automation and automation without a test case; both are gaps to
close or to justify in `coverage-gaps.md`. Regenerate after adding cases and after each
execution phase.

## Execution report

Must contain: total tests · passed · failed · errors · skipped · flaky · duration · browser and
build id · coverage · defects · automation defects · environment failures · flaky tests with
frequency · remaining risks.

The runner generates `reports/<run-id>/execution-report.md`, `report.json` and `junit.xml` per
run with totals, per-test results, every attempt and the evidence paths (relative to the run
directory). The consolidated `qa-artifacts/execution-report.md` summarizes the runs that matter
(phases A–F, targeted and full regression, repeat runs) and replaces every `UNCLASSIFIED` with a
category and its evidence.

Report skips explicitly with their reason. A skipped P0 is a coverage gap, not a pass. A test
that ran only on one browser is a result for that browser.

## Severity rubric

Severity is impact on the user and the business, judged from evidence; priority is when it
should be fixed. They are set independently.

| Severity | Criteria (any one is enough) |
|---|---|
| **Critical** | data loss or corruption · security breach (auth bypass, privilege escalation, IDOR, secret exposure) · payment/money incorrect · the whole application or a core workflow unusable for all users · no workaround |
| **High** | a core workflow blocked or wrong for a class of users or data · incorrect results silently persisted · a workaround exists but is not obvious to the user |
| **Medium** | a secondary workflow blocked or wrong · a core workflow degraded (extra steps, confusing state) with an obvious workaround · validation gaps without data-integrity impact |
| **Low** | cosmetic · wording · layout · inconsistencies with no functional effect · edge cases with negligible frequency |

Do not inflate: a High needs evidence of the blocked workflow (screenshot + API), a Critical
needs evidence of the loss, breach or unusability. Do not deflate either: "has a workaround"
lowers High to Medium only when the user can be expected to find it.

## Defect report format

For every confirmed application defect (`assets/artifact-templates/defects.md` carries a filled
example):

```
BUG ID:
TITLE:
SEVERITY:        Critical / High / Medium / Low — with the rubric criterion that applies
PRIORITY:        P0 / P1 / P2 / P3
FEATURE:
ENVIRONMENT:     env, browser + version, build id / commit

PRECONDITIONS:

STEPS TO REPRODUCE:
1.
2.
3.

EXPECTED:        with its source (requirement, verified implementation, or "assumed expected — needs product confirmation")
ACTUAL:

EVIDENCE:
- Screenshot
- Logs
- API request/response
- URL
- Repeat frequency (--repeat)
- Database evidence where appropriate

ROOT CAUSE:      file:line when you found it; "not located" otherwise
IMPACT:
REGRESSION RISK:
AFFECTED COMPONENTS:

RECOMMENDATION:
REGRESSION TEST:  test id that now guards it
```

Where useful, add which layer owns the fix (frontend, backend, both) with the evidence that
decides it — e.g. the endpoint returns the right data but the UI never renders it.

## Coverage model

Measure coverage across: features · user roles · user journeys · APIs · pages · states ·
negative paths · boundary conditions · authorization paths · cross-feature flows · browsers ·
regression · and, for sampled reconnaissance, the code you did not read.

Never define coverage only as "number of automated tests". 1000 weak tests can provide less
confidence than 100 high-quality tests. Record what is not covered and why in
`coverage-gaps.md`; an honest gap list is worth more than an inflated pass count.
Accessibility observations from `--a11y` go here or in the execution report as observations —
never as a compliance claim.

## Communication contract

Artifacts hold the detail; chat holds the status. After each gate, post at most five lines:

```
Gate 4 — test cases
Findings: 14 cases (3 P0, 6 P1), 2 behaviors need product confirmation (TC-AUTH-900, TC-ITEM-900)
Deliverable: qa-artifacts/test-cases.md
Blockers: none
Next: Gate 5–12 vertical slice: AUTH-001 end to end
```

Do not paste artifacts into the conversation; link them. Do paste the exact error and the
evidence path when you are blocked.

## Change safety

Never modify production data. Before destructive operations verify: environment · target
database · target user · scope. Use disposable test data wherever possible.

Never expose credentials or secrets in reports (the API client and `ctx.attach()` redact
headers, bodies and query strings through `core/redact.py`; settings are written with
`redacted()`). Never commit secrets into source control — `.env` is git-ignored in the
skeleton; keep it that way.
