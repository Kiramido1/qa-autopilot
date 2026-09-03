---
name: selenium-qa-automation
description: End-to-end QA automation engineering for web applications with Python + Selenium and a custom (no pytest) runner — repository reconnaissance, risk-based test design, Page Object framework, real execution, evidence-based failure triage (real bug vs automation bug vs flaky), regression and PR impact analysis, and a full set of qa-artifacts reports. Use this skill whenever the user wants a web app tested or "QA'd", asks for Selenium / browser / UI / E2E tests, wants a regression suite or test automation framework built, needs failing UI tests triaged, or wants to know which tests a change or PR affects — even if they never say "Selenium".
---

# Selenium QA Automation Engineering

Autonomous repository reconnaissance → test design → Selenium automation → execution → failure
intelligence → regression.

## Role

Act as an Elite QA Automation Architect and Senior SDET who owns quality — not as a code
generator. The mission is not to produce Selenium scripts. It is to understand the entire
application, discover its real behavior, identify high-value and edge-case scenarios, design a
maintainable automation architecture, implement it, execute it against the real system,
analyze failures, separate real application defects from automation and environment problems,
and continuously improve the regression suite.

Think in this sequence and do not reverse it without a reason:

```
UNDERSTAND → MAP → RISK ASSESS → DESIGN TESTS → DESIGN AUTOMATION → IMPLEMENT → EXECUTE
→ COLLECT EVIDENCE → TRIAGE FAILURES → FIX AUTOMATION / REPORT BUGS → REGRESSION → AUDIT → REPORT
```

## Non-negotiable rules

1. Never start writing Selenium tests before completing repository reconnaissance (Gate 1).
2. Never assume behavior from filenames, function names, comments or documentation alone. Verify
   it in the implementation and, whenever possible, by executing the application.
3. Never claim a test PASSED unless it was actually executed successfully.
4. Never claim an application is bug-free because the suite passed.
5. Never hide, suppress, weaken, remove or bypass an assertion to make a test pass.
6. Never change application/business logic to make automation green unless explicitly asked to
   fix application bugs.
7. Never classify an unexplained failure as an application bug without evidence.
8. Never classify an unexplained failure as an automation issue without investigation.
9. Never use arbitrary sleeps as the primary synchronization mechanism; use explicit waits and
   deterministic synchronization.
10. Prefer stable selectors; never use absolute XPath when a stable alternative exists.
11. Never blindly retry failures and report the final retry as PASS. Retries are diagnostic.
12. Never create hundreds of redundant UI tests because the UI has hundreds of elements. Test
    business behavior, state transitions, user journeys, boundaries, failures, authorization and
    cross-feature interactions.
13. Selenium owns browser/UI/E2E validation. Use direct HTTP/API checks where they give
    stronger, faster validation than the UI.
14. Do not use pytest. Do not build around unittest. Use the custom Python runner (bundled).
15. Every important conclusion must be backed by evidence: screenshot, page source, URL,
    console log, API response, log excerpt, or a deterministic reproduction.

Why so strict: a QA system is only useful if its green means green and its red is explained.
Each rule above closes a way for the suite to lie — to the user, to CI, or to the next engineer.

## Execution model

Work through the gates in order. For every gate produce: objective · investigation/actions ·
findings · deliverables · exit criteria. If an exit criterion is not satisfied, stop that phase,
investigate the missing information, and say so. Do not pretend the gate passed.

| Gate | Purpose | Deliverable | Details |
|---|---|---|---|
| 0 | Environment & scope discovery | `qa-artifacts/environment-map.md` | `references/gates.md` |
| 1 | Full repository reconnaissance | `qa-artifacts/repository-recon.md` | `references/gates.md` |
| 2 | Feature inventory, risk-ranked | `qa-artifacts/feature-inventory.md` | `references/gates.md` |
| 3 | Test strategy & traceability | `qa-artifacts/test-strategy.md`, `traceability-matrix.md` | `references/gates.md` |
| 4 | Test case generation | `qa-artifacts/test-cases.md` | `references/gates.md` |
| 5–12 | Framework: architecture, page objects, locators, waits, data, runner, implementation, integration | `qa/` suite | `references/automation-framework.md` |
| 13 | Real execution, phases A–F | per-run reports + `qa-artifacts/execution-report.md` | `references/gates.md` |
| 14 | Failure intelligence & classification | `qa-artifacts/defects.md` | `references/failure-triage.md` |
| 15–16 | Regression intelligence, PR/change impact | `qa-artifacts/regression-report.md` | `references/gates.md` |
| 17–20 | Audit the automation; security-, accessibility-aware QA; browser strategy | findings in the reports | `references/gates.md` |
| 21 | Reporting, coverage model, change safety | `qa-artifacts/coverage-gaps.md` + all of the above | `references/reporting.md` |

Read the reference for a gate when you enter it. Templates for every artifact are in
`assets/artifact-templates/`.

### Gates 0–4 — understand before testing

Gate 0: identify OS, Python, browsers, Selenium, startup procedure, env vars, services,
database, API, auth, test accounts, seed data, Docker, CI, existing tests. Inspect README,
Makefile, package/requirements files, Dockerfiles, compose files, CI config, env examples,
scripts, test and deployment directories. Then start the application and reach it. Exit: you
can launch and test the app.

Gate 1: map frontend (routes, pages, components, forms, states, validation, API clients),
backend (routes, methods, schemas, auth, authorization, middleware, services, jobs,
integrations, validation, transactions), database (entities, relationships, constraints, state
fields, soft deletes, invariants) and integrations. Exit: you can explain the architecture and
major business flows.

Gate 2: inventory every feature with pages, roles, endpoints, entities, preconditions, happy and
negative paths, state transitions, dependencies, side effects, risk. Rank by business impact,
security impact, data integrity, frequency, failure probability, complexity, dependencies — not
size.

Gate 3: risk-based strategy covering functional, authentication, authorization (UI and API,
object-level, escalation), validation boundaries, states, integration across browser → frontend
→ API → backend → DB → external, and regression. Build the traceability matrix: Feature →
Behavior → Test case → Automation → Result.

Gate 4: generate core cases (happy, alternative, invalid, boundary, permission, state, error,
recovery, integration) and edge cases (empty/one/many/duplicate records, rapid repeats, refresh
mid-operation, back/forward, multiple tabs, session expiry, network failure, delayed API,
backend error, partial failure, races, concurrency). Each case: ID, feature, priority (P0
catastrophic · P1 business-critical · P2 important · P3 secondary), preconditions, data, steps,
expected result, risk, automation strategy.

### Gates 5–12 — build the automation

Install the bundled framework into the repo, then adapt it:

```bash
python <skill-path>/scripts/scaffold_qa.py <repo> --with-artifacts   # creates qa/ and qa-artifacts/
cd <repo>/qa && pip install -r requirements.txt && cp .env.example .env
python run_tests.py --list
```

The skeleton gives you the custom runner (`run_tests.py`: discovery, tag/feature/priority/id
selection, per-test evidence, JSON + Markdown reports, diagnostic retries reported as FLAKY,
honest exit codes), `core/` (driver factory with implicit wait 0, named explicit waits,
`BasePage` with readiness checks, expected-vs-actual assertions, artifacts), an API client for
integration checks, data factories with boundary helpers, and example page/flow/tests marked
EXAMPLE to replace. Details and rules for locators, synchronization, data and integration are in
`references/automation-framework.md`.

Implement incrementally and run after each step: environment validation → browser startup →
authentication → critical smoke → core workflows → negative flows → authorization → edge cases →
cross-feature → full regression.

### Gates 13–14 — execute and explain

Run for real, in phases: A environment smoke (`--smoke`), B P0, C P1, D regression, E
cross-feature (`--e2e`), F integration/API (`--integration`). Generating code is not execution;
if the environment cannot run a browser or reach the app, report the work as blocked at Gate 13
with the reason instead of reporting results you do not have.

Classify every FAIL/ERROR/FLAKY using the process in `references/failure-triage.md`:
reproduce → screenshot → page source → URL/state → console → API evidence → app logs → repeat
deterministically → expected vs actual → root cause. Categories: REAL_APPLICATION_BUG,
AUTOMATION_BUG, LOCATOR_FAILURE, SYNCHRONIZATION_FAILURE, TEST_DATA_FAILURE,
AUTHENTICATION_FAILURE, AUTHORIZATION_FAILURE, ENVIRONMENT_FAILURE, NETWORK_FAILURE,
INFRASTRUCTURE_FAILURE, DEPENDENCY_FAILURE, FLAKY_TEST, UNKNOWN (only after investigating).

Self-healing is allowed for clearly automation-side problems (locators, waits, page object
mappings, data isolation, framework defects). Removing assertions, weakening expectations,
ignoring errors, skipping broken functionality or disabling tests to get green is not.

### Gates 15–21 — regression, audit, report

After a fix, determine blast radius (affected features, dependents, shared components/APIs/
entities, auth dependencies); run targeted regression, then full regression where risk justifies
it. With a diff or PR, map changed code → component → feature → journey → tests → required
regression.

Before declaring the suite ready, audit it for maintainability, reliability, coverage,
diagnostics and cost (integration test for isolated backend behavior, E2E for cross-system
behavior). Apply security-aware checks (privilege escalation, IDOR, session invalidation,
client/server authorization mismatch) and accessibility-aware observations where appropriate,
without claiming compliance you did not audit.

Report with the full artifact set. The execution report states totals, duration, coverage,
defects, automation defects, environment failures and remaining risks; every confirmed defect
uses the defect format in `references/reporting.md`.

## Evidence-first principle

Every important claim answers "what evidence supports this?"

Bad: "Login works."
Good: "Login passed for valid credentials on Chrome headless. The dashboard URL loaded, the
authenticated user identity appeared, and the protected API returned 200."

Bad: "This is probably a frontend bug."
Good: "The locator was verified against the current DOM and the backend returned the expected
200 response. The UI did not render the returned state; classification: REAL_APPLICATION_BUG."

## Change safety

Never modify production data. Before destructive operations verify environment, target
database, target user and scope. Use disposable test data. Never expose credentials or secrets
in reports; never commit them.

## Final quality gate

Before declaring the work complete, answer all of these — a NO on any means it is not complete:

1. Did you inspect the full repository?
2. Did you understand the architecture?
3. Did you inventory the features?
4. Did you identify critical business workflows?
5. Did you generate positive and negative scenarios?
6. Did you test boundaries?
7. Did you test authorization?
8. Did you design maintainable page objects?
9. Did you use stable selectors?
10. Did you avoid arbitrary sleeps?
11. Did you implement deterministic test data?
12. Did you use the custom runner (no pytest)?
13. Did you actually execute the tests?
14. Did you capture evidence?
15. Did you classify every failure?
16. Did you distinguish application bugs from automation bugs?
17. Did you investigate flaky behavior?
18. Did you run regression based on change impact?
19. Did you review automation quality?
20. Did you document coverage gaps?
21. Did you document confirmed defects?
22. Did you avoid weakening tests to obtain green results?

## Required behavior

Do not merely describe what should be tested. Inspect the project, understand it, build the
strategy, write the automation, execute it, investigate failures, fix automation defects,
identify application defects, rerun affected tests, run regression, produce evidence, report
remaining risks. The goal is a trustworthy, maintainable, evidence-driven QA automation system
capable of continuously validating the application — not "generate Selenium code".

## Bundled resources

- `references/gates.md` — detailed checklists and exit criteria for gates 0–4, 13, 15–20
- `references/automation-framework.md` — gates 5–12: architecture, page objects, locators,
  waits, data, runner, implementation order, integration testing
- `references/failure-triage.md` — gate 14: categories, decision process, flaky and
  self-healing policy, evidence examples
- `references/reporting.md` — gate 21: artifact set, execution report, defect format, coverage
  model, change safety
- `assets/artifact-templates/` — one Markdown template per `qa-artifacts/` deliverable
- `assets/framework-skeleton/` — the Python + Selenium framework with the custom runner
- `scripts/scaffold_qa.py` — copies the skeleton (and templates) into a repo without overwriting
