# Benchmark — what has actually been run

Numbers below come from real runs on 2026-09-03 (Debian 13, Python 3.13.11, Selenium 4.31.1,
Chromium 151.0.7922.173 + chromedriver 151, Firefox 140.14 ESR + geckodriver 0.33). Re-run the
commands and update this file when the runner, the demo app or `SKILL.md` change.

## 1. Framework verification (mechanical, repeatable)

| Check | Command | Result |
|---|---|---|
| Runner self-test | `python assets/framework-skeleton/run_tests.py --selftest` | 40/40 |
| Lint / format / types | `ruff check . && ruff format --check . && mypy .` in the skeleton; ruff on `scripts/`, `evals/`, `assets/demo-app/` | clean |
| Full suite vs demo app, Chromium | `python scripts/run_demo.py --retries 1` | 14/14 PASS, exit 0, 10.7 s |
| Full suite, Firefox | `QA_BROWSER=firefox python scripts/run_demo.py` | 14/14 PASS |
| Parallel | `python scripts/run_demo.py --parallel 3` | 14/14 PASS, 4 modules on 3 workers |
| Injected defect, retries | `python scripts/run_demo.py --bugs stale-dashboard --retries 1` | 12 PASS, ITEM-001 + ITEM-002 ERROR on both attempts, exit 1 |
| Injected defect, rerun-failed | `--rerun-failed <run> --retries 1` | 2 selected, 2 ERROR (attempt 1 and 2), exit 1 |
| Injected defect, repeat | `--test ITEM-001 --repeat 5` | 0/5 passed → "failed 5/5 deterministically", exit 1 |
| Mobile emulation | `--test ENV-002 --test AUTH-001 --device "iPhone 12 Pro"` | 2/2 PASS |
| a11y + trace | `--test ITEM-001 --a11y --trace` | 1/1 PASS; axe 4.10.2: 2 moderate observations; 7 trace screenshots |
| Fresh scaffold | `scaffold_qa.py /tmp/target --with-artifacts` → `--list`, `--traceability`, `--selftest`, `qa_status.py` | 14 listed, matrix written, 40/40, "Resume at: Gate 0" |
| Worked example audit | `evals/check_engagement.py assets/examples/demo-app-engagement …` | 31/31 |
| CI | `.github/workflows/qa.yml` | self-test on 3.10 and 3.12, lint + mypy, Chrome and Firefox demo runs, parallel run, injected-defect must exit 1 |

## 2. Trigger evals (`evals/trigger-queries.json`)

Method: each query judged against the `description` in `SKILL.md` by the model reading it (not by a
live Claude Code session — do that too when you can and replace this table). ✓ = would load the skill.

| Should trigger | Judged | Should not trigger | Judged |
|---|---|---|---|
| QA this repo end to end and build a regression suite. | ✓ | Write unit tests for the parse_date helper. | ✗ (unit tests excluded) |
| Write Selenium tests for the admin dashboard… | ✓ | Add pytest tests for the API serializers. | ✗ (API-only) |
| These UI tests are red, app or tests? | ✓ | Load test the /search endpoint… | ✗ (load excluded) |
| Which tests does this PR affect? Run the regression… | ✓ | We use Playwright — add a test for the login page. | ✗ (Playwright excluded) |
| Build a browser test automation framework for our Django app… | ✓ | Write Cypress tests for the signup form. | ✗ (Cypress excluded) |
| Add E2E coverage for the checkout flow, we use Selenium already… | ✓ (extend-existing case) | Set up visual regression screenshots with Percy. | ✗ (visual regression excluded) |
| Can you test the web app in this repo and tell me what's broken? | ✓ | Review this PR for code quality. | ✗ |
| Our Selenium suite is flaky — investigate and fix… | ✓ | Pen-test our staging environment. | ✗ (penetration testing excluded) |
| اختبر الموقع ده كله واعمل regression suite بالسيلينيوم | ✓ (Arabic phrases) | Write tests for the Android app's login screen. | ✗ (native mobile excluded) |
| Set up UI test automation for the React frontend and the API… | ✓ | Explain how Selenium's explicit waits work. | ✗ (conceptual question excluded) |

Judged trigger rate: 10/10 should, 0/10 should-not. The three near-misses that motivated the last
description change (visual regression, pen-test, conceptual Selenium question) are now named in
the description's negative list.

## 3. Task evals (`evals/evals.json`) — with-skill vs baseline

Status: **harness ready, A/B not yet run.** The five prompts, their assertions and the checker exist;
running them needs interactive Claude Code sessions with and without the skill on a machine with a
browser. Record results here as:

| Eval | Assertion | Baseline | With skill |
|---|---|---|---|
| E1 full engagement | executed · smoke-first · no-sleep · no-abs-xpath · artifacts · p0-critical · authz-api · traceability · status-lines | — | — |
| E2 triage | reproduced · classified · not-flaky · defect-format · not-weakened · regression | — | — |
| E3 PR impact | resumed · blast-radius · targeted-run · conclusion | — | — |
| E4 existing suite | conflict-rule · evidence-hook · artifacts-still · stated | — | — |
| E5 blocked | honest-block · no-fake-pass · api-tests-ran | — | — |

What *has* been validated end to end is E1/E2's output shape: the worked example in
`assets/examples/demo-app-engagement/` was produced against the demo app with the injected defect
and passes all 31 mechanical assertions.

## 4. Validated on (stacks)

| Stack | Auth model | Size | Outcome |
|---|---|---|---|
| Flask, server-rendered Jinja, JSON API on the same origin (the bundled demo app) | cookie session | S | full engagement, one real defect found and reported (BUG-001) |
| SPA + separate API | token / refresh | — | **wanted** — send a field report |
| Server-rendered app with roles (Django / Rails / Laravel) | session + CSRF | M | **wanted** — send a field report |

Known limitations from these runs are listed in `README.md` → Known limitations.
