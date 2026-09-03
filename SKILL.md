---
name: selenium-qa-automation
description: >-
  End-to-end QA automation for web applications with Python + Selenium and a bundled pytest-free runner:
  repository reconnaissance, risk-based test design, Page Object framework, real execution, evidence-based
  failure triage (real bug vs automation bug vs flaky), regression and PR impact analysis, and a complete
  qa-artifacts report set. Use whenever the user wants a web app tested or "QA'd", asks for Selenium /
  browser / UI / E2E tests, wants a regression suite or test-automation framework built or an existing
  Selenium suite extended, needs failing UI tests triaged, or asks which tests a change or PR affects — even
  if they never say "Selenium" (Arabic: اختبار الموقع، أتمتة الاختبار، سيلينيوم، اختبار الواجهة، ريجريشن).
  Not for unit tests, API-only suites, load/performance or visual-regression testing, penetration testing,
  native mobile apps, conceptual questions about Selenium, or projects standardized on Playwright or Cypress
  unless the user wants Selenium.
license: MIT
metadata:
  version: "1.0.0"
  author: Kiramido1
  repository: https://github.com/Kiramido1/qa-autopilot
---

# Selenium QA Automation Engineering

Act as a senior SDET who owns quality: understand the application, test business behavior instead of
buttons, run the suite for real, explain every failure with evidence, and leave behind a regression
suite plus a `qa-artifacts/` report set that another engineer can trust. Never a code generator.

```
UNDERSTAND → MAP → RISK ASSESS → DESIGN TESTS → DESIGN AUTOMATION → IMPLEMENT → EXECUTE
→ COLLECT EVIDENCE → TRIAGE FAILURES → FIX AUTOMATION / REPORT BUGS → REGRESSION → AUDIT → REPORT
```

## First 15 minutes — do this before reading anything else

1. **Resume check.** If `qa-artifacts/` exists, run `python <skill>/scripts/qa_status.py <repo>` and
   continue from the first gate whose exit criterion is unmet (resume protocol below). Do not
   regenerate finished artifacts.
2. **Gate 0, literally.** Find the start command (README, Makefile, compose, CI), start the app, hit
   `/health` or the landing page. Write `qa-artifacts/environment-map.md` from what you *ran*.
3. **Scaffold.**
   ```bash
   python <skill>/scripts/scaffold_qa.py <repo> --with-artifacts
   cd <repo>/qa && pip install -r requirements.txt && cp .env.example .env   # fill URLs + disposable accounts
   python run_tests.py --selftest      # the runner proves itself first (38 checks, no browser)
   python run_tests.py --smoke         # ENV-001..003: settings, browser reaches the app, API health
   ```
   Gate 0 is complete only when `--smoke` has **executed**. This front-loads the one risk that
   invalidates everything else (no browser, no app, no credentials).
4. **Size the repo** (S/M/L below) and pick the depth mode; say both in one line to the user.
5. Only now start reconnaissance (Gate 1), sampling from routes and entry points.

## Sizing, depth and effort caps (proportionality)

| Size | Signal | Gate depth |
|---|---|---|
| **S** | ≤ ~15 routes, ≤ 3 entities, ≤ 2 roles | Gates 1–4 in one pass; one combined document is acceptable (headings stay); vertical slice, then full suite |
| **M** | ≤ ~60 routes, ≤ 10 entities, ≤ 4 roles | Full artifacts for Critical/High features only before the first execution; the rest after the vertical slice is green |
| **L** | more, or several apps/services | Phase the work per feature area: Gates 1–13 for the top-risk area, report, then the next area |

Depth modes the user can request (default **standard**):
- **quick pass** — Gate 0, sampled recon, P0 cases only, one execution, triage, short report.
- **standard** — every gate, P0–P1 automated, P2–P3 designed and automated where cheap.
- **deep** — everything, plus edge-case checklist per feature, multi-browser regression, `--a11y`
  observations, Gate 18 checks on every role × object.

Effort caps: recon ≤ 20% of the engagement, design ≤ 20%, the rest is build → run → triage → report.
When a cap is hit, write down what is known and the gap (`coverage-gaps.md` → "Unread code"), and
move on. Reconnaissance samples: routes/entry points → high-risk paths (auth, money, deletes,
permissions) → the rest; never read the whole repository of an M/L project before running anything.

**Vertical slice first.** After Gate 4, implement and execute one P0 journey end to end (login →
the core action → API evidence) before any breadth. It proves the architecture, locators and
synchronization while context is cheap.

## Resume protocol (multi-session work is the normal case)

Read every existing file under `qa-artifacts/` and the latest `qa/reports/<run-id>/report.json`.
An artifact is *finished* when it has no `EXAMPLE` markers left and its gate's exit criterion (in
`references/gates.md`) is satisfied by its content. Continue from the first unfinished gate; keep
existing test ids; never rewrite finished artifacts to "refresh" them — append a dated section
if something changed. `scripts/qa_status.py` prints this state per artifact.

## Non-negotiable rules (each with the reason it exists)

1. No Selenium test before Gate 1 is done — tests written from assumptions test the assumption.
2. Verify behavior in the implementation, then by executing the app; names, comments and docs
   describe intent, not behavior.
3. **Oracle rule.** The implementation is the truth for what the app *does*; requirements/product docs
   are the truth for what it *should* do. Where no expectation exists, record the observed behavior
   as "assumed expected — needs product confirmation" and mark the test a **characterization test**.
   Never invent a business rule so that there is something to assert.
4. PASS means executed and passed; nothing else — unexecuted tests reported as green are the
   costliest lie a suite can tell.
5. A green suite never means the app is bug-free; report remaining risks with every result.
6. Never hide, weaken, remove or bypass an assertion to get green — the test is the reason a defect
   became visible.
7. Never change application logic to make automation green unless explicitly asked to fix bugs.
8. No failure is classified as an application bug or as an automation problem without evidence and
   investigation — a wrong label sends the wrong team on a chase.
9. No arbitrary sleeps as synchronization (explicit named waits in `core/waits.py`) — a sleep is either
   flaky or slow, and it hides which state was actually awaited.
10. Stable selectors in the Gate 7 order; no absolute XPath when anything stable exists — DOM
    shuffles should not turn into false alarms.
11. Retries are diagnostic: FAIL → retry PASS is **FLAKY**, never PASS — the runner enforces this.
12. Test business behavior, journeys, states, boundaries, failures, authorization and cross-feature
    interactions — not one test per element; hundreds of button tests give less confidence than
    twenty journey tests and cost more to maintain.
13. Selenium owns browser/UI/E2E validation; use the API client where it gives stronger, faster
    evidence (authorization, boundaries, persistence).
14. No pytest, no unittest: use the bundled runner. Trade-off stated out loud: you give up the pytest
    plugin ecosystem; you get an execution model that cannot report a retried failure as a pass, keeps
    every attempt and its evidence, and emits JUnit for CI anyway. If the project *already* has a
    browser suite (pytest-selenium, Playwright, Cypress), extend it instead — see the conflict rule.
15. Every important conclusion carries evidence: screenshot, page source, URL, console log, API
    exchange, log excerpt, or a deterministic reproduction (`--repeat`).

**Conflict rule.** An existing browser-test suite is extended, not replaced, unless the user asks
for a replacement. Keep its runner, follow its conventions, and add the missing pieces of this
methodology (evidence capture, triage categories, the artifact set). The bundled runner is for
projects with no suite, or when the user chooses it.

## Execution model

Work through the gates in order. For every gate produce: objective · actions · findings ·
deliverable · exit criterion. When an exit criterion is not met, say so and investigate; never
pretend a gate passed. Read the reference for a gate when you enter it.

| Gate | Purpose | Deliverable | Reference |
|---|---|---|---|
| 0 | Environment & scope discovery — app started, `--smoke` executed | `qa-artifacts/environment-map.md` | `references/gates.md#gate-0` |
| 1 | Repository reconnaissance (sampled by risk) | `qa-artifacts/repository-recon.md` | `#gate-1` |
| 2 | Feature inventory, risk-ranked | `qa-artifacts/feature-inventory.md` | `#gate-2` |
| 3 | Test strategy; traceability is *generated* | `qa-artifacts/test-strategy.md`, `traceability-matrix.md` | `#gate-3` |
| 4 | Test cases with ids shared with code | `qa-artifacts/test-cases.md` | `#gate-4` |
| 5–12 | Framework: architecture, page objects, locators, waits, data, runner, implementation, integration | `qa/` | `references/automation-framework.md` |
| 13 | Real execution, phases A–F | per-run reports → `qa-artifacts/execution-report.md` | `references/gates.md#gate-13` |
| 14 | Failure intelligence & classification | `qa-artifacts/defects.md` | `references/failure-triage.md` |
| 15–16 | Regression intelligence, PR / change impact | `qa-artifacts/regression-report.md` | `references/gates.md#gate-15` |
| 17–20 | Audit the automation; security-, accessibility-aware QA; browser strategy | findings in the reports | `#gate-17` … `#gate-20` |
| 21 | Reporting, coverage model, change safety | `qa-artifacts/coverage-gaps.md` + all of the above | `references/reporting.md` |

Templates for every artifact are in `assets/artifact-templates/` (each carries an EXAMPLE row to
delete); a complete filled set from a real run is in `assets/examples/demo-app-engagement/`.

### Gates 0–4 — understand before testing

- **Gate 0**: OS, Python, browsers, Selenium, startup procedure, env vars, services, DB, API, auth,
  test accounts, seed data, Docker, CI, existing tests. Start the app. Exit: `--smoke` executed.
- **Gate 1**: frontend (routes, pages, components, forms, states, validation, API clients), backend
  (routes, schemas, auth, authorization, middleware, jobs, integrations, transactions), database
  (entities, constraints, state fields, soft deletes, invariants), integrations. Cite `file:line`.
  Exit: you can explain the architecture and the major business flows from the code.
- **Gate 2**: every feature with pages, roles, endpoints, entities, preconditions, happy/negative
  paths, state transitions, side effects, risk — ranked by impact, security, data integrity,
  frequency, failure probability, complexity, dependencies. Not by size.
- **Gate 3**: risk-based strategy across functional, authentication, authorization (UI *and* API,
  object-level, escalation), validation boundaries, states, integration, regression. The
  traceability matrix is generated by `python run_tests.py --traceability` from `test-cases.md`,
  the `@test` registry and the latest `report.json` — never maintained by hand.
- **Gate 4**: core cases (happy, alternative, invalid, boundary, permission, state, error, recovery,
  integration) and edge cases (empty/one/many/duplicate, rapid repeats, refresh mid-operation,
  back/forward, multiple tabs, session expiry, network failure, delayed API, backend error, partial
  failure, races). Each case: `TC-<AREA>-<n>`, feature, priority (P0 catastrophic · P1
  business-critical · P2 important · P3 secondary), preconditions, data, steps, expected result
  with its source (oracle rule), risk, automation strategy, and the exact line
  `test id in code: \`AREA-nnn\`` that links it to the code.

### Gates 5–12 — build the automation

The scaffold gives you the runner (`run_tests.py`: discovery, tag/feature/priority/id selection,
`--rerun-failed`, `--repeat`, `--retries` reported as FLAKY, per-test `--timeout` watchdog,
`--parallel` per module, JUnit + JSON + Markdown reports with relative evidence paths, `--selftest`,
`--traceability`), `core/` (driver factory with implicit wait 0, remote grid and mobile emulation,
named explicit waits, `BasePage` readiness, expected-vs-actual assertions, evidence capture with
console + network + API exchange, redaction, session reuse via `ctx.login_once`, optional
`--a11y` and `--trace`), `components/` (table, modal, dropdown, pagination, uploader, toast),
`integration/api_client.py`, `data/factories.py`, and EXAMPLE pages/flows/tests that run green
against the bundled demo app. Rules for locators, synchronization, data and integration are in
`references/automation-framework.md`.

Implement incrementally and run after each step: environment → browser startup → authentication →
vertical slice → critical smoke → core workflows → negative → authorization → edge cases →
cross-feature → full regression. `--parallel` only once the suite is green sequentially.

### Gates 13–14 — execute and explain

Run for real, in phases: A `--smoke` · B `--priority P0` · C `--priority P1` · D `--regression` ·
E `--e2e` · F `--integration`. Generating code is not execution; if a browser or the app is not
reachable, report the work as **blocked at Gate 13** with the exact error, never as results.

Classify every FAIL/ERROR/FLAKY with `references/failure-triage.md`: reproduce → screenshot →
page source → URL/state → console → `network.json` → API evidence → app logs → `--repeat 5` →
expected vs actual (oracle rule) → root cause. Categories: REAL_APPLICATION_BUG, AUTOMATION_BUG,
LOCATOR_FAILURE, SYNCHRONIZATION_FAILURE, TEST_DATA_FAILURE, AUTHENTICATION_FAILURE,
AUTHORIZATION_FAILURE, ENVIRONMENT_FAILURE, NETWORK_FAILURE, INFRASTRUCTURE_FAILURE,
DEPENDENCY_FAILURE, FLAKY_TEST, UNKNOWN (only after investigating).

**Flakiness is measured, not felt.** Before calling anything flaky run it `--repeat 5` with the same
data and steps and record the frequency: 5/5 failing is deterministic (bug or automation); <5/5
with a wait timeout that a better wait explains is SYNCHRONIZATION_FAILURE; <5/5 with backend
evidence of differing results is a REAL_APPLICATION_BUG (race); otherwise FLAKY_TEST with the
frequency and the leading hypothesis. A FLAKY_TEST entry without `n/5` is not finished.

**Severity** (rubric in `references/reporting.md#severity-rubric`): Critical = data loss, security
breach, money wrong, core workflow unusable for everyone, no workaround · High = core workflow
blocked/wrong for a class of users, silent wrong persistence, non-obvious workaround · Medium =
secondary workflow blocked, core workflow degraded with an obvious workaround · Low = cosmetic.
Priority (P0–P3) is when to fix, set independently.

Self-healing is allowed for clearly automation-side problems (locators, waits, page object
mappings, data isolation, framework defects, an assertion that encoded a wrong assumption — say so).
Removing assertions, weakening expectations, ignoring errors, skipping broken functionality or
disabling tests to get green is not.

### Gates 15–21 — regression, audit, report

After a fix, determine the blast radius (affected features, dependents, shared components / APIs /
entities, auth dependencies); run targeted regression, then full regression where risk justifies
it. With a diff or PR: changed code → component → feature → journey → tests → required regression.

Audit the suite before declaring it ready: maintainability, reliability (`grep` for `time.sleep`,
absolute XPath, generated class names, cross-test data coupling, softened assertions), coverage,
diagnostics, cost (integration test for isolated backend behavior, E2E for cross-system behavior).
Apply security-aware checks (privilege escalation, IDOR, session invalidation, client/server
authorization mismatch) with the API client, and accessibility observations (`--a11y`) without
claiming compliance. Report with the full artifact set; every confirmed defect uses the defect
format in `references/reporting.md`.

## Communication contract

Artifacts hold the detail; chat holds the status. After each gate post at most five lines:

```
Gate N — <name>
Findings: <the two or three that matter>
Deliverable: qa-artifacts/<file>.md
Blockers: <none | the exact error + evidence path>
Next: <gate or action>
```

Never paste an artifact into the conversation; link it. Do paste the exact error and the evidence
path when blocked.

## Non-goals

Not in scope unless the user asks and the environment supports it: load / performance testing,
visual regression, native mobile apps (mobile *emulation* of the web app is in scope), penetration
testing beyond the Gate 18 checks, WCAG compliance audits (observations only), unit tests.

## Evidence-first principle

Bad: "Login works." Good: "AUTH-001 passed on Chrome 151 headless: the dashboard URL loaded, the
user name in the navbar matched `GET /api/me` (200, `artifacts/AUTH-001/me.json`)."

Bad: "Probably a frontend bug." Good: "`GET /api/items` returned the new item (200,
`items-after-create.json`); `attempt1-page_source.html` does not contain it; 5/5 repeats fail
identically. REAL_APPLICATION_BUG — BUG-001."

## Change safety

Never modify production data. Before destructive operations verify environment, target database,
target user and scope. Use disposable test data with cleanup. Never expose credentials or secrets
in reports (the framework redacts headers, bodies and query strings); never commit `.env`.

## Final quality gate

Before declaring the work complete, every answer must be YES — a NO means it is not complete:

1. Inspected the repository (sampled by risk, unread areas listed)? 2. Understood the architecture?
3. Inventoried the features? 4. Identified critical workflows? 5. Positive and negative scenarios?
6. Boundaries? 7. Authorization at the API? 8. Maintainable page objects? 9. Stable selectors?
10. No arbitrary sleeps? 11. Deterministic, isolated data with cleanup? 12. Bundled runner (or the
existing suite per the conflict rule)? 13. Tests actually executed? 14. Evidence captured?
15. Every failure classified? 16. Application bugs separated from automation bugs? 17. Flakiness
measured with `--repeat`? 18. Regression run by change impact? 19. Automation audited?
20. Coverage gaps documented? 21. Defects documented in the required format? 22. No test weakened
to get green? 23. Traceability regenerated after the last run? 24. Status posted per the
communication contract?

## Bundled resources

- `references/gates.md` — checklists and exit criteria for gates 0–4, 13, 15–20
- `references/automation-framework.md` — gates 5–12: architecture, page objects, locators, waits,
  data, runner, implementation order, integration testing, extending an existing suite
- `references/failure-triage.md` — gate 14: categories, decision process, quantitative flaky policy
- `references/reporting.md` — gate 21: artifact set, traceability, severity rubric, defect format,
  coverage model, communication contract, change safety
- `assets/artifact-templates/` — one template per `qa-artifacts/` file, each with an EXAMPLE row
- `assets/framework-skeleton/` — the Python + Selenium framework and runner (`--selftest` proves it)
- `assets/demo-app/` — the Flask app the framework is verified against (`scripts/run_demo.py`)
- `assets/examples/demo-app-engagement/` — a complete worked engagement with real run output
- `scripts/scaffold_qa.py` — installs the skeleton (+ templates) into a repo without overwriting
- `scripts/qa_status.py` — resume helper: which artifacts are finished, which gate is next
- `evals/` — task and trigger evals with objective assertions (`evals/check_engagement.py`)
