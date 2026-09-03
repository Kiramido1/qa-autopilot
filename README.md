# selenium-qa-automation

An [Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) that turns Claude into a
senior QA automation engineer for web applications: repository reconnaissance → risk-based
test design → Python + Selenium Page Object framework → real execution → evidence-based
failure triage → regression. It ships with a working, pytest-free test runner and templates
for every QA artifact it produces.

The skill exists because "generate some Selenium tests" is not QA. This skill makes the agent
understand the application first, test business behavior instead of buttons, run the tests
for real, and explain every failure with evidence — separating real application bugs from
locator, synchronization, data and environment problems — before it reports anything.

## What's in the repo

```
selenium-qa-automation/
├── SKILL.md                       skill entry point: rules, gated workflow, final quality gate
├── references/
│   ├── gates.md                   detailed checklists for gates 0–4, 13, 15–20
│   ├── automation-framework.md    gates 5–12: architecture, page objects, locators, waits, data, runner
│   ├── failure-triage.md          gate 14: categories, bug-vs-automation process, flaky/self-healing policy
│   └── reporting.md               gate 21: artifact set, defect format, coverage model, change safety
├── assets/
│   ├── artifact-templates/        one Markdown template per qa-artifacts/ deliverable (10 files)
│   └── framework-skeleton/        the Python + Selenium framework with the custom runner
├── scripts/
│   └── scaffold_qa.py             copies the skeleton (+ templates) into a target repo, never overwrites
├── README.md · LICENSE · .gitignore
```

## Installation

**Claude Code** — personal skill (all projects):

```bash
git clone https://github.com/<you>/selenium-qa-automation.git ~/.claude/skills/selenium-qa-automation
```

or project skill (this repo only):

```bash
git clone https://github.com/<you>/selenium-qa-automation.git .claude/skills/selenium-qa-automation
```

Claude Code loads skills from `~/.claude/skills/<name>/SKILL.md` (personal) and
`.claude/skills/<name>/SKILL.md` (project). See the
[Claude Code skills documentation](https://code.claude.com/docs/en/skills).

**Claude.ai / Claude Desktop (Cowork)** — zip the repository folder and upload it as a custom
skill in your Claude settings, or use the `.skill` file from the
[Releases](../../releases) page if one is published. Custom skills require a paid plan; see the
[Claude help center](https://support.claude.com).

**Claude API** — upload the folder through the Skills API and reference its `skill_id` with the
code execution tool. See the
[Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

## Usage

Point Claude at a repository and ask for QA. The description in `SKILL.md` triggers on
requests like:

- "QA this repo end to end and build a regression suite."
- "Write Selenium tests for the admin dashboard — login, user management, exports."
- "These UI tests are red, figure out whether it's the app or the tests."
- "Which tests does this PR affect? Run the regression that matters."

The agent then works through the gates below, writing a `qa-artifacts/` folder and a `qa/`
test suite into the repository, and reports with evidence.

Real execution (Gate 13) needs a machine where the application runs and a browser is installed
— typically Claude Code on your workstation or a CI runner. In an environment without a
browser or without access to the app's backend, the skill stops at Gate 13 and says so rather
than reporting results it does not have.

## The gates

| Gate | What happens | Output |
|---|---|---|
| 0 | Environment & scope discovery — find out how to launch and reach the app, then do it | `qa-artifacts/environment-map.md` |
| 1 | Repository reconnaissance — frontend, backend, database, integrations, auth model, business rules verified in code | `qa-artifacts/repository-recon.md` |
| 2 | Feature inventory ranked by impact, security, data integrity, frequency, failure probability, complexity | `qa-artifacts/feature-inventory.md` |
| 3 | Risk-based test strategy and traceability matrix | `qa-artifacts/test-strategy.md`, `traceability-matrix.md` |
| 4 | Test cases (P0–P3): happy, alternative, invalid, boundary, permission, state, error, recovery, integration + edge cases | `qa-artifacts/test-cases.md` |
| 5–12 | Framework: architecture, page objects & components, locator priority, explicit waits, isolated data, custom runner, incremental implementation, API integration checks | `qa/` |
| 13 | Real execution in phases: environment smoke → P0 → P1 → regression → cross-feature → integration | per-run reports, `qa-artifacts/execution-report.md` |
| 14 | Failure intelligence: every FAIL/ERROR/FLAKY classified from evidence (`REAL_APPLICATION_BUG`, `AUTOMATION_BUG`, `LOCATOR_FAILURE`, `SYNCHRONIZATION_FAILURE`, `TEST_DATA_FAILURE`, …) | `qa-artifacts/defects.md` |
| 15–16 | Regression intelligence and PR/change blast-radius analysis | `qa-artifacts/regression-report.md` |
| 17–20 | Audit of the automation itself; security-aware and accessibility-aware checks; browser strategy | findings in the reports |
| 21 | Reporting, coverage model (never "number of tests"), change safety | `qa-artifacts/coverage-gaps.md` |

The full rule set — no pytest, no arbitrary sleeps, no absolute XPath, no weakened
assertions, no retry-to-green, no PASS without execution — is in `SKILL.md`.

## The bundled framework

`assets/framework-skeleton/` is a complete starting point, installed into a repo with:

```bash
python scripts/scaffold_qa.py /path/to/repo --with-artifacts
cd /path/to/repo/qa
pip install -r requirements.txt
cp .env.example .env            # URLs and disposable test accounts; never committed
python run_tests.py --list
python run_tests.py --smoke
```

```
qa/
├── run_tests.py      custom runner: discovery, --smoke/--regression/--e2e/--integration,
│                     --feature, --priority, --test, --browser, --headed/--headless, --retries
├── config/           settings.py (CLI > env vars > .env > environments.py) · environments.py
├── core/             driver (implicit wait 0) · waits (named explicit waits) · base_page ·
│                     assertions (expected vs actual) · artifacts · registry · context · logger
├── pages/ components/ flows/      Page Object Model, examples marked EXAMPLE
├── integration/      api_client.py — requests with redacted evidence
├── data/             factories.py (unique + boundary data) · fixtures.py
└── tests/            smoke/ regression/ e2e/ integration/
```

Every run writes `reports/<run-id>/` with `execution-report.md`, `report.json`, `run.log` and,
for each failure, screenshot + page source + URL + browser console + traceback + context.
Exit codes: `0` all passed · `1` any FAIL/ERROR/FLAKY · `2` configuration error · `3` nothing
selected. A test that fails and then passes on a diagnostic retry is reported as **FLAKY**,
never as PASS.

Tests are plain functions:

```python
from core.assertions import assert_in
from core.registry import test
from pages.login_page import LoginPage

@test(id="AUTH-002", feature="authentication", priority="P1", tags=("regression", "negative"))
def test_login_with_invalid_password_shows_error(ctx):
    page = LoginPage(ctx.driver, ctx.settings).open()
    page.login("nobody@example.test", "wrong")
    assert_in("/login", ctx.driver.current_url, "left the login page with bad credentials")
```

## Requirements

- Python 3.9+ (the skeleton uses only `selenium>=4.20` and `requests>=2.31`)
- Chrome, Firefox or Edge on the machine that runs the tests; Selenium Manager downloads the
  matching driver, or set `QA_CHROMEDRIVER_PATH` / `QA_GECKODRIVER_PATH` for offline CI
- The application under test running locally or reachable from that machine

## Contributing

Issues and pull requests are welcome — especially real-world adaptations of the framework
skeleton (components for common UI libraries, additional wait conditions, CI examples). Keep
the non-negotiable rules intact: they are what make the skill's results trustworthy.

## License

MIT — see [LICENSE](LICENSE).
