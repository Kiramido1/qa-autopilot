# Gate details — discovery, design, execution, regression, audits

Companion to SKILL.md. Read the section for the gate you are entering; each ends with the
exit criterion that must be true before moving on. Gates 5–12 (framework build) are in
`automation-framework.md`, Gate 14 (triage) in `failure-triage.md`, Gate 21 (reports) in
`reporting.md`. Templates for every deliverable live in `assets/artifact-templates/`.

Contents
- [Gate 0 — Environment & scope discovery](#gate-0--environment--scope-discovery)
- [Gate 1 — Full repository reconnaissance](#gate-1--full-repository-reconnaissance)
- [Gate 2 — Application feature inventory](#gate-2--application-feature-inventory)
- [Gate 3 — Test strategy & traceability](#gate-3--test-strategy--traceability)
- [Gate 4 — Test case generation](#gate-4--test-case-generation)
- [Gate 13 — Real execution](#gate-13--real-execution)
- [Gate 15 — Regression intelligence](#gate-15--regression-intelligence)
- [Gate 16 — PR / change impact analysis](#gate-16--pr--change-impact-analysis)
- [Gate 17 — Quality review of the automation itself](#gate-17--quality-review-of-the-automation-itself)
- [Gate 18 — Security-aware QA](#gate-18--security-aware-qa)
- [Gate 19 — Accessibility-aware QA](#gate-19--accessibility-aware-qa)
- [Gate 20 — Browser strategy](#gate-20--browser-strategy)

---

## Gate 0 — Environment & scope discovery

Objective: know how to launch and reach the application before anything else.

Identify: operating system · Python version · browser availability and versions · Selenium
version · application startup procedure · required environment variables · required services ·
database availability · API availability · authentication requirements · test accounts · seed
data · Docker/container setup · CI/CD configuration · existing test infrastructure · existing
automation · build/install commands.

Inspect: README · Makefile · package files · requirements files · pyproject.toml · Dockerfiles ·
docker-compose files · CI configuration · environment examples · scripts · test directories ·
deployment files.

Then actually start the application and hit it (browser or HTTP). A startup command copied from
a README that you have not run is an assumption, not a finding.

Deliverable: `qa-artifacts/environment-map.md` — environment, dependencies, startup instructions,
browser matrix, required credentials/configuration (names, never values), known limitations,
existing tests, existing automation.

Exit criterion: you can launch and test the application. If not, stop and investigate the gap
(missing service, credentials, browser). Do not proceed on the assumption that it will work later.

---

## Gate 1 — Full repository reconnaissance

Objective: understand the real architecture and behavior from the implementation.

Frontend — identify: framework · routing · pages · components · forms · modals · tables ·
filters · search · pagination · uploads · downloads · authentication UI · role-based UI · loading
states · empty states · error states · toasts · notifications · navigation · responsive behavior ·
client-side validation · API clients · state management.

Backend — identify: routes · HTTP methods · request schemas · response schemas · authentication ·
authorization · middleware · services · repositories · background jobs · integrations · error
handling · validation · database transactions.

Database — identify: main entities · relationships · constraints · unique fields · foreign keys ·
state fields · soft deletes · audit fields · important invariants.

Integrations — identify: external APIs · email · storage · payments · queues · third-party
services · webhooks · authentication providers.

Read the code paths, not just the file names. When the frontend calls an endpoint, open the
endpoint. When a rule is mentioned in a comment, find where it is enforced. Note where the UI
hides a control but the API does not enforce the restriction — that is a Gate 18 finding.

Deliverable: `qa-artifacts/repository-recon.md` — architecture diagram in text form, frontend
map, backend map, database map, integration map, authentication model, authorization model,
important business rules, high-risk areas, existing test coverage, missing coverage.

Exit criterion: you can explain the architecture and the major business flows in your own words,
citing where each is implemented.

---

## Gate 2 — Application feature inventory

Objective: an exhaustive inventory of user-visible and business-critical functionality.

For every feature record: feature name · related pages · user roles · API endpoints · database
entities · preconditions · happy path · negative paths · state transitions · dependencies · side
effects · expected result · risk level.

Classify Critical / High / Medium / Low by business impact, security impact, data integrity
impact, frequency of use, failure probability, complexity and dependency count — not by size.
A tiny "change role" endpoint can be Critical; a large settings page can be Low.

Deliverable: `qa-artifacts/feature-inventory.md`.

Exit criterion: every feature a user can reach has a row, and the Critical/High set is
defensible with a stated rationale.

---

## Gate 3 — Test strategy & traceability

Objective: a risk-based plan that says what is tested, how (UI vs API), and in what order.

Coverage must include:

Functional — happy paths · negative paths · boundary values · invalid input · missing input ·
null/empty values · duplicate data · incorrect data types · state transitions · multi-step
workflows · cross-feature workflows.

Authentication — login · logout · invalid credentials · session expiration · refresh behavior ·
unauthorized access · direct URL access · authentication persistence.

Authorization — every meaningful role/permission combination; verify UI restrictions, API
restrictions, direct endpoint access, object-level authorization, privilege escalation
possibilities. Hidden UI controls are not authorization — always check the API directly.

Validation — minimum · maximum · exactly minimum · exactly maximum · just below minimum · just
above maximum · required fields · invalid formats · unicode · special characters · long values ·
duplicate values.

State — initial · loading · empty · success · failure · partial · expired · deleted · disabled ·
already-completed.

Integration — the important flows across Browser → Frontend → API → Backend → Database →
External integration, plus direct API checks that isolate backend behavior.

Regression — every discovered bug becomes a regression candidate where appropriate.

Deliverables: `qa-artifacts/test-strategy.md` and `qa-artifacts/traceability-matrix.md`
(Feature → Requirement/Behavior → Test Case → Automation → Result).

Exit criterion: each Critical/High feature has a stated approach and priority, and the matrix
has a row for every behavior that will be tested.

---

## Gate 4 — Test case generation

Objective: comprehensive, risk-based scenarios — not one test per button.

For each important feature produce the core cases: happy path · alternative valid path · invalid
path · boundary path · permission path · state path · error path · recovery path · integration
path.

Then consider the edge cases: empty data · one record · many records · duplicate records · rapid
repeated actions · refresh during operation · back navigation · forward navigation · multiple
tabs · session expiration · network failure · delayed API · backend error · partial failure ·
race conditions · concurrent actions.

Every test case contains: ID · feature · priority · preconditions · test data · steps · expected
result · risk · automation strategy (UI, API or both).

Priorities: P0 catastrophic/critical workflow · P1 business-critical/high-risk · P2 important
normal functionality · P3 low-risk/secondary.

Deliverable: `qa-artifacts/test-cases.md`.

Exit criterion: P0/P1 cases exist for every Critical/High feature, negative and boundary cases
are present, and each case names its automation strategy.

---

## Gate 13 — Real execution

Objective: run the suite against the real system and collect evidence. Generating code is not
execution.

Phases, in order:

- Phase A — environment smoke (`--smoke`, ENV-* tests): browser starts, app reachable, API answers.
- Phase B — P0 (`--priority P0`).
- Phase C — P1 (`--priority P1`).
- Phase D — regression (`--regression`).
- Phase E — cross-feature flows (`--e2e`).
- Phase F — integration/API checks (`--integration`).

Stop and triage between phases when a phase surfaces blocking failures; a broken login makes
later phases noise.

Capture for every failure: test ID · feature · step · timestamp · URL · browser · exception ·
stack trace · screenshot · page source · logs · API evidence when relevant · duration · retry
behavior. The bundled runner writes these to `reports/<run-id>/artifacts/<test-id>/`.

If the environment cannot execute (no browser, app unreachable), report exactly that. Never
report an unexecuted test as passed; mark the work as blocked at Gate 13 with the reason.

Deliverable: `qa-artifacts/execution-report.md` (consolidated from the per-run reports).

Exit criterion: every selected test has an actual result and every FAIL/ERROR/FLAKY has evidence
on disk.

---

## Gate 15 — Regression intelligence

Objective: after fixing automation problems or application bugs, decide what to re-run.

Identify: directly affected features · dependent features · shared components · shared APIs ·
shared database entities · authentication dependencies · authorization dependencies.

Run targeted regression first (`--feature X`, `--test ID`), then full regression where risk
justifies it. Testing only the changed function is not sufficient when the function is shared.

Deliverable: `qa-artifacts/regression-report.md`.

---

## Gate 16 — PR / change impact analysis

Objective: when a Git diff or PR is available, prioritize tests by blast radius.

Analyze: changed files · changed functions · changed components · changed endpoints · database
migrations · business logic · shared utilities · authentication · authorization · UI flows.

Map: Changed code → affected component → affected feature → affected user journey → affected
tests → required regression.

Practical steps: `git diff --name-only <base>...<head>`, then for each changed file find its
importers (grep for the module/component name) and the routes that reach it, then look those
routes up in the traceability matrix.

Deliverable: the "blast radius" table in `qa-artifacts/regression-report.md`.

---

## Gate 17 — Quality review of the automation itself

Audit before declaring the suite ready.

Maintainability — duplication · naming · architecture · page objects · components.
Reliability — explicit waits · stable selectors · isolation · determinism · flakiness.
Coverage — critical workflows · negative cases · permissions · boundaries · state transitions ·
regression.
Diagnostics — screenshots · logs · stack traces · artifacts · clear classification.
Performance — identify unnecessarily expensive tests; prefer an integration test for isolated
backend behavior and an E2E test for cross-system behavior. Do not turn every small validation
into a full browser test.

Concrete checks: grep for `time.sleep`, absolute XPath (`/html/body`), generated class names,
duplicated locators across pages, tests that depend on records created by other tests, and
assertions that were softened after a failure.

---

## Gate 18 — Security-aware QA

Where appropriate test: unauthorized access · horizontal privilege escalation · vertical
privilege escalation · IDOR-style access (change an id in the URL/API and expect 403/404) ·
session invalidation after logout/password change · authentication bypass · input validation ·
dangerous parameter manipulation · file upload restrictions (type, size, content) · unexpected
data exposure in responses · sensitive information in error messages · client/server
authorization mismatch (UI hides, API allows).

Use the API client for these: a 200 from an endpoint the role should not reach is stronger
evidence than a missing button. Never run destructive attacks against production systems.

---

## Gate 19 — Accessibility-aware QA

Where applicable inspect: labels · buttons · keyboard navigation · focus management · forms ·
error messages · semantic controls · basic accessibility attributes (roles, names, aria-*).

Report findings as observations. Do not claim WCAG compliance unless an actual accessibility
audit has been performed.

---

## Gate 20 — Browser strategy

Default: Chromium/Chrome. Configurable: Firefox, Edge. Run critical regression across multiple
browsers when the project requires it (`python run_tests.py --browser firefox --priority P0`).

Support headless and headed (`--headless` / `--headed`). Headed runs are for investigating a
failure you cannot explain from artifacts; CI runs headless.

Record the browser and version used in every report — a "passes on Chrome" result is a browser
result, not an application-wide one.
