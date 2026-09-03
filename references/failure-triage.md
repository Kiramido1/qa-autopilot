# Failure triage — Gate 14

Every FAIL, ERROR and FLAKY result must be classified from evidence. Do not guess: an
unexplained failure is neither an application bug nor an automation issue until it has been
investigated. The runner leaves every such result as `UNCLASSIFIED` on purpose — classification
is a judgment you make with the artifacts in front of you, and it is recorded in
`qa-artifacts/execution-report.md` and, for confirmed bugs, `qa-artifacts/defects.md`.

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

## Bug vs automation — the decision process

1. Reproduce the failure (re-run the single test: `--test <ID>`, headed if needed).
2. Check the screenshot — what was on screen at the moment of failure?
3. Check the page source — is the element there under a different attribute? Is there an
   error banner the test did not expect?
4. Check the current URL and state — did a redirect, session expiry or modal intervene?
5. Check the browser console logs (`attemptN-browser_console.json`) — JS errors, failed
   requests.
6. Check API/network evidence — call the same endpoint with `integration/api_client.py`; what
   did the backend actually return?
7. Check application logs if available.
8. Repeat deterministically — same data, same steps; does it fail the same way every time?
9. Compare expected vs actual behavior against the verified implementation (Gate 1), not
   against what the test assumed.
10. Determine the root cause and classify.

Write the classification with the evidence that supports it. Two sentences that cite the
artifact beat a paragraph of speculation.

## REAL_APPLICATION_BUG criteria

Classify as a real bug when, with evidence: the application violates expected behavior · the
backend returns an incorrect result · the UI displays an incorrect state · a business rule is
violated · authorization is bypassed · data becomes inconsistent · a valid operation fails · an
invalid operation is incorrectly accepted · a regression is introduced.

Then write the defect report (format in `reporting.md`) and add a regression test where
appropriate.

## AUTOMATION_BUG criteria (and its sub-categories)

Classify as automation when: the locator is wrong (LOCATOR_FAILURE) · the page object is
incorrect · an assertion is incorrect · test data setup is wrong (TEST_DATA_FAILURE) · wait
logic is insufficient (SYNCHRONIZATION_FAILURE) · the test assumes incorrect application
behavior · cleanup corrupts the environment · the automation uses a brittle implementation.

Fix the automation, then re-run the test and its neighbors (same page object, same flow).

## Environment, network, infrastructure, dependency

Use these when the failure is outside both the application and the suite: browser or driver
missing or mismatched (ENVIRONMENT_FAILURE), DNS/proxy/connection resets (NETWORK_FAILURE),
CI runner out of memory or disk (INFRASTRUCTURE_FAILURE), a third-party service down
(DEPENDENCY_FAILURE). The evidence is usually in `attemptN-exception.txt` and the run log. Fix
or report the environment; do not skip the test to make the run green.

## Flaky test policy

Never convert `FAIL → RETRY → PASS` into `PASS`. Report it as:

```
Initial result: FAIL
Retry result:   PASS
Classification: FLAKY_TEST
```

The runner does this automatically with `--retries N`: the final status is FLAKY, every attempt
stays in the report, and the exit code stays non-zero. Retries are diagnostic — they answer
"is it deterministic?", not "can we ignore it?".

Investigate flakiness and track: frequency · root cause · timing · environment · selector
instability · race conditions. Most flaky tests are a SYNCHRONIZATION_FAILURE or a real race in
the application; both are worth knowing.

## Self-healing policy

Automation may repair itself when the problem is clearly automation-related.

Allowed: updating broken locators · improving waits · correcting page object mappings ·
improving test data isolation · fixing framework defects.

Forbidden: removing assertions · making expected results weaker · ignoring errors · accepting
unexpected UI · treating exceptions as success · skipping broken functionality · disabling tests
merely to obtain green CI.

The test is the reason a defect became visible. If the fix you are about to make would also
have hidden a real bug, it is not a fix.

## Evidence-first examples

Bad: "Login works."
Good: "Login passed for valid credentials on Chrome 128 headless. The dashboard URL loaded, the
authenticated user's name appeared in the navbar, and `GET /api/me` returned 200 with the same
user id."

Bad: "This is probably a frontend bug."
Good: "The locator was verified against the current DOM (`attempt1-page_source.html`) and
`POST /api/orders` returned 201 with status `created` (`response.json`), but the table still
shows `pending` after the loading indicator disappeared. Classification: REAL_APPLICATION_BUG."

Bad: "Flaky, re-ran and it passed."
Good: "Failed 2 of 5 deterministic re-runs at `waits.visible(TOAST)`; the toast is removed
about 300 ms after the API response and the wait started after navigation completed.
Classification: SYNCHRONIZATION_FAILURE — wait for the toast before the URL change; re-run 5×
green."
