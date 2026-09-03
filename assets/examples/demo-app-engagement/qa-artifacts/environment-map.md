# Environment map

> Gate 0 deliverable. Fill from the repository and by actually starting the app — not from assumptions.
> Exit criterion: you can launch and reach the application. If not, stop and investigate.

## Execution environment
- OS / Python / Node: Linux (Debian 13) / Python 3.13.11 / Node not needed (server-rendered Flask app, no build step)
- Selenium version: 4.31.1 (system package). Selenium Manager binary is **missing** in this packaging, so drivers must be given explicitly.
- Browsers available (name → version): Chrome 151.0.7922.173 (`/usr/bin/chromium`) with chromedriver 151.0.7922.173 (`/usr/bin/chromedriver`); Firefox with geckodriver at `/usr/bin/geckodriver`. Chrome is the primary browser (Gate 20).
- Docker / compose: none in the repo; the app runs as a plain process.
- CI/CD configuration found: `.github/workflows/qa.yml` at the skill root runs the skeleton against this same app on Chrome and Firefox.

## Application
- Startup command(s): `DEMO_BUGS=stale-dashboard python assets/demo-app/app.py` (port 5000; `DEMO_PORT` overrides). Verified: `GET /api/health` → `{"bugs": ["stale-dashboard"], "status": "ok"}`.
- Required services (DB, cache, queue, storage): none — items live in an in-memory dict (`app.py:36`), reset on restart or via `POST /api/reset` (`app.py:234-239`).
- Required environment variables (names only, never values): `DEMO_SECRET_KEY` (optional, has a demo default), `DEMO_BUGS`, `DEMO_HOST`, `DEMO_PORT`.
- Seed data / migrations: `seed()` at `app.py:41-45` creates 3 items (ids 1–2 owned by the user account, id 3 by the admin). No migrations.
- Base URL / API base URL: `http://127.0.0.1:5000` for both (UI and JSON API share the origin and the session cookie).
- Authentication method and test accounts (role → where the credential lives): Flask signed session cookie set by `POST /login` (form) or `POST /api/login` (JSON). `test_user` → `QA_TEST_USER_EMAIL` / `QA_TEST_USER_PASSWORD`; `admin` → `QA_ADMIN_EMAIL` / `QA_ADMIN_PASSWORD` (values in `qa/.env`, taken from `.env.example`; both accounts are hardcoded demo accounts in `app.py:31-34`).

## Existing tests and automation
- Test directories and frameworks found: none in the app itself. The skill's skeleton (`qa/`, custom runner) is the first suite.
- What they cover / how to run them: n/a.

## Known limitations
- Selenium Manager cannot download drivers here → `QA_CHROMEDRIVER_PATH=/usr/bin/chromedriver QA_CHROME_BINARY=/usr/bin/chromium` are required. Without them every browser test is ERROR `NoSuchDriverException` (seen once, run discarded).
- State is process-local: a parallel run against one app instance shares the item store, so tests use unique names from `data/factories.py` and clean up what they create.
- No session expiry, no password reset, no pagination exist in the app — those areas cannot be tested and are listed in `coverage-gaps.md`.

## Evidence
- `DEMO_BUGS=stale-dashboard python app.py` → app up; `curl /api/health` → 200 JSON above.
- Run `20260903-132200`, Phase A: ENV-001 PASS (settings), ENV-002 PASS (browser rendered `/login`, title `Sign in · Demo`, screenshot `artifacts/ENV-002/landing.png`), ENV-003 PASS (health 200, exchange attached as `artifacts/ENV-003/health-response.json`).
- Browser identity recorded by the runner: chrome 151.0.7922.173 / driver 151.0.7922.173 (`runs/20260903-132200/report.json` → `run.browser`).
