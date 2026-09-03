"""EXAMPLE flow: multi-step user journeys composed from page objects.

Flows are where cross-page sequences live so tests read as business steps.
"""

from __future__ import annotations

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage


def login(driver, settings, email: str, password: str) -> DashboardPage:
    """Log in through the real UI and wait until the dashboard is ready.

    Tighten the success condition to what the application really does
    (dashboard URL, user menu, welcome text) when adapting this flow.
    """
    page = LoginPage(driver, settings).open()
    page.login(email, password)
    return DashboardPage(driver, settings).wait_until_ready()


def login_as(ctx, role: str = "test_user") -> DashboardPage:
    """Authenticated dashboard for `role`, reusing the session after the first login (ctx.login_once)."""
    creds = ctx.require_credentials(role)
    ctx.login_once(role, lambda: login(ctx.driver, ctx.settings, creds.email, creds.password))
    return DashboardPage(ctx.driver, ctx.settings).open()
