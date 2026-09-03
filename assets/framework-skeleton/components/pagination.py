"""Pagination control: next/previous/go-to with state queries."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from components.base_component import BaseComponent
from core.trace import trace


class Pagination(BaseComponent):
    root_locator = (By.CSS_SELECTOR, "[data-testid='pagination'], nav[aria-label='pagination'], .pagination")
    NEXT = (By.CSS_SELECTOR, "[data-testid='pagination-next'], [aria-label='Next page'], a[rel='next']")
    PREVIOUS = (By.CSS_SELECTOR, "[data-testid='pagination-prev'], [aria-label='Previous page'], a[rel='prev']")
    PAGE = (By.CSS_SELECTOR, "[data-testid^='pagination-page-'], [aria-label^='Page ']")
    CURRENT = (By.CSS_SELECTOR, "[aria-current='page'], .active")

    def current_page(self) -> int:
        text = self.find(self.CURRENT).text.strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        return int(digits) if digits else 1

    def has_next(self) -> bool:
        return self._enabled(self.NEXT)

    def has_previous(self) -> bool:
        return self._enabled(self.PREVIOUS)

    def next(self):
        self.find(self.NEXT).click()
        trace("pagination", "next")
        return self

    def previous(self):
        self.find(self.PREVIOUS).click()
        trace("pagination", "previous")
        return self

    def go_to(self, number: int):
        for link in self.find_all(self.PAGE):
            if link.text.strip() == str(number):
                link.click()
                trace("pagination", str(number))
                return self
        raise ValueError(f"no page link {number}")

    def _enabled(self, locator) -> bool:
        elements = self.find_all(locator)
        if not elements:
            return False
        element = elements[0]
        return (
            element.is_enabled()
            and element.get_attribute("aria-disabled") != "true"
            and "disabled" not in (element.get_attribute("class") or "")
        )
