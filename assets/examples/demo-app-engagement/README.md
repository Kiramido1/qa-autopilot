# Worked example — the skill applied to the demo app

This directory is one complete engagement of the `selenium-qa-automation` skill against
`assets/demo-app/app.py`, started with `DEMO_BUGS=stale-dashboard` so that a real application
defect exists to find, triage and report. Every artifact under `qa-artifacts/` is what the agent is
expected to produce; every claim in them cites a file, a route in `app.py` or a run id.

Nothing here is mocked. The reports under `runs/` are the runner's own output copied verbatim:
`report.json`, `junit.xml`, `execution-report.md` and, for the defective run, the
`artifacts/ITEM-001/` evidence (screenshot, page source, browser console, failed network requests,
exception, context, and the API exchange attached by the test). Evidence paths inside them are
relative to the run directory, which is why they still resolve here.

`traceability-matrix.md` was generated, not written:
`run_tests.py --traceability --artifacts-dir qa-artifacts --from-run 20260903-132200` — it reads
`test-cases.md`, the `@test` registry and the run, and picks up the classifications from
`execution-report.md`.

## Reproduce

```bash
pip install -r assets/framework-skeleton/requirements.txt -r assets/demo-app/requirements.txt
python scripts/run_demo.py --bugs stale-dashboard --run-id 20260903-132200                                   # 12 pass, 2 error
python scripts/run_demo.py --bugs stale-dashboard --run-id 20260903-132300 --rerun-failed 20260903-132200 --retries 1
python scripts/run_demo.py --bugs stale-dashboard --run-id 20260903-132400 --test ITEM-001 --repeat 5        # 0/5
python scripts/run_demo.py --run-id verify-demo                                                              # flag off: 14 pass
QA_BROWSER=firefox python scripts/run_demo.py --run-id demo-firefox --test AUTH-001 --test AUTH-002 --test ITEM-001
python scripts/run_demo.py --run-id demo-mobile --test ENV-002 --test AUTH-001 --device "iPhone 12 Pro"
python scripts/run_demo.py --run-id demo-trace --test ITEM-001 --a11y --trace
cd assets/framework-skeleton && QA_REPORTS_DIR=../examples/demo-app-engagement/runs \
  python run_tests.py --traceability --artifacts-dir ../examples/demo-app-engagement/qa-artifacts --from-run 20260903-132200
```

On a machine where Selenium Manager cannot download drivers (this run: Debian 13, chromedriver 151
packaged), set `QA_CHROMEDRIVER_PATH` and `QA_CHROME_BINARY` first.

## Sizing and depth

The demo app is size **S**: two accounts / one role pair (user, admin), ~13 routes, one entity
(`Item`), no external integrations. Gates 1–4 were therefore done in one pass each, and the vertical
slice (login → create item → verify via API) was implemented and executed before any breadth.
Depth mode: standard.

## What the example demonstrates

| Topic | Where |
|---|---|
| Gate 0 exit criterion taken literally: ENV-001..003 executed before anything else | `qa-artifacts/environment-map.md`, run `20260903-132200` |
| Recon from the implementation, with line numbers, not from the README | `qa-artifacts/repository-recon.md` |
| Risk ranking that is not size ranking (a 4-line ownership check is Critical) | `qa-artifacts/feature-inventory.md` |
| Oracle rule: expected results cite `app.py:line`; two "assumed expected — needs product confirmation" cases; a characterization test | `qa-artifacts/test-cases.md` (TC-AUTH-005, TC-AUTH-900, TC-ITEM-003) |
| A generated traceability matrix with classifications pulled from the execution report | `qa-artifacts/traceability-matrix.md` |
| ERROR (wait timeout) triaged as REAL_APPLICATION_BUG, not SYNCHRONIZATION_FAILURE, from API + page-source evidence | `qa-artifacts/execution-report.md`, `runs/20260903-132200/artifacts/ITEM-001/` |
| Flakiness ruled out quantitatively (`--repeat 5` → 0/5; `--rerun-failed --retries 1` → ERROR twice) | `runs/20260903-132400/`, `runs/20260903-132300/` |
| An AUTOMATION_BUG (AUTH-003's assertion) fixed by *strengthening* the assertion | `qa-artifacts/execution-report.md` → Automation defects |
| A defect report in the required format, severity justified by the rubric | `qa-artifacts/defects.md` |
| Blast radius of the fix and the regression that proves it (`verify-demo`, Firefox, mobile) | `qa-artifacts/regression-report.md`, `runs/verify-demo/`, `runs/demo-firefox/`, `runs/demo-mobile/` |
| Honest coverage gaps, including two axe-core observations that are not a WCAG claim | `qa-artifacts/coverage-gaps.md`, `runs/demo-trace/` |
| The mechanical audit passes | `python evals/check_engagement.py assets/examples/demo-app-engagement --qa assets/framework-skeleton --reports assets/examples/demo-app-engagement/runs --run 20260903-132200` |

## Files

```
demo-app-engagement/
├── README.md
├── qa-artifacts/                 all ten deliverables, filled
└── runs/
    ├── 20260903-132200/          full run with the defect: report.json · junit.xml · execution-report.md · artifacts/ITEM-001/
    ├── 20260903-132300/          --rerun-failed --retries 1: execution-report.md (ERROR on both attempts)
    ├── 20260903-132400/          --repeat 5 on ITEM-001: execution-report.md (0/5)
    ├── verify-demo/              the fixed build: 14/14
    ├── demo-firefox/             AUTH-001, AUTH-002, ITEM-001 on Firefox 140
    ├── demo-mobile/              ENV-002, AUTH-001 with iPhone 12 Pro emulation
    └── demo-trace/               ITEM-001 with --a11y --trace: execution-report.md · junit.xml · artifacts/ITEM-001/attempt1-a11y.json
```
