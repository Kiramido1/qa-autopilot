"""Dialog / modal component. Root defaults to role="dialog"; override the
button locators for the UI library in use."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from components.base_component import BaseComponent
from core.trace import trace


class Modal(BaseComponent):
    root_locator = (By.CSS_SELECTOR, "[role='dialog']")
    TITLE = (By.CSS_SELECTOR, "h1, h2, h3, [data-testid='modal-title']")
    CONFIRM = (By.CSS_SELECTOR, "[data-testid='modal-confirm']")
    CANCEL = (By.CSS_SELECTOR, "[data-testid='modal-cancel']")
    CLOSE = (By.CSS_SELECTOR, "[data-testid='modal-close'], [aria-label='Close']")

    def title(self) -> str:
        return self.find(self.TITLE).text.strip()

    def body_text(self) -> str:
        return self.root.text.strip()

    def confirm(self):
        self._click(self.CONFIRM, "confirm")
        return self

    def cancel(self):
        self._click(self.CANCEL, "cancel")
        return self

    def close(self):
        self._click(self.CLOSE, "close")
        return self

    def wait_until_gone(self, timeout: float | None = None) -> bool:
        return self.wait.absent(self.locator, timeout)

    def _click(self, locator, action: str) -> None:
        self.root  # noqa: B018 - ensures the dialog is visible before looking inside it
        self.wait.clickable(locator).click()
        trace(f"modal-{action}", "")
