"""EXAMPLE cross-layer journeys: UI action -> API evidence -> UI state.
Session reuse (ctx.login_once) keeps them fast; setup_module seeds via the API."""

from core.assertions import assert_equal, assert_in, assert_not_in, assert_true
from core.registry import test
from data.factories import unique_name
from flows.authentication import login_as
from pages.dashboard_page import DashboardPage


def setup_module(module):
    """Seed one item through the API for the delete journey; remove it afterwards if it survives."""
    email, password = module.settings.credentials("test_user")
    if not (email and password):
        return
    login = module.api.post("/api/login", json={"email": email, "password": password})
    if login.status_code != 200:
        raise RuntimeError(f"API login failed: {login.status_code} {login.text[:200]}")
    created = module.api.post("/api/items", json={"name": unique_name("Seeded")})
    created.raise_for_status()
    item = created.json()
    item_id = item["id"]
    module.store["seeded_item"] = item
    module.add_cleanup(lambda: module.api.delete(f"/api/items/{item_id}"))


@test(id="ITEM-001", feature="items", priority="P0", tags=("e2e", "regression"))
def test_create_item_appears_in_table_and_api(ctx):
    """Creating an item through the UI persists it (API) and shows it in the table with a toast."""
    dashboard = login_as(ctx, "test_user")
    name = unique_name("Item")
    dashboard.create_item(name)
    assert_in(name, dashboard.toast.message(), "no confirmation toast after creating an item")
    ctx.api.set_cookies_from_driver(ctx.driver)
    items = ctx.api.get("/api/items").json()
    ctx.attach("items-after-create.json", ctx.api.last_exchange())
    created = next((i for i in items if i["name"] == name), None)
    assert_true(created is not None, "backend did not persist the item created in the UI")
    assert created is not None  # narrows the type for mypy; the real check is the assertion above
    ctx.add_cleanup(ctx.api.delete, f"/api/items/{created['id']}")
    dashboard.table.wait_for_row(name)
    assert_in(name, dashboard.item_names(), "item persisted by the backend is missing from the table")


@test(id="ITEM-002", feature="items", priority="P1", tags=("e2e", "regression"))
def test_delete_item_via_confirm_dialog(ctx):
    """Confirming the delete dialog removes the row and the backend no longer returns the item."""
    seeded = ctx.module.store.get("seeded_item")
    if not seeded:
        ctx.skip("setup_module could not seed an item (credentials missing)")
    dashboard = login_as(ctx, "test_user")
    dashboard.table.wait_for_row(seeded["name"])
    dashboard.delete_item(seeded["id"], confirm=True)
    dashboard.table.wait_for_row_gone(seeded["name"])
    ctx.api.set_cookies_from_driver(ctx.driver)
    remaining = [i["id"] for i in ctx.api.get("/api/items").json()]
    ctx.attach("items-after-delete.json", ctx.api.last_exchange())
    assert_not_in(seeded["id"], remaining, "backend still returns the deleted item")


@test(id="ITEM-003", feature="items", priority="P2", tags=("e2e", "regression", "negative"))
def test_cancelled_delete_keeps_item(ctx):
    """Cancelling the confirm dialog changes nothing."""
    dashboard = login_as(ctx, "test_user")
    names = dashboard.item_names()
    if not names:
        ctx.skip("no items to cancel-delete")
    first_row = dashboard.table.rows()[0]
    item_id = int(first_row.get_attribute("data-item-id"))
    dashboard.delete_item(item_id, confirm=False)
    assert_equal(DashboardPage(ctx.driver, ctx.settings).item_names(), names, "cancelling the dialog changed the table")
