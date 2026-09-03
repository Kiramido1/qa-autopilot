"""Native <select> and custom listbox dropdowns behind one interface."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from components.base_component import BaseComponent
from core.trace import trace


class NativeSelect(BaseComponent):
    """A <select> element; root_locator points at the select itself."""

    def options(self) -> list[str]:
        return [o.text.strip() for o in Select(self.root).options]

    def selected_text(self) -> str:
        return Select(self.root).first_selected_option.text.strip()

    def select_by_text(self, text: str):
        Select(self.root).select_by_visible_text(text)
        trace("select", text)
        return self

    def select_by_value(self, value: str):
        Select(self.root).select_by_value(value)
        trace("select", value)
        return self


class Listbox(BaseComponent):
    """Custom dropdown: a trigger that opens a list of options (role=listbox/option by default)."""

    OPTIONS = (By.CSS_SELECTOR, "[role='option']")
    LISTBOX = (By.CSS_SELECTOR, "[role='listbox']")

    def open(self):
        self.root.click()
        self.wait.visible(self.LISTBOX)
        return self

    def options(self) -> list[str]:
        self.open()
        return [o.text.strip() for o in self.driver.find_elements(*self.OPTIONS)]

    def select_by_text(self, text: str):
        self.open()
        for option in self.driver.find_elements(*self.OPTIONS):
            if option.text.strip() == text:
                option.click()
                trace("select", text)
                self.wait.absent(self.LISTBOX)
                return self
        raise ValueError(f"no option {text!r}")

    def selected_text(self) -> str:
        return self.root.text.strip()
