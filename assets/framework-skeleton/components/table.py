"""Generic data table: rows by text, cells by header, sorting, counts.

Adapt the locators to the UI library (MUI DataGrid, AG Grid, plain <table>...)
by overriding HEADER / ROW / CELL on a subclass; the methods stay the same.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from components.base_component import BaseComponent
from core.trace import trace


class Table(BaseComponent):
    root_locator = (By.CSS_SELECTOR, "table")
    HEADER = (By.CSS_SELECTOR, "thead th")
    ROW = (By.CSS_SELECTOR, "tbody tr")
    CELL = (By.CSS_SELECTOR, "td")

    def headers(self) -> list[str]:
        return [h.text.strip() for h in self.find_all(self.HEADER)]

    def rows(self) -> list:
        return self.find_all(self.ROW)

    def row_count(self) -> int:
        return len(self.rows())

    def row_texts(self) -> list[list[str]]:
        return [[c.text.strip() for c in row.find_elements(*self.CELL)] for row in self.rows()]

    def row_by_text(self, text: str):
        """First row containing `text` in any cell; None when absent (assert in the test)."""
        for row in self.rows():
            if text in row.text:
                return row
        return None

    def wait_for_row(self, text: str, timeout: float | None = None):
        return self.wait.until(lambda d: self.row_by_text(text) or False, f"table row containing {text!r}", timeout)

    def wait_for_row_gone(self, text: str, timeout: float | None = None) -> bool:
        return self.wait.until(lambda d: self.row_by_text(text) is None, f"table row containing {text!r} gone", timeout)

    def cell(self, row, header: str) -> str:
        headers = self.headers()
        if header not in headers:
            raise ValueError(f"no column {header!r}; columns are {headers}")
        return row.find_elements(*self.CELL)[headers.index(header)].text.strip()

    def column_values(self, header: str) -> list[str]:
        return [self.cell(row, header) for row in self.rows()]

    def sort_by(self, header: str):
        for element in self.find_all(self.HEADER):
            if element.text.strip() == header:
                element.click()
                trace("sort", header)
                return self
        raise ValueError(f"no column {header!r}; columns are {self.headers()}")
