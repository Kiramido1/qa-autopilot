"""EXAMPLE page object (matches the bundled demo app; adapt to the real DOM).

Locators follow the Gate 7 priority (data-testid > stable id > name > semantic
> stable CSS > relative XPath). Replace them with what the real DOM offers, and
ask developers for data-testid attributes where nothing stable exists.
"""

from __future__ import annotations

from core.base_page import BasePage
from core.locators import by_testid


class LoginPage(BasePage):
    path = "/login"

    EMAIL = by_testid("login-email")
    PASSWORD = by_testid("login-password")
    SUBMIT = by_testid("login-submit")
    ERROR = by_testid("login-error")

    ready_locator = SUBMIT

    def login(self, email: str, password: str):
        self.type(self.EMAIL, email)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self

    def error_text(self) -> str:
        return self.text_of(self.ERROR)
