# Failure triage — Gate 14

Every FAIL, ERROR and FLAKY result must be classified from evidence. Do not guess: an
unexplained failure is neither an application bug nor an automation issue until it has been
investigated. The runner leaves every such result as `UNCLASSIFIED` on purpose — classification
is a judgment you make with the artifacts in front of you, and it is recorded in
`qa-artifacts/execution-report.md` (template: `assets/artifact-templates/execution-report.md`)
and, for confirmed bugs, `qa-artifacts/defects.md` (template: `assets/artifact-templates/defects.md`,
severity rubric in `reporting.md#severity-rubric`).

Worked example with real artifacts: `assets/examples/demo-app-engagement/qa-artifacts/execution-report.md`.

## Categories

```
REAL_APPLICATION_BUG
AUTOMATION_BUG
LOCATOR_FAILURE
SYNCHRONIZATION_FAILURE
TEST_DATA_FAILURE
AUTHENTICATION_FAILURE
AUTHORIZATION_FAILURE
ENVIRONMENT_FAILURE
NETWORK_FAILURE
INFRASTRUCTURE_FAILURE
DEPENDENCY_FAILURE
FLAKY_TEST
UNKNOWN
```

`UNKNOWN` is allowed only after the investigation below has been done and documented; it
means "investigated, not yet explained", never "did not look".

## What the runner gives you

For each attempt, under `reports/<run-id>/artifacts/<test-id>/`:

| File | Answers |
|---|---|
| `attemptN-exception.txt` | where it stopped (a `Waits` timeout names the state it waited for and the URL) |
| `attemptN-screenshot.png`, `attemptN-page_source.html`, `attemptN-url.txt` | what the user would have seen; is the element there under another attribute? |
| `attemptN-browser_console.json` | JS errors, failed fetches |
| `attemptN-network.json` | failed / non-2xx requests during the test (Chrome/Edge) |
| `attemptN-context.json` | browser version, build id, the last API exchange the test made |
| attachments from `ctx.attach(...)` | API evidence the test deliberately kept |
| `trace/` (with `--trace`) | a screenshot after every page action |

An ERROR whose exception is a `TimeoutException` from `core/waits.py` is *not automatically* a
SYNCHRONIZATION_FAILURE: the wait describes the state that never happened. Whether that is a
timing problem or the application never producing the state is what the rest of the evidence
decides.

## Bug vs automation — the decision process

1. Reproduce the failure (`--test <ID>`, `--headed` if needed).
2. Check the screenshot — what was on screen at the moment of failure?
3. Check the page source — is the element there under a different attribute? Is there an
   error banner the test did not expect?
4. Check the current URL and state — did a redirect, session expiry or modal intervene?
5. Check the browser console and `network.json` — JS errors, failed or 4xx/5xx requests.
6. Check API evidence — the attached exchange, or call the same endpoint with
   `integration/api_client.py`; what did the backend actually return?
7. Check application logs if available.
8. Repeat deterministically: `--test <ID> --repeat 5`. Same data, same steps — the runner reports
   the frequency (`failed 5/5 deterministically` vs `passed 2/5`).
9. Compare expected vs actual behavior against the verified implementation (Gate 1) and the
   oracle rule (SKILL.md): the code says what the app *does*, requirements say what it *should*
   do. If the expectation came from an assumption, the test may be the thing that is wrong.
10. Determine the root cause and classify.

Write the classification with the evidence that supports it. Two sentences that cite the
artifact beat a paragraph of speculation.

## REAL_APPLICATION_BUG criteria

Classify as a real bug when, with evidence: the application violates expected behavior · the
backend returns an incorrect result · the UI displays an incorrect state · a business rule is
violated · authorization is bypassed · data becomes inconsistent · a valid operation fails · an
invalid operation is incorrectly accepted · a regression is introduced.

Then write the defect report (format and severity rubric in `reporting.md`) and add a
regression test where appropriate.

## AUTOMATION_BUG criteria (and its sub-categories)

Classify as automation when: the locator is wrong (LOCATOR_FAILURE) · the page object is
incorrect · an assertion is incorrect · test data setup is wrong (TEST_DATA_FAILURE) · wait
logic is insufficient (SYNCHRONIZATION_FAILURE) · the test assumes incorrect application
behavior · cleanup corrupts the environment · the automation uses a brittle implementation.

Fix the automation, then re-run the test and its neighbors (same page object, same flow).
Record it in the execution report's "Automation defects" section — an automation bug you fixed
is still a finding about the suite's reliability.

## Environment, network, infrastructure, dependency

Use these when the failure is outside both the application and the suite: browser or driver
missing or mismatched (ENVIRONMENT_FAILURE), DNS/proxy/connection resets (NETWORK_FAILURE),
CI runner out of memory or disk (INFRASTRUCTURE_FAILURE), a third-party service down
(DEPENDENCY_FAILURE). The evidence is usually in `attemptN-exception.txt` and the run log. Fix
or report the environment; do not skip the test to make the run green.

A `TestTimeout` (the per-test watchdog fired) is an ERROR to triage like any other: a hung
page load, an alert nobody dismissed, or a genuinely stuck backend call.

## Flaky test policy — quantitative

Never convert `FAIL → RETRY → PASS` into `PASS`. Report it as:

```
Initial result: FAIL
Retry result:   PASS
Classification: FLAKY_TEST  (pending investigation)
```

The runner does this automatically with `--retries N`: the final status is FLAKY, every attempt
stays in the report, and the exit code stays non-zero. Retries are diagnostic — they answer
"is it deterministic?", not "can we ignore it?".

Before classifying, measure: `python run_tests.py --test <ID> --repeat 5`.

| Result of 5 runs | Classification |
|---|---|
| fails 5/5 with the same evidence | not flaky — go back to the decision process (bug or automation) |
| fails 1–4/5, exception is a wait timeout and a longer/better wait explains every failure | SYNCHRONIZATION_FAILURE — fix the wait, re-run 5× green |
| fails 1–4/5, backend evidence (network.json, API exchange, logs) shows the backend itself returned different results | REAL_APPLICATION_BUG (a race in the application) |
| fails 1–4/5, cause not yet found | FLAKY_TEST, with the frequency and the leading hypothesis recorded |

Record for every FLAKY_TEST: frequency (`n/5`) · root cause or hypothesis · timing · environment ·
selector stability · race conditions. A FLAKY_TEST entry without a frequency is not finished.

## Self-healing policy

Automation may repair itself when the problem is clearly automation-related.

Allowed: updating broken locators · improving waits · correcting page object mappings ·
improving test data isolation · fixing framework defects · correcting an assertion that
encoded a wrong assumption (say so in the report).

Forbidden: removing assertions · making expected results weaker · ignoring errors · accepting
unexpected UI · treating exceptions as success · skipping broken functionality · disabling tests
merely to obtain green CI.

The test is the reason a defect became visible. If the fix you are about to make would also
have hidden a real bug, it is not a fix.

## Evidence-first examples

Bad: "Login works."
Good: "Login passed for valid credentials on Chrome 151 headless. The dashboard URL loaded, the
authenticated user's name appeared in the navbar, and `GET /api/me` returned 200 with the same
user name (`artifacts/AUTH-001/me.json`)."

Bad: "This is probably a frontend bug."
Good: "`GET /api/items` after the create returned 200 with the new item (id 8,
`items-after-create.json`), but `attempt1-page_source.html` lists only ids 1, 2 and 7 and the
page had finished loading; 5/5 repeats fail identically (run 20260903-132400). Classification:
REAL_APPLICATION_BUG — BUG-001."

Bad: "Flaky, re-ran and it passed."
Good: "Failed 2 of 5 repeats at `waits.visible(TOAST)`; the toast is removed about 300 ms after
the API response and the wait started after navigation completed. Classification:
SYNCHRONIZATION_FAILURE — wait for the toast before the URL change; re-run 5× green."

Bad: "AUTH-003 fails, the app lets anonymous users into the dashboard."
Good: "AUTH-003 asserted `'/dashboard' not in current_url`; the URL at failure was
`/login?next=/dashboard` (`attempt1-url.txt`) — the redirect is correct and the assertion was
wrong. Classification: AUTOMATION_BUG — compare the path only; re-run PASS."
