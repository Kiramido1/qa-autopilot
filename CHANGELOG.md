# Changelog

All notable changes to the `selenium-qa-automation` skill. Versions follow `metadata.version` in `SKILL.md`.

## [1.0.0] — 2026-09-03

First tagged release: methodology, framework, demo app, worked example, evals and CI are all in place and
verified against each other (see `benchmark.md`).

### Methodology (SKILL.md, references)
- "First 15 minutes" section: resume check → start the app → scaffold → `--selftest` → `--smoke` → size the repo.
- Sizing rule (S/M/L), depth modes (quick pass / standard / deep), effort caps, reconnaissance sampling, vertical slice first.
- Resume protocol for multi-session work, backed by `scripts/qa_status.py`.
- Oracle rule: implementation = what the app does, requirements = what it should do; "assumed expected — needs product
  confirmation" and characterization tests; never invent a business rule.
- Severity rubric (Critical/High/Medium/Low with criteria), set independently of priority.
- Quantitative flaky policy: `--repeat 5` before any classification; the n/5 table.
- Communication contract (five-line status per gate), non-goals, conflict rule for existing suites.
- Every non-negotiable rule carries its reason; rule 14 (no pytest) states the trade-off.
- Traceability is derived (`run_tests.py --traceability`) from `test-cases.md`, the registry, `report.json`
  and the classifications in `execution-report.md`.
- Gate 0 exit criterion made literal (ENV-* executed); every reference section names its template and vice versa.
- Description gains negative triggers, the "extend an existing suite" case and Arabic phrases.

### Framework skeleton
- `--selftest` (41 runner checks, no browser), JUnit XML, relative evidence paths, `--rerun-failed`, `--repeat`,
  per-test `--timeout` watchdog, `--parallel` per module, `setup_module`/`teardown_module` and session hooks,
  `ctx.login_once` session reuse (`--fresh-session`), network evidence from Chrome performance logs,
  redaction of headers, bodies and query strings, `--remote-url`, `--device` mobile emulation, generic
  components (table, modal, dropdown, pagination, file uploader), `by_testid()` with configurable attribute,
  `--a11y` axe-core observations, `--trace`, build identity (git SHA/branch, `QA_BUILD_ID`) and browser/driver
  versions in run metadata, ruff + mypy config, Makefile, Windows notes.

### Repository
- Demo app (`assets/demo-app/`) with injectable defects; `scripts/run_demo.py`; a full worked engagement with
  the runner's real output (`assets/examples/demo-app-engagement/`); `evals/` with task and trigger evals and
  `check_engagement.py`; `docs/walkthrough.md`; GitHub Actions (self-test, lint/mypy, Chrome + Firefox runs,
  parallel run, injected-defect detection); issue templates; `CONTRIBUTING.md`; `benchmark.md`.

## [0.1.0] — 2026-09-03

Initial skill: SKILL.md with 15 rules and 22 gates, four references, ten artifact templates, framework skeleton
with the custom runner, `scripts/scaffold_qa.py`.
