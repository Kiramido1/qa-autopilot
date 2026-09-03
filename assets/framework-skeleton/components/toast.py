"""EXAMPLE component — replace the locator with the real one after Gate 7."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from components.base_component import BaseComponent


class Toast(BaseComponent):
    root_locator = (By.CSS_SELECTOR, "[data-testid='toast']")

    def message(self) -> str:
        return self.root.text.strip()

    def wait_until_gone(self, timeout: float = 10.0) -> bool:
        return self.wait.absent(self.root_locator, timeout)
