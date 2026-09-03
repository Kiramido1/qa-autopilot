# qa-autopilot — `selenium-qa-automation`

[![qa](https://github.com/Kiramido1/qa-autopilot/actions/workflows/qa.yml/badge.svg)](https://github.com/Kiramido1/qa-autopilot/actions/workflows/qa.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Selenium 4.20+](https://img.shields.io/badge/selenium-4.20%2B-43B02A)
![Skill v1.0.0](https://img.shields.io/badge/skill-v1.0.0-6f42c1)

An [Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) that turns Claude into
a senior QA automation engineer for web applications: repository reconnaissance → risk-based test
design → Python + Selenium Page Object framework → **real execution** → evidence-based failure triage
→ regression. It ships with a pytest-free runner that cannot report a retried failure as a pass, a
demo app the whole thing is verified against in CI, and a complete worked engagement with real run output.

The skill exists because "generate some Selenium tests" is not QA. The agent has to understand the
application first, test business behavior instead of buttons, run the tests for real, and explain
every failure with evidence — separating real application bugs from locator, synchronization, data
and environment problems — before it reports anything.

## Contents

- [Quick start](#quick-start)
- [What the agent does](#what-the-agent-does)
- [What's in the repo](#whats-in-the-repo)
- [The bundled framework](#the-bundled-framework)
- [Validated on](#validated-on)
- [Known limitations](#known-limitations)
- [Evals and benchmark](#evals-and-benchmark)
- [Contributing](#contributing) · [License](#license)

## Quick start

**Install the skill (Claude Code)** — personal, for all projects:

```bash
git clone https://github.com/Kiramido1/qa-autopilot.git ~/.claude/skills/selenium-qa-automation
```

or per project: `git clone https://github.com/Kiramido1/qa-autopilot.git .claude/skills/selenium-qa-automation`.
Claude Code loads `~/.claude/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md`
([docs](https://code.claude.com/docs/en/skills)). For Claude.ai / Desktop, zip the folder and upload it as a
custom skill; for the API, upload it through the Skills API.

**See it work in two minutes** (no repository needed — the bundled demo app):

```bash
pip install -r assets/framework-skeleton/requirements.txt -r assets/demo-app/requirements.txt
python assets/framework-skeleton/run_tests.py --selftest        # the runner proves itself: 41 checks, no browser
python scripts/run_demo.py                                       # 14 tests against the demo app → 14 pass
python scripts/run_demo.py --bugs stale-dashboard --retries 1    # injected defect → ITEM-001/002 ERROR, exit 1
python evals/check_engagement.py assets/examples/demo-app-engagement \
   --qa assets/framework-skeleton --reports assets/examples/demo-app-engagement/runs --run 20260903-132200
```

**Then point Claude at a repository:** "QA this repo end to end and build a regression suite", "these
UI tests are red — app or tests?", "which tests does this PR affect?", "extend our Selenium suite
with the checkout flow". The agent works through the gates below, writes `qa-artifacts/` and `qa/`
into the repository, and posts a five-line status after each gate.

## What the agent does

| Gate | What happens | Output |
|---|---|---|
| **first 15 min** | resume check (`scripts/qa_status.py`), start the app, scaffold, `--selftest`, `--smoke`, size the repo (S/M/L), pick a depth mode | one status line |
| 0 | Environment & scope discovery — exit criterion is literal: the ENV-* smoke tests **executed** | `qa-artifacts/environment-map.md` |
| 1 | Repository reconnaissance, sampled by risk (routes → auth → money/deletes → the rest); unread areas listed | `repository-recon.md` |
| 2 | Feature inventory ranked by impact, security, data integrity, frequency, failure probability — not size | `feature-inventory.md` |
| 3 | Risk-based strategy; vertical slice named; traceability is **generated** by the runner | `test-strategy.md`, `traceability-matrix.md` |
| 4 | Test cases with the oracle rule (implementation = what it does, requirements = what it should do, else "assumed expected — needs product confirmation") and ids shared with code | `test-cases.md` |
| 5–12 | Framework: page objects, components, locator priority, named waits, isolated data with cleanup, hooks, session reuse, API checks; vertical slice first | `qa/` |
| 13 | Real execution in phases A–F; blocked-at-Gate-13 is a legal outcome, a fake PASS is not | per-run reports → `execution-report.md` |
| 14 | Every FAIL/ERROR/FLAKY classified from evidence; flakiness **measured** with `--repeat 5`; severity by rubric | `defects.md` |
| 15–16 | Regression by blast radius; PR / diff impact analysis | `regression-report.md` |
| 17–20 | Audit of the suite (mechanical checks in `evals/check_engagement.py`), security-aware and accessibility-aware checks, browser strategy | findings in the reports |
| 21 | Coverage model (never "number of tests"), honest gaps, change safety | `coverage-gaps.md` |

Proportionality is built in: an S-sized repo compresses Gates 1–4 into one pass, an L-sized one is
phased per feature area, effort caps stop reconnaissance from eating the engagement, and the user
can ask for a **quick pass**, **standard** or **deep** run. Multi-session work resumes from the
first unfinished gate instead of regenerating artifacts.

The non-negotiable rules — no pytest, no arbitrary sleeps, no absolute XPath, no weakened
assertions, no retry-to-green, no PASS without execution, no business rule invented to have
something to assert — are in [`SKILL.md`](SKILL.md), each with the reason it exists.

## What's in the repo

```
qa-autopilot/
├── SKILL.md                         entry point: first 15 minutes, sizing, resume protocol, rules, gates, quality gate
├── references/
│   ├── gates.md                     gates 0–4, 13, 15–20: checklists, exit criteria, proportionality
│   ├── automation-framework.md      gates 5–12 + extending an existing suite (conflict rule)
│   ├── failure-triage.md            gate 14: categories, decision process, quantitative flaky policy
│   └── reporting.md                 gate 21: artifact set, traceability, severity rubric, defect format, communication contract
├── assets/
│   ├── artifact-templates/          one template per qa-artifacts/ file, each with an EXAMPLE row
│   ├── framework-skeleton/          the Python + Selenium framework and runner (see below)
│   ├── demo-app/                    ~260-line Flask app with data-testid attributes and injectable defects
│   └── examples/demo-app-engagement/  all ten artifacts filled + the runner's real output for seven runs
├── scripts/
│   ├── scaffold_qa.py               installs the skeleton (+ templates) into a repo, never overwrites
│   ├── qa_status.py                 resume helper: which artifacts are finished, which gate is next
│   └── run_demo.py                  starts the demo app, runs the skeleton against it, stops it
├── evals/                           task evals, trigger evals, check_engagement.py (objective assertions)
├── docs/walkthrough.md              an annotated real run: injected defect → evidence → classification
├── .github/workflows/qa.yml         self-test, lint + mypy, Chrome and Firefox runs against the demo app
├── benchmark.md · CHANGELOG.md · CONTRIBUTING.md · LICENSE
```

## The bundled framework

`assets/framework-skeleton/` is installed into a repository with `python scripts/scaffold_qa.py <repo> --with-artifacts`.

```
qa/
├── run_tests.py      selection: --smoke/--regression/--e2e/--integration, --tag, --feature, --priority, --test, --rerun-failed
│                     environment: --env, --browser, --headed/--headless, --remote-url (Grid/BrowserStack/Sauce), --device (mobile emulation)
│                     execution: --retries (→ FLAKY, never PASS), --repeat N (frequency), --timeout (watchdog), --parallel N,
│                     --fail-fast, --fresh-session, --a11y (axe-core observations), --trace (screenshot per action)
│                     tools: --selftest (40 runner checks, no browser), --traceability, --list
├── core/             engine · driver (implicit wait 0) · named waits · base_page · assertions (expected vs actual) ·
│                     artifacts (screenshot, page source, URL, console, failed network requests, API exchange, traceback) ·
│                     registry (@test) · context (ctx) · session (login_once) · redact · junit · traceability · a11y · trace · parallel
├── components/       table · modal · dropdown · pagination · file_uploader · toast
├── pages/ flows/     Page Objects and journeys (EXAMPLEs run green against the demo app)
├── integration/      api_client.py — requests with redacted evidence
├── data/             factories.py (unique + boundary data) · fixtures.py
└── tests/            smoke/ regression/ e2e/ integration/ · session_hooks.py (setup_session / setup_module hooks)
```

Every run writes `reports/<run-id>/` with `execution-report.md`, `report.json`, `junit.xml`, `run.log`
and per-failure evidence, all paths relative to the run directory so CI uploads stay valid. Run
metadata records browser and driver versions and the application's git SHA/branch. Exit codes:
`0` all passed · `1` any FAIL/ERROR/FLAKY or hook failure · `2` configuration error · `3` nothing selected.

```python
from core.assertions import assert_equal, assert_in
from core.registry import test
from flows.authentication import login

@test(id="AUTH-001", feature="authentication", priority="P0", tags=("smoke", "regression"))
def test_login_with_valid_credentials(ctx):
    creds = ctx.require_credentials("test_user")
    dashboard = login(ctx.driver, ctx.settings, creds.email, creds.password)
    assert_in("/dashboard", ctx.driver.current_url, "did not reach the dashboard")
    ctx.api.set_cookies_from_driver(ctx.driver)
    me = ctx.api.get("/api/me")
    ctx.attach("me.json", ctx.api.last_exchange())          # redacted API evidence next to the result
    assert_equal(dashboard.user_name(), me.json()["name"], "UI identity differs from the backend identity")
```

Requirements: Python 3.10+, `selenium>=4.20`, `requests>=2.31`; Chrome, Firefox or Edge (Selenium
Manager downloads drivers, or set `QA_CHROMEDRIVER_PATH` / `QA_GECKODRIVER_PATH` offline); the
application reachable from the machine that runs the tests. Windows notes are in the skeleton README.

## Validated on

| What | Where | Result |
|---|---|---|
| Runner self-test (statuses, exit codes, cleanup, hooks, watchdog, repeat, rerun-failed, relative paths, redaction, JUnit, parallel, duplicate ids, traceability, cookie sanitization) | local, Python 3.13.11; CI 3.10 / 3.12 | 41/41 |
| Full suite against the demo app | Chromium 151 + chromedriver 151, Debian 13 | 14/14, 10.7 s |
| Full suite, Firefox | Firefox 140.14 ESR + geckodriver 0.33 | 14/14 |
| `--parallel 3` | Chromium 151 | 14/14 |
| Injected defect `stale-dashboard` (`--retries 1`, `--rerun-failed`, `--repeat 5`) | Chromium 151 | ITEM-001/002 ERROR on every attempt, 0/5 — exit 1, not FLAKY |
| Mobile emulation (`--device "iPhone 12 Pro"`), `--a11y` + `--trace` | Chromium 151 | 2/2, 1/1 with 2 moderate axe observations |
| `ruff check`, `ruff format --check`, `mypy` on the skeleton | ruff 0.16, mypy 2.3 | clean |
| `evals/check_engagement.py` on the worked example | — | 31/31 |
| GitHub Actions: self-test (3.10, 3.12), lint + mypy, demo app on Chrome and Firefox, parallel run, injected-defect detection | ubuntu-latest | see badge |

Stacks the skill has been run against: a server-rendered Flask app with cookie sessions (the demo).
Field reports for SPAs with a separate API and for other auth models are wanted — see
`.github/ISSUE_TEMPLATE/field_report.md` and [`benchmark.md`](benchmark.md).

## Known limitations

- **Real execution needs a real machine.** Gate 13 requires the app running and a browser installed
  (Claude Code on a workstation or a CI runner). Without them the skill stops at Gate 13 and says so.
- **Selenium Manager may be missing** in distro-packaged Selenium (Debian): set `QA_CHROMEDRIVER_PATH`
  and `QA_CHROME_BINARY`. A newer Chrome than the packaged chromedriver will not work either.
- Browser console and network evidence come from Chrome/Edge; Firefox runs record exception, screenshot, page source and URL.
- `--parallel` is per module and shares the application instance; it is for suites already green sequentially.
- `--a11y` downloads axe-core once (or uses `QA_AXE_PATH`); findings are observations, never compliance.
- The traceability generator parses `test-cases.md` and `execution-report.md` by convention (`test id in code:`,
  a block naming a test id and a category); other layouts need the matrix written by hand.

## Evals and benchmark

`evals/evals.json` holds five task evals with objective assertions (executed, evidenced, classified,
traced, not weakened), `evals/trigger-queries.json` ten should-trigger and ten near-miss queries, and
`evals/check_engagement.py` the mechanical checks — also used at Gate 17. What has actually been run,
with numbers, is in [`benchmark.md`](benchmark.md).

## Contributing

Issues and pull requests are welcome — field reports from real engagements most of all. Read
[`CONTRIBUTING.md`](CONTRIBUTING.md); the non-negotiable rules are the product, and every framework
change runs green against the demo app before it merges.

## License

MIT — see [LICENSE](LICENSE).
