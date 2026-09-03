"""Phase A — environment smoke. Proves the harness can reach the app before
anything else is trusted."""
from selenium.webdriver.common.by import By

from core.assertions import assert_true
from core.registry import test


@test(id="ENV-001", feature="environment", priority="P0", tags=("smoke",), browser=False)
def test_settings_are_configured(ctx):
    """A base URL is the minimum needed to run anything."""
    assert_true(ctx.settings.base_url, "QA_BASE_URL is not set (see .env.example)")
    ctx.log.info("env=%s base_url=%s api=%s", ctx.settings.env_name, ctx.settings.base_url, ctx.settings.api_base_url)


@test(id="ENV-002", feature="environment", priority="P0", tags=("smoke",))
def test_application_loads_in_browser(ctx):
    """The browser starts and the application renders a document at the base URL."""
    ctx.driver.get(ctx.settings.base_url)
    ctx.waits.page_ready()
    assert_true(ctx.driver.find_elements(By.TAG_NAME, "body"), "no <body> rendered at the base URL")
    ctx.screenshot("landing.png")
    ctx.log.info("title=%r url=%s", ctx.driver.title, ctx.driver.current_url)


@test(id="ENV-003", feature="environment", priority="P1", tags=("smoke", "integration"), browser=False)
def test_api_health_endpoint_responds(ctx):
    """The API answers at its health path; a 5xx means the backend is not usable."""
    if not ctx.settings.api_base_url:
        ctx.skip("QA_API_BASE_URL not set")
    response = ctx.api.get(ctx.settings.api_health_path)
    ctx.attach("health-response.json", ctx.api.last_exchange())
    assert_true(response.status_code < 500, f"health endpoint returned {response.status_code}")
