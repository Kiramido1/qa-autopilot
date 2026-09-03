"""Reusable UI fragments (navbar, modal, table, toast...) scoped to a root element."""

from __future__ import annotations

from typing import Optional

from selenium.common.exceptions import TimeoutException

from core.waits import Locator, Waits


class BaseComponent:
    root_locator: Optional[Locator] = None

    def __init__(self, driver, timeout: float = 10.0, root_locator: Optional[Locator] = None):
        self.driver = driver
        self.wait = Waits(driver, timeout)
        resolved = root_locator if root_locator is not None else self.root_locator
        if resolved is None:
            raise ValueError(f"{type(self).__name__} needs a root_locator")
        self.locator: Locator = resolved

    @property
    def root(self):
        return self.wait.visible(self.locator)

    def find(self, locator: Locator):
        return self.root.find_element(*locator)

    def find_all(self, locator: Locator) -> list:
        return self.root.find_elements(*locator)

    def is_displayed(self, timeout: float = 2.0) -> bool:
        try:
            self.wait.visible(self.locator, timeout)
            return True
        except TimeoutException:
            return False
