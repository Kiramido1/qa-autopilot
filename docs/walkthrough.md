# Walkthrough — one real run, from red to a defect report

Everything below is the runner's real console output from this repository's demo app, lightly
trimmed (absolute paths shortened). It shows what the skill does at Gates 13–14 when a test goes
red: collect evidence, refuse to guess, measure, classify, write the defect.

## 1. The run (injected defect `stale-dashboard`, one diagnostic retry)

```bash
python scripts/run_demo.py --bugs stale-dashboard --run-id bug-check --retries 1
```

```text
14:09:20 INFO  run bug-check — 14 test(s) | env=local base_url=http://127.0.0.1:5081 browser=chrome headless=True parallel=1
14:09:20 INFO  session: health={'bugs': ['stale-dashboard'], 'status': 'ok'}
14:09:20 INFO  ── API-001 test_me_requires_authentication [P0 · authentication]
14:09:20 INFO  [PASS] API-001 (0.00s)
14:09:20 INFO  ── API-003 test_user_cannot_delete_another_users_item [P0 · items]
14:09:20 INFO  [PASS] API-003 (0.02s)
14:09:20 INFO  ── API-002 test_item_name_boundaries [P1 · items]
14:09:20 INFO  [PASS] API-002 (0.02s)
14:09:20 INFO  ── API-004 test_items_are_scoped_to_owner [P2 · items]
14:09:20 INFO  [PASS] API-004 (0.01s)
14:09:20 INFO  ── AUTH-001 test_login_with_valid_credentials [P0 · authentication]
14:09:21 INFO  [PASS] AUTH-001 (0.96s)
14:09:21 INFO  ── AUTH-002 test_login_with_invalid_password_shows_error [P1 · authentication]
14:09:22 INFO  [PASS] AUTH-002 (0.94s)
14:09:22 INFO  ── AUTH-003 test_protected_page_redirects_anonymous_user [P1 · authentication]
14:09:23 INFO  [PASS] AUTH-003 (0.64s)
14:09:23 INFO  ── AUTH-004 test_logout_invalidates_session [P1 · authentication]
14:09:25 INFO  [PASS] AUTH-004 (2.10s)
14:09:25 INFO  ── ENV-001 test_settings_are_configured [P0 · environment]
14:09:25 INFO  env=local base_url=http://127.0.0.1:5081 api=http://127.0.0.1:5081
14:09:25 INFO  [PASS] ENV-001 (0.00s)
14:09:25 INFO  ── ENV-002 test_application_loads_in_browser [P0 · environment]
14:09:26 INFO  title='Sign in · Demo' url=http://127.0.0.1:5081/login browser={'name': 'chrome', 'version': '151.0.7922.173', 'driver_version': '151.0.7922.173', 'platform': 'linux'}
14:09:26 INFO  [PASS] ENV-002 (0.69s)
14:09:26 INFO  ── ENV-003 test_api_health_endpoint_responds [P1 · environment]
14:09:26 INFO  [PASS] ENV-003 (0.00s)
14:09:26 INFO  ── ITEM-001 test_create_item_appears_in_table_and_api [P0 · items]
14:09:37 INFO  diagnostic retry 1/1 for ITEM-001
14:09:48 INFO  [ERROR] ITEM-001 (22.69s) — TimeoutException: Message: table row containing 'Item 20260903140938-vd8od0' (waited 10.0s; url=http://127.0.0.1:5081/dashboard)
14:09:48 INFO  ── ITEM-002 test_delete_item_via_confirm_dialog [P1 · items]
14:10:00 INFO  diagnostic retry 1/1 for ITEM-002
14:10:11 INFO  [ERROR] ITEM-002 (22.44s) — TimeoutException: Message: table row containing 'Seeded 20260903140926-cdwdsy' gone (waited 10.0s; url=http://127.0.0.1:5081/dashboard)
14:10:11 INFO  ── ITEM-003 test_cancelled_delete_keeps_item [P2 · items]
14:10:13 INFO  [PASS] ITEM-003 (2.33s)
14:10:13 INFO  session: done
14:10:13 INFO  summary: 14 total | 12 pass | 0 fail | 2 error | 0 flaky | 0 skip — reports in reports/bug-check
demo app up at http://127.0.0.1:5081 (bugs: stale-dashboard); running: run_tests.py --run-id bug-check --retries 1
```

Two things to notice. The runner sorted P0 first, so the environment smoke and the P0 API checks
ran before the first browser test. And the retry did **not** turn the result green: attempt 2
failed the same way, the status is `ERROR`, the exit code is 1.

## 2. What the evidence says

`reports/bug-check/artifacts/ITEM-001/` after the run:

| File | What it shows |
|---|---|
| `attempt1-exception.txt` | `TimeoutException: table row containing 'Item …' (waited 10.0s; url=…/dashboard)` — the named wait tells you *which state* never happened |
| `items-after-create.json` | `GET /api/items` → **200, the new item is in the list** (attached by the test right after the create) |
| `attempt1-page_source.html` | the table has ids 1, 2 and 7 — the new id is **not** rendered |
| `attempt1-screenshot.png` | toast "Item … created" above the stale table |
| `attempt1-browser_console.json` | no JavaScript errors |
| `attempt1-network.json` | one non-2xx request: `favicon.ico` 404 — nothing relevant |
| `attempt1-context.json` | Chrome 151 / chromedriver 151, build `demo-app@stale-dashboard`, last API exchange |

The wait timed out, but this is not a SYNCHRONIZATION_FAILURE: the page had finished loading, the
backend already had the item, and the UI did not show it. The API evidence is what decides.

## 3. Measure before you call anything flaky

```bash
python scripts/run_demo.py --bugs stale-dashboard --run-id repeat-check --test ITEM-001 --repeat 5
```

```text
14:12:09 INFO  [ERROR] ITEM-001 (56.44s) — failed 5/5 deterministically — TimeoutException: Message: table row containing 'Item 20260903141159-vee9dg' (waited 10.0s; url=http://127.0.0.1:5084/dashboard)
14:12:09 INFO  summary: 1 total | 0 pass | 0 fail | 1 error | 0 flaky | 0 skip — reports in reports/repeat-check
```

0/5. Deterministic. Not flaky.

## 4. Classification and defect

In `qa-artifacts/execution-report.md`:

> ITEM-001 `bug-check`: ERROR at `waits.until(table row containing 'Item …')`. Evidence:
> `items-after-create.json` — `GET /api/items` 200 **including** the new item; `attempt1-page_source.html`
> — rows 1, 2, 7 only; 5/5 repeats identical (`repeat-check`). Classification: **REAL_APPLICATION_BUG** — BUG-001.

In `qa-artifacts/defects.md`, BUG-001 with severity **High** (core workflow wrong for every user,
non-obvious workaround), root cause `app.py:158-160` (`dashboard()` prefers `STALE_SNAPSHOT` over
`visible_items`), and ITEM-001 / ITEM-002 as the regression tests. The full versions are in
`assets/examples/demo-app-engagement/qa-artifacts/`.

## 5. The fix, verified

```bash
python scripts/run_demo.py --run-id verify-demo          # same suite, build without the flag
```

```text
14:15:25 INFO  ── ITEM-001 test_create_item_appears_in_table_and_api [P0 · items]
14:15:27 INFO  [PASS] ITEM-001 (2.07s)
14:15:27 INFO  ── ITEM-002 test_delete_item_via_confirm_dialog [P1 · items]
14:15:28 INFO  [PASS] ITEM-002 (1.02s)
14:15:31 INFO  summary: 14 total | 14 pass | 0 fail | 0 error | 0 flaky | 0 skip — reports in reports/verify-demo
```

No test was changed between the red run and the green one. That is the whole point.
