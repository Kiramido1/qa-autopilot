"""EXAMPLE integration checks (Python requests -> API -> backend), no browser.
Authorization and validation are cheaper and stronger here than through the UI."""

from core.assertions import assert_equal, assert_in, assert_status
from core.registry import test
from data.factories import boundary_strings, unique_name


def _login(ctx, role: str):
    creds = ctx.require_credentials(role)
    response = ctx.api.post("/api/login", json={"email": creds.email, "password": creds.password})
    assert_status(response, 200, f"API login failed for {role}")
    return creds


@test(id="API-001", feature="authentication", priority="P0", tags=("integration", "authorization"), browser=False)
def test_me_requires_authentication(ctx):
    """/api/me without a session is rejected, not served."""
    response = ctx.api.get("/api/me")
    ctx.attach("me-anonymous.json", ctx.api.last_exchange())
    assert_status(response, 401, "protected endpoint served an anonymous request")


@test(id="API-002", feature="items", priority="P1", tags=("integration", "boundary"), browser=False)
def test_item_name_boundaries(ctx):
    """Name length 1 and 50 are accepted; 0 and 51 are rejected with 400 (limits verified in app.py)."""
    _login(ctx, "test_user")
    cases = boundary_strings(1, 50)
    for label, expected in (("at_min", 201), ("at_max", 201), ("empty", 400), ("above_max", 400), ("whitespace", 400)):
        response = ctx.api.post("/api/items", json={"name": cases[label]})
        assert_status(response, expected, f"unexpected status for {label} ({len(cases[label])} chars)")
        if response.status_code == 201:
            ctx.add_cleanup(ctx.api.delete, f"/api/items/{response.json()['id']}")
    ctx.attach("boundaries-last-exchange.json", ctx.api.history())


@test(id="API-003", feature="items", priority="P0", tags=("integration", "authorization", "security"), browser=False)
def test_user_cannot_delete_another_users_item(ctx):
    """Object-level authorization (IDOR): a user deleting an admin-owned item gets 403 and the item survives."""
    _login(ctx, "admin")
    admin_item = ctx.api.post("/api/items", json={"name": unique_name("AdminOwned")}).json()
    ctx.add_cleanup(ctx.api.delete, f"/api/items/{admin_item['id']}")
    ctx.api.session.cookies.clear()
    _login(ctx, "test_user")
    response = ctx.api.delete(f"/api/items/{admin_item['id']}")
    ctx.attach("idor-attempt.json", ctx.api.last_exchange())
    assert_status(response, 403, "user was allowed to delete another user's item")
    ctx.api.session.cookies.clear()
    _login(ctx, "admin")
    ids = [i["id"] for i in ctx.api.get("/api/items").json()]
    assert_in(admin_item["id"], ids, "the admin's item was deleted despite the 403")


@test(id="API-004", feature="items", priority="P2", tags=("integration",), browser=False)
def test_items_are_scoped_to_owner(ctx):
    """A regular user only sees their own items."""
    creds = _login(ctx, "test_user")
    items = ctx.api.get("/api/items").json()
    ctx.attach("items.json", ctx.api.last_exchange())
    assert_equal({i["owner"] for i in items} - {creds.email}, set(), "item list contains other owners' items")
