"""EXAMPLE flow: multi-step user journeys composed from page objects.

Flows are where cross-page sequences live so tests read as business steps.
"""
from __future__ import annotations

from pages.login_page import LoginPage


def login(driver, settings, email: str, password: str) -> str:
    """Log in through the real UI and wait until the app leaves the login page.

    Returns the post-login URL. Tighten the success condition to what the
    application really does (dashboard URL, user menu, welcome text).
    """
    page = LoginPage(driver, settings).open()
    login_url = driver.current_url
    page.login(email, password)
    page.wait.url_changes(login_url)
    return driver.current_url
