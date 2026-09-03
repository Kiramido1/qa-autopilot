"""EXAMPLE tests for the example LoginPage. Replace with cases from
qa-artifacts/test-cases.md once the real locators and behavior are known."""
from core.assertions import assert_in, assert_not_in, assert_visible
from core.registry import test
from data.factories import unique_email
from pages.login_page import LoginPage


@test(id="AUTH-001", feature="authentication", priority="P0", tags=("smoke", "regression", "e2e"))
def test_login_with_valid_credentials(ctx):
    """Valid credentials leave the login page."""
    creds = ctx.require_credentials("test_user")
    page = LoginPage(ctx.driver, ctx.settings).open()
    page.login(creds.email, creds.password)
    ctx.waits.url_changes(page.url())
    assert_not_in("/login", ctx.driver.current_url, "still on the login page after submitting valid credentials")
    ctx.log.info("post-login url=%s", ctx.driver.current_url)


@test(id="AUTH-002", feature="authentication", priority="P1", tags=("regression", "negative"))
def test_login_with_invalid_password_shows_error(ctx):
    """Wrong password: an error is shown and the user stays on the login page."""
    page = LoginPage(ctx.driver, ctx.settings).open()
    page.login(unique_email(), "wrong-password-123")
    assert_visible(page, LoginPage.ERROR, "no error message for invalid credentials", ctx.settings.default_timeout)
    assert_in("/login", ctx.driver.current_url, "navigated away from login with invalid credentials")
