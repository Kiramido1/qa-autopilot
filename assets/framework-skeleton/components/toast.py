"""EXAMPLE component — replace the locator with the real one after Gate 7."""

from __future__ import annotations

from components.base_component import BaseComponent
from core.locators import by_testid


class Toast(BaseComponent):
    root_locator = by_testid("toast")

    def message(self) -> str:
        return self.root.text.strip()

    def wait_until_gone(self, timeout: float = 10.0) -> bool:
        return self.wait.absent(self.locator, timeout)
