"""EXAMPLE page object for the demo dashboard: items table, create form, confirm dialog."""

from __future__ import annotations

from components.modal import Modal
from components.table import Table
from components.toast import Toast
from core.base_page import BasePage
from core.locators import by_testid


class DashboardPage(BasePage):
    path = "/dashboard"

    USER_NAME = by_testid("user-name")
    USER_ROLE = by_testid("user-role")
    LOGOUT = by_testid("logout-link")
    ITEM_NAME = by_testid("item-name")
    ITEM_CREATE = by_testid("item-create")
    ITEM_ERROR = by_testid("item-error")
    ITEMS_TABLE = by_testid("items-table")
    ready_locator = ITEMS_TABLE

    @property
    def table(self) -> Table:
        return Table(self.driver, self.wait.timeout, self.ITEMS_TABLE)

    @property
    def toast(self) -> Toast:
        return Toast(self.driver, self.wait.timeout)

    @property
    def confirm_dialog(self) -> Modal:
        return Modal(self.driver, self.wait.timeout, by_testid("confirm-dialog"))

    def user_name(self) -> str:
        return self.text_of(self.USER_NAME)

    def create_item(self, name: str):
        self.type(self.ITEM_NAME, name)
        self.click(self.ITEM_CREATE)
        self.wait_until_ready()  # full page round-trip in the demo app
        return self

    def delete_item(self, item_id: int, confirm: bool = True):
        self.click(by_testid(f"item-delete-{item_id}"))
        dialog = self.confirm_dialog
        if confirm:
            dialog.confirm()
            self.wait_until_ready()
        else:
            dialog.cancel()
            dialog.wait_until_gone()
        return self

    def item_names(self) -> list[str]:
        return self.table.column_values("Name") if not self.is_visible(by_testid("items-empty"), 0.5) else []

    def logout(self):
        self.click(self.LOGOUT)
        return self
