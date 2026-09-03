# Gate details — discovery, design, execution, regression, audits

Companion to SKILL.md. Read the section for the gate you are entering; each ends with the exit
criterion that must be true before moving on and names the template it feeds. Gates 5–12
(framework build) are in `automation-framework.md`, Gate 14 (triage) in `failure-triage.md`,
Gate 21 (reports) in `reporting.md`. A complete filled artifact set from a real run is in
`assets/examples/demo-app-engagement/qa-artifacts/`.

Contents
- [Proportionality: sizing, sampling, effort caps](#proportionality-sizing-sampling-effort-caps)
- [Gate 0 — Environment & scope discovery](#gate-0--environment--scope-discovery)
- [Gate 1 — Repository reconnaissance](#gate-1--repository-reconnaissance)
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

## Proportionality: sizing, sampling, effort caps

Size the repository in the first 15 minutes and say it in the Gate 0 status line:

| Size | Signal | What changes |
|---|---|---|
| S | ≤ ~15 routes, ≤ 3 entities, ≤ 2 roles | Gates 1–4 in one pass; one document with the four headings is fine; full suite after the vertical slice |
| M | ≤ ~60 routes, ≤ 10 entities, ≤ 4 roles | Full artifacts for Critical/High features before the first execution; Medium/Low after the vertical slice is green |
| L | more, or several deployables | One feature area at a time through Gate 13; report; next area. Never "recon everything first" |

Sampling order for Gate 1: entry points and routes → authentication and authorization → money,
deletion, state machines, uploads → shared services and middleware → the rest as time allows.
Everything not read goes in `coverage-gaps.md` under "Unread code" — a listed gap is a finding,
an unlisted one is a lie of omission.

Effort caps (share of the engagement): recon ≤ 20%, design ≤ 20%. When exceeded, write what is
known plus the gap and move on to the vertical slice; the first real execution teaches more than
another hour of reading.

Depth modes: **quick pass** (Gate 0, sampled recon, P0 only, one execution, triage, short report) ·
**standard** (default; every gate, P0–P1 automated) · **deep** (everything, edge-case checklist per
feature, multi-browser, `--a11y`, Gate 18 on every role × object).

---

## Gate 0 — Environment & scope discovery

Objective: launch and reach the application before anything else — and prove it by executing.

Identify: operating system · Python version · browsers and versions · Selenium version · app
startup procedure · required environment variables (names, never values) · required services ·
database · API · authentication · test accounts · seed data · Docker/compose · CI/CD · existing
test infrastructure and automation · build/install commands.

Inspect: README · Makefile · package/requirements files · pyproject · Dockerfiles · compose files ·
CI configuration · env examples · scripts · test directories · deployment files.

Then start the application and hit it. Scaffold the framework, fill `qa/.env`, and run:

```bash
python run_tests.py --selftest     # the runner proves itself (no browser)
python run_tests.py --smoke        # ENV-001 settings · ENV-002 browser reaches the app · ENV-003 API health
```

If the machine has no browser or the app is unreachable, this is where you find out — and where
you stop and say so, instead of designing tests for a system you cannot run.

Deliverable: `qa-artifacts/environment-map.md` (template `assets/artifact-templates/environment-map.md`).

Exit criterion (literal): **the ENV-* smoke tests have executed** and their run id is cited in the
environment map. "The README says `npm start`" is not an exit.

---

## Gate 1 — Repository reconnaissance

Objective: understand the real architecture and behavior from the implementation, sampled by risk.

Frontend — framework · routing · pages · components · forms · modals · tables · filters · search ·
pagination · uploads · downloads · auth UI · role-based UI · loading/empty/error states · toasts ·
navigation · responsive behavior · client-side validation · API clients · state management.

Backend — routes · methods · request/response schemas · authentication · authorization · middleware ·
services · repositories · background jobs · integrations · error handling · validation · transactions.

Database — entities · relationships · constraints · unique fields · foreign keys · state fields ·
soft deletes · audit fields · invariants.

Integrations — external APIs · email · storage · payments · queues · webhooks · auth providers.

Read the code paths, not the file names. When the frontend calls an endpoint, open the endpoint.
When a comment mentions a rule, find where it is enforced and cite `file:line`. Where the UI hides
a control but the API does not enforce the restriction, that is a Gate 18 finding. Apply the
oracle rule: the code tells you what the app *does*; note separately what docs/requirements say
it *should* do, and mark disagreements as candidate defects.

Deliverable: `qa-artifacts/repository-recon.md` (template `assets/artifact-templates/repository-recon.md`).

Exit criterion: you can explain the architecture and the major business flows in your own words,
citing where each is implemented, and the unread areas are listed.

---

## Gate 2 — Application feature inventory

Objective: an inventory of user-visible and business-critical functionality, risk-ranked.

For every feature: name · pages · roles · endpoints · entities · preconditions · happy path ·
negative paths · state transitions · dependencies · side effects · risk level.

Rank Critical / High / Medium / Low by business impact, security impact, data integrity, frequency
of use, failure probability, complexity and dependency count — not by size. A four-line ownership
check can be Critical; a large settings page can be Low. Write the rationale for every Critical/High.

Deliverable: `qa-artifacts/feature-inventory.md` (template `assets/artifact-templates/feature-inventory.md`).

Exit criterion: every reachable feature has a row and the Critical/High set has a stated rationale.

---

## Gate 3 — Test strategy & traceability

Objective: a risk-based plan that says what is tested, how (UI vs API), in what order, and what is
deliberately not automated.

Coverage areas — Functional: happy · negative · boundary · invalid · missing · null/empty · duplicate ·
wrong types · state transitions · multi-step · cross-feature. Authentication: login · logout ·
invalid credentials · expiry · refresh · unauthorized access · direct URL · persistence.
Authorization: every meaningful role × permission, UI *and* API, object-level, escalation — hidden
UI controls are not authorization. Validation: min · max · exactly · just outside · required ·
formats · unicode · special characters · long · duplicates. State: initial · loading · empty ·
success · failure · partial · expired · deleted · disabled · completed. Integration: browser →
frontend → API → backend → DB → external, plus direct API checks. Regression: every bug becomes a
regression candidate.

Name the vertical slice (one P0 journey) that will be built and executed first.

Traceability is **generated**, not maintained: `python run_tests.py --traceability` builds the
matrix from `test-cases.md`, the `@test` registry and the latest `report.json`. At Gate 3 it lists
the planned cases as "not automated"; after each run it carries results and classifications.

Deliverables: `qa-artifacts/test-strategy.md` (template `assets/artifact-templates/test-strategy.md`)
and `qa-artifacts/traceability-matrix.md` (generated; format in `reporting.md#traceability`).

Exit criterion: each Critical/High feature has an approach and priority, the vertical slice is
named, and the matrix has a row for every behavior that will be tested.

---

## Gate 4 — Test case generation

Objective: risk-based scenarios, not one test per button.

Per important feature, the core cases: happy · alternative valid · invalid · boundary · permission ·
state · error · recovery · integration. Then the edge cases: empty · one · many · duplicate · rapid
repeats · refresh mid-operation · back · forward · multiple tabs · session expiry · network failure ·
delayed API · backend error · partial failure · races · concurrency.

Every case: `TC-<AREA>-<n>` · feature · priority · preconditions · test data · steps · expected result
**with its source** (verified implementation `file:line`, a requirement, or "assumed expected — needs
product confirmation", which makes it a characterization test) · risk · automation strategy (UI, API,
both, manual) · `test id in code: \`AREA-nnn\`` — the same id used in `@test(id=...)`. The
traceability generator parses that line.

Priorities: P0 catastrophic/critical workflow · P1 business-critical/high-risk · P2 important
normal · P3 low-risk/secondary.

Deliverable: `qa-artifacts/test-cases.md` (template `assets/artifact-templates/test-cases.md`).

Exit criterion: P0/P1 cases exist for every Critical/High feature, negative and boundary cases are
present, every expected result names its source, and each case names its automation strategy.

---

## Gate 13 — Real execution

Objective: run the suite against the real system and collect evidence. Generating code is not execution.

Phases, in order — stop and triage between phases when a phase surfaces blocking failures (a broken
login makes later phases noise):

- A — environment smoke: `--smoke` (ENV-*).
- B — P0: `--priority P0`.
- C — P1: `--priority P1`.
- D — regression: `--regression`.
- E — cross-feature flows: `--e2e`.
- F — integration/API: `--integration`.

For an S-sized app one run of everything is acceptable — the runner orders P0 first anyway; record
which tests belong to which phase in the execution report.

Useful during execution: `--fail-fast` in phase B, `--rerun-failed <run-id> --retries 1` to check
determinism, `--test <ID> --repeat 5` before any flaky claim, `--headed` and `--trace` for a failure
the artifacts cannot explain, `--parallel N` only once the suite is green sequentially.

The runner captures per failure: exception + traceback · screenshot · page source · URL · browser
console · failed/non-2xx network requests · the last API exchange · duration · every attempt, under
`reports/<run-id>/artifacts/<test-id>/`, plus `report.json`, `junit.xml` and `execution-report.md`.
Run metadata records browser/driver versions and the app's git SHA/branch (`QA_APP_REPO`,
`QA_BUILD_ID`) — a result without a build identifier is not reproducible.

If the environment cannot execute (no browser, app unreachable), report exactly that with the error
text and evidence path: **blocked at Gate 13**. Never report an unexecuted test as passed.

Deliverable: `qa-artifacts/execution-report.md` (template `assets/artifact-templates/execution-report.md`),
consolidated from the per-run reports; then `python run_tests.py --traceability`.

Exit criterion: every selected test has an actual result and every FAIL/ERROR/FLAKY has evidence on disk.

---

## Gate 15 — Regression intelligence

Objective: after fixing automation problems or application bugs, decide what to re-run.

Identify: directly affected features · dependent features · shared components · shared APIs ·
shared entities · authentication and authorization dependencies.

Run targeted regression first (`--feature X`, `--test ID`, `--rerun-failed`), then full regression
where risk justifies it. Testing only the changed function is not sufficient when the function is
shared. Regenerate the traceability matrix afterwards.

Deliverable: `qa-artifacts/regression-report.md` (template `assets/artifact-templates/regression-report.md`).

---

## Gate 16 — PR / change impact analysis

Objective: with a diff or PR, prioritize tests by blast radius.

Analyze: changed files · functions · components · endpoints · migrations · business logic · shared
utilities · authentication · authorization · UI flows.

Map: changed code → affected component → affected feature → affected journey → affected tests →
required regression.

Practical steps: `git diff --name-only <base>...<head>`; for each changed file grep for its
importers and the routes that reach it; look those routes up in the traceability matrix; run that
set, then decide on full regression.

Deliverable: the blast-radius table in `qa-artifacts/regression-report.md`.

---

## Gate 17 — Quality review of the automation itself

Audit before declaring the suite ready — a suite that lies quietly is worse than no suite.

Maintainability — duplication · naming · architecture · page objects · components.
Reliability — explicit waits · stable selectors · isolation · determinism · measured flakiness.
Coverage — critical workflows · negative · permissions · boundaries · state transitions · regression.
Diagnostics — screenshots · logs · stack traces · artifacts · clear classification.
Cost — integration test for isolated backend behavior, E2E for cross-system behavior; no small
validation as a full browser test.

Concrete checks (`evals/check_engagement.py` runs the mechanical ones):

```bash
grep -rn "time.sleep" qa/ --include=*.py            # must be empty outside core/ helpers with a documented reason
grep -rn "/html/body" qa/ --include=*.py            # absolute XPath: none
grep -rn "css-[a-z0-9]\{5,\}\|sc-[a-zA-Z]" qa/       # generated class names: none
python run_tests.py --selftest                       # runner still honest
```

Also look for locators duplicated across pages, tests that depend on records another test created,
and assertions softened after a failure (`git log -p qa/tests` tells that story).

---

## Gate 18 — Security-aware QA

Where appropriate test: unauthorized access · horizontal privilege escalation · vertical privilege
escalation · IDOR (change an id in the URL/API, expect 403/404 and an unchanged record) · session
invalidation after logout / password change · authentication bypass · input validation · dangerous
parameter manipulation · file upload restrictions (type, size, content) · unexpected data exposure
in responses · sensitive information in error messages · client/server authorization mismatch (UI
hides, API allows) · unauthenticated maintenance/test endpoints left enabled.

Use the API client: a 200 from an endpoint the role should not reach is stronger evidence than a
missing button. Never run destructive attacks against production systems. This is not a
penetration test; say so in the report.

---

## Gate 19 — Accessibility-aware QA

Inspect where applicable: labels · buttons · keyboard navigation · focus management · forms · error
messages · semantic controls · roles, names, `aria-*`. `--a11y` injects axe-core after each browser
test and records violations as observations next to the result.

Report findings as observations. Do not claim WCAG compliance unless an actual accessibility audit
has been performed.

---

## Gate 20 — Browser strategy

Default Chrome/Chromium; Firefox and Edge configurable (`--browser`); Selenium Grid / cloud via
`--remote-url`; Chrome mobile emulation via `--device` for responsive checks. Run the P0 set on a
second browser when the project supports it: `python run_tests.py --browser firefox --priority P0`.

Headless in CI; headed (`--headed`) only to investigate a failure the artifacts cannot explain.
Record browser and driver versions in every report (the runner does) — a pass on Chrome is a Chrome
result, not an application-wide one.
