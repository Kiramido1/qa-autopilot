"""Page Object base class.

A page owns its locators, its UI actions and its readiness check. Business
assertions belong in tests (or flows), not here — keep pages reusable.
"""

from __future__ import annotations

from typing import Optional

from selenium.common.exceptions import TimeoutException

from core.exceptions import PageNotReady
from core.trace import trace
from core.waits import Locator, Waits, describe


class BasePage:
    path: str = "/"  # relative to settings.base_url
    ready_locator: Optional[Locator] = None  # an element that proves the page rendered

    def __init__(self, driver, settings, timeout: Optional[float] = None):
        self.driver = driver
        self.settings = settings
        self.wait = Waits(driver, timeout or settings.default_timeout)

    # ---- navigation ---------------------------------------------------
    def url(self) -> str:
        return f"{self.settings.base_url}{self.path}"

    def open(self):
        self.driver.get(self.url())
        self.wait_until_ready()
        trace("open", self.path)
        return self

    def wait_until_ready(self, timeout: Optional[float] = None):
        try:
            self.wait.page_ready(timeout)
            if self.ready_locator:
                self.wait.visible(self.ready_locator, timeout)
        except TimeoutException as error:
            raise PageNotReady(f"{type(self).__name__} not ready: {error}") from error
        return self

    def is_loaded(self, timeout: float = 2.0) -> bool:
        try:
            self.wait_until_ready(timeout)
            return True
        except PageNotReady:
            return False

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    # ---- interactions -------------------------------------------------
    def click(self, locator: Locator):
        self.wait.clickable(locator).click()
        trace("click", describe(locator))
        return self

    def type(self, locator: Locator, text: str, clear: bool = True):
        element = self.wait.visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)
        trace("type", describe(locator))
        return element

    def select_option(self, locator: Locator, visible_text: str):
        from selenium.webdriver.support.ui import Select

        Select(self.wait.visible(locator)).select_by_visible_text(visible_text)
        trace("select", f"{describe(locator)} -> {visible_text}")
        return self

    def text_of(self, locator: Locator) -> str:
        return self.wait.visible(locator).text

    def is_visible(self, locator: Locator, timeout: float = 2.0) -> bool:
        try:
            self.wait.visible(locator, timeout)
            return True
        except TimeoutException:
            return False

    def scroll_into_view(self, element):
        """JavaScript is acceptable for scrolling only; never use it to bypass a real user action."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return element
