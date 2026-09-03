#!/usr/bin/env python3
"""Demo application for the selenium-qa-automation skill.

A deliberately small Flask app (login, dashboard with an items table, JSON
API) with stable data-testid attributes, used to prove the bundled framework
end to end: a fresh clone runs green against it, and CI does the same.

    pip install flask
    python app.py                       # http://127.0.0.1:5000
    DEMO_BUGS=stale-dashboard python app.py   # inject a documented defect for triage practice

Accounts: qa.user@example.test / Password123!  ·  qa.admin@example.test / Password123!

Injectable defects (DEMO_BUGS, comma separated) — used by assets/examples/:
  stale-dashboard   the dashboard renders the item list captured at login, so a
                    newly created item is missing until the user logs in again
  idor              DELETE /api/items/<id> skips the ownership check
"""

from __future__ import annotations

import itertools
import os
from functools import wraps

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("DEMO_SECRET_KEY", "demo-only-not-a-secret")
BUGS = {b.strip() for b in os.environ.get("DEMO_BUGS", "").split(",") if b.strip()}

USERS = {
    "qa.user@example.test": {"password": "Password123!", "name": "QA User", "role": "user"},
    "qa.admin@example.test": {"password": "Password123!", "name": "QA Admin", "role": "admin"},
}
_ids = itertools.count(1)
ITEMS: dict[int, dict] = {}
STALE_SNAPSHOT: dict[str, list] = {}
MAX_NAME = 50


def seed() -> None:
    ITEMS.clear()
    for owner, name in (
        ("qa.user@example.test", "Quarterly report"),
        ("qa.user@example.test", "Launch checklist"),
        ("qa.admin@example.test", "Admin runbook"),
    ):
        item_id = next(_ids)
        ITEMS[item_id] = {"id": item_id, "name": name, "owner": owner}


def current_user():
    email = session.get("user")
    return {"email": email, **USERS[email]} if email in USERS else None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def api_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "authentication required"}), 401
        return view(*args, **kwargs)

    return wrapper


def visible_items(user) -> list[dict]:
    if user["role"] == "admin":
        return list(ITEMS.values())
    return [i for i in ITEMS.values() if i["owner"] == user["email"]]


def validate_name(name) -> str | None:
    if not isinstance(name, str) or not name.strip():
        return "name is required"
    if len(name.strip()) > MAX_NAME:
        return f"name must be at most {MAX_NAME} characters"
    return None


LAYOUT = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{{ title }} · Demo</title>
<style>body{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}
.toast{background:#e6f4ea;border:1px solid #34a853;padding:.5rem 1rem;margin:1rem 0}
.error{color:#b00020}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:.4rem;text-align:left}
[role=dialog]{border:1px solid #333;padding:1rem;background:#fff;position:fixed;top:30%;left:50%;transform:translateX(-50%)}
[hidden]{display:none!important}</style></head><body>{{ body|safe }}</body></html>"""

LOGIN = """<h1>Sign in</h1>
{% if error %}<p class="error" data-testid="login-error" role="alert">{{ error }}</p>{% endif %}
<form method="post" data-testid="login-form">
<label for="email">Email</label><br><input id="email" name="email" type="email" data-testid="login-email" value="{{ email }}" required><br>
<label for="password">Password</label><br><input id="password" name="password" type="password" data-testid="login-password" required><br>
<input type="hidden" name="next" value="{{ next }}">
<button type="submit" data-testid="login-submit">Sign in</button></form>"""

DASHBOARD = """<nav><span data-testid="user-name">{{ user.name }}</span> · <span data-testid="user-role">{{ user.role }}</span>
· <a href="/logout" data-testid="logout-link">Sign out</a></nav>
<h1>Dashboard</h1>
{% if toast %}<div class="toast" data-testid="toast" role="status">{{ toast }}</div>{% endif %}
{% if error %}<p class="error" data-testid="item-error" role="alert">{{ error }}</p>{% endif %}
<form method="post" action="/items" data-testid="item-form">
<label for="name">New item</label> <input id="name" name="name" data-testid="item-name" maxlength="{{ max_name }}">
<button type="submit" data-testid="item-create">Create</button></form>
<table data-testid="items-table"><thead><tr><th>ID</th><th>Name</th><th>Owner</th><th>Actions</th></tr></thead><tbody>
{% for item in items %}<tr data-testid="item-row" data-item-id="{{ item.id }}"><td>{{ item.id }}</td><td data-testid="item-name-cell">{{ item.name }}</td><td>{{ item.owner }}</td>
<td><button type="button" data-testid="item-delete-{{ item.id }}" onclick="openDialog({{ item.id }}, '{{ item.name|e }}')">Delete</button></td></tr>
{% else %}<tr data-testid="items-empty"><td colspan="4">No items yet</td></tr>{% endfor %}</tbody></table>
<div role="dialog" aria-modal="true" aria-labelledby="dlg-title" data-testid="confirm-dialog" hidden>
<h2 id="dlg-title">Delete item?</h2><p data-testid="dialog-body"></p>
<form method="post" id="delete-form"><button type="submit" data-testid="modal-confirm">Delete</button>
<button type="button" data-testid="modal-cancel" onclick="closeDialog()">Cancel</button></form></div>
<script>function openDialog(id,name){const d=document.querySelector('[role=dialog]');d.hidden=false;
document.querySelector('[data-testid=dialog-body]').textContent='Delete "'+name+'"? This cannot be undone.';
document.getElementById('delete-form').action='/items/'+id+'/delete';}
function closeDialog(){document.querySelector('[role=dialog]').hidden=true;}</script>"""


def page(title: str, template: str, **context):
    return render_template_string(LAYOUT, title=title, body=render_template_string(template, **context))


@app.get("/")
def index():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error, email = None, ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        account = USERS.get(email)
        if account and account["password"] == request.form.get("password"):
            session.clear()
            session["user"] = email
            if "stale-dashboard" in BUGS:
                STALE_SNAPSHOT[email] = [dict(i) for i in visible_items({"email": email, **account})]
            target = request.form.get("next") or url_for("dashboard")
            return redirect(target if target.startswith("/") else url_for("dashboard"))
        error = "Invalid email or password"
    return page("Sign in", LOGIN, error=error, email=email, next=request.args.get("next", ""))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    items = STALE_SNAPSHOT.get(user["email"]) if "stale-dashboard" in BUGS else None
    if items is None:
        items = visible_items(user)
    return page(
        "Dashboard",
        DASHBOARD,
        user=user,
        items=items,
        toast=session.pop("toast", None),
        error=session.pop("error", None),
        max_name=MAX_NAME,
    )


@app.post("/items")
@login_required
def create_item_form():
    problem = validate_name(request.form.get("name"))
    if problem:
        session["error"] = problem
    else:
        item = _create(current_user(), request.form["name"].strip())
        session["toast"] = f'Item "{item["name"]}" created'
    return redirect(url_for("dashboard"))


@app.post("/items/<int:item_id>/delete")
@login_required
def delete_item_form(item_id: int):
    status = _delete(current_user(), item_id)
    session["toast" if status == 204 else "error"] = "Item deleted" if status == 204 else f"Could not delete item ({status})"
    return redirect(url_for("dashboard"))


# ---- JSON API ---------------------------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "bugs": sorted(BUGS)})


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    account = USERS.get(email)
    if not account or account["password"] != data.get("password"):
        return jsonify({"error": "invalid credentials"}), 401
    session.clear()
    session["user"] = email
    return jsonify({"email": email, "name": account["name"], "role": account["role"]})


@app.get("/api/me")
@api_auth
def api_me():
    user = current_user()
    return jsonify({"email": user["email"], "name": user["name"], "role": user["role"]})


@app.get("/api/items")
@api_auth
def api_items():
    return jsonify(visible_items(current_user()))


@app.post("/api/items")
@api_auth
def api_create_item():
    data = request.get_json(silent=True) or {}
    problem = validate_name(data.get("name"))
    if problem:
        return jsonify({"error": problem}), 400
    return jsonify(_create(current_user(), data["name"].strip())), 201


@app.delete("/api/items/<int:item_id>")
@api_auth
def api_delete_item(item_id: int):
    status = _delete(current_user(), item_id)
    if status == 204:
        return "", 204
    return jsonify({"error": {403: "forbidden", 404: "not found"}[status]}), status


@app.post("/api/reset")
def api_reset():
    """Test hook: restore seed data (disposable demo only — never ship this)."""
    STALE_SNAPSHOT.clear()
    seed()
    return jsonify({"status": "reset", "items": len(ITEMS)})


def _create(user, name: str) -> dict:
    item = {"id": next(_ids), "name": name, "owner": user["email"]}
    ITEMS[item["id"]] = item
    return item


def _delete(user, item_id: int) -> int:
    item = ITEMS.get(item_id)
    if item is None:
        return 404
    if item["owner"] != user["email"] and user["role"] != "admin" and "idor" not in BUGS:
        return 403
    del ITEMS[item_id]
    return 204


seed()

if __name__ == "__main__":
    app.run(host=os.environ.get("DEMO_HOST", "127.0.0.1"), port=int(os.environ.get("DEMO_PORT", "5000")), debug=False)
