# Demo application

A ~200-line Flask app the bundled framework is verified against: login,
dashboard with an items table and a confirm dialog, and a JSON API — every
interactive element carries a `data-testid`.

```bash
pip install -r requirements.txt
python app.py                              # http://127.0.0.1:5000
DEMO_BUGS=stale-dashboard python app.py    # inject a documented defect (see app.py)
```

Accounts: `qa.user@example.test` and `qa.admin@example.test`, password `Password123!`.

| Route | Purpose |
|---|---|
| `GET/POST /login`, `GET /logout` | session login form (`login-email`, `login-password`, `login-submit`, `login-error`) |
| `GET /dashboard` | `user-name`, `items-table`, `item-row`, `item-name`, `item-create`, `toast`, `confirm-dialog` |
| `POST /items`, `POST /items/<id>/delete` | form actions behind the dashboard |
| `GET /api/health` | `{"status": "ok", "bugs": [...]}` |
| `POST /api/login`, `GET /api/me` | cookie session for API checks |
| `GET/POST /api/items`, `DELETE /api/items/<id>` | owner-scoped items; name 1–50 chars; 403 on someone else's item |
| `POST /api/reset` | restore seed data (test hook) |

`DEMO_BUGS=stale-dashboard` makes the dashboard render the list captured at
login (a real application bug for triage practice); `DEMO_BUGS=idor` removes
the ownership check on delete (a Gate 18 finding). `assets/examples/` shows
the full engagement against the app with `stale-dashboard` enabled.
