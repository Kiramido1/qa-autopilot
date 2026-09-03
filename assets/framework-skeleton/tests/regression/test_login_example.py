"""EXAMPLE authentication tests (green against the bundled demo app).
Replace with cases from qa-artifacts/test-cases.md once the real locators and
behavior are known."""

from urllib.parse import urlsplit

from core.assertions import assert_equal, assert_in, assert_visible
from core.registry import test
from data.factories import unique_email
from flows.authentication import login
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage


@test(id="AUTH-001", feature="authentication", priority="P0", tags=("smoke", "regression", "e2e"))
def test_login_with_valid_credentials(ctx):
    """Valid credentials reach the dashboard and the identity shown is the account that logged in."""
    creds = ctx.require_credentials("test_user")
    dashboard = login(ctx.driver, ctx.settings, creds.email, creds.password)
    assert_in("/dashboard", ctx.driver.current_url, "did not reach the dashboard after valid login")
    ctx.api.set_cookies_from_driver(ctx.driver)
    me = ctx.api.get("/api/me")
    ctx.attach("me.json", ctx.api.last_exchange())
    assert_equal(me.status_code, 200, "backend does not recognise the browser session")
    assert_equal(dashboard.user_name(), me.json()["name"], "UI identity differs from the backend identity")


@test(id="AUTH-002", feature="authentication", priority="P1", tags=("regression", "negative"))
def test_login_with_invalid_password_shows_error(ctx):
    """Wrong password: an error is shown and the user stays on the login page."""
    page = LoginPage(ctx.driver, ctx.settings).open()
    page.login(unique_email(), "wrong-password-123")
    assert_visible(page, LoginPage.ERROR, "no error message for invalid credentials", ctx.settings.default_timeout)
    assert_in("/login", ctx.driver.current_url, "navigated away from login with invalid credentials")


@test(id="AUTH-003", feature="authentication", priority="P1", tags=("regression", "authorization"))
def test_protected_page_redirects_anonymous_user(ctx):
    """Direct URL access to the dashboard without a session lands on the login page."""
    ctx.driver.get(f"{ctx.settings.base_url}/dashboard")
    ctx.waits.url_contains("/login")
    # Compare the path, not the whole URL: the redirect carries ?next=/dashboard.
    assert_equal(urlsplit(ctx.driver.current_url).path, "/login", "anonymous user was not redirected to the login page")


@test(id="AUTH-004", feature="authentication", priority="P1", tags=("regression",))
def test_logout_invalidates_session(ctx):
    """After sign-out the dashboard is no longer reachable with the old browser session."""
    creds = ctx.require_credentials("test_user")
    dashboard = login(ctx.driver, ctx.settings, creds.email, creds.password)
    dashboard.logout()
    ctx.waits.url_contains("/login")
    ctx.driver.get(f"{ctx.settings.base_url}/dashboard")
    ctx.waits.url_contains("/login")
    assert_in("/login", ctx.driver.current_url, "dashboard still reachable after logout")
    page = DashboardPage(ctx.driver, ctx.settings)
    assert_equal(page.is_loaded(1.0), False, "dashboard rendered after logout")
