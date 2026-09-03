# Environment map

> Gate 0 deliverable — checklist and exit criterion in `references/gates.md#gate-0`. Fill from the repository
> **and by actually starting the app**. Exit criterion is literal: the ENV-* smoke tests have executed
> (`python run_tests.py --smoke`). Delete the EXAMPLE lines after use; a complete one is in
> `assets/examples/demo-app-engagement/qa-artifacts/environment-map.md`.

## Execution environment
- OS / Python / Node: <!-- EXAMPLE: Debian 13, Python 3.13.11, no Node (server-rendered) -->
- Selenium version: <!-- EXAMPLE: 4.31.1 -->
- Browsers available (name → version): <!-- EXAMPLE: chrome 151.0.7922.173 (driver 151 via QA_CHROMEDRIVER_PATH), firefox 128 -->
- Docker / compose: <!-- EXAMPLE: none -->
- CI/CD configuration found: <!-- EXAMPLE: .github/workflows/qa.yml runs the suite headless on push -->

## Application
- Startup command(s): <!-- EXAMPLE: `python app.py` → http://127.0.0.1:5000 (verified: /api/health → 200) -->
- Required services (DB, cache, queue, storage): <!-- EXAMPLE: none, in-memory store -->
- Required environment variables (names only, never values): <!-- EXAMPLE: DEMO_SECRET_KEY (optional), DEMO_BUGS (test-only) -->
- Seed data / migrations: <!-- EXAMPLE: seed() at import; POST /api/reset restores it -->
- Base URL / API base URL: <!-- EXAMPLE: http://127.0.0.1:5000 / same origin, health at /api/health -->
- Authentication method and test accounts (role → where the credential lives): <!-- EXAMPLE: cookie session; test_user → QA_TEST_USER_*, admin → QA_ADMIN_* in qa/.env -->

## Existing tests and automation
- Test directories and frameworks found: <!-- EXAMPLE: none -->
- What they cover / how to run them: <!-- EXAMPLE: — -->

## Known limitations
- <!-- EXAMPLE: Selenium Manager cannot download drivers on this machine → explicit driver paths required -->

## Evidence
- Command run → result (startup log excerpt, health check response, screenshot): <!-- EXAMPLE: `--smoke` run 20260903-132200: ENV-001/002/003 PASS, landing.png under artifacts/ENV-002/ -->
