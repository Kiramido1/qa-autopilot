"""EXAMPLE page object.

Locators follow the Gate 7 priority (data-testid > stable id > name > semantic
> stable CSS > relative XPath). Replace them with what the real DOM offers, and
ask developers for data-testid attributes where nothing stable exists.
"""
from __future__ import annotations

from selenium.webdriver.common.by import By

from core.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    EMAIL = (By.CSS_SELECTOR, "[data-testid='login-email']")
    PASSWORD = (By.CSS_SELECTOR, "[data-testid='login-password']")
    SUBMIT = (By.CSS_SELECTOR, "[data-testid='login-submit']")
    ERROR = (By.CSS_SELECTOR, "[data-testid='login-error']")

    ready_locator = SUBMIT

    def login(self, email: str, password: str):
        self.type(self.EMAIL, email)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self

    def error_text(self) -> str:
        return self.text_of(self.ERROR)
