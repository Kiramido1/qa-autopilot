"""Locator helpers in Gate 7 priority order: test id > semantic > text.

    from core.locators import by_testid, by_role, by_label
    SUBMIT = by_testid("login-submit")

The test-id attribute name is configurable (QA_TESTID_ATTRIBUTE, default
data-testid) because projects use data-test, data-cy, data-qa...
"""

from __future__ import annotations

import os

from selenium.webdriver.common.by import By

Locator = tuple[str, str]


def testid_attribute() -> str:
    return os.environ.get("QA_TESTID_ATTRIBUTE", "data-testid")


def by_testid(value: str, attribute: str | None = None) -> Locator:
    return (By.CSS_SELECTOR, f"[{attribute or testid_attribute()}='{value}']")


def by_role(role: str, name: str | None = None) -> Locator:
    """ARIA role, optionally with accessible name (aria-label or visible text)."""
    if name is None:
        return (By.CSS_SELECTOR, f"[role='{role}']")
    quoted = _xpath_literal(name)
    return (By.XPATH, f"//*[@role={_xpath_literal(role)} and (@aria-label={quoted} or normalize-space(.)={quoted})]")


def by_label(text: str) -> Locator:
    """Form control associated with a <label> whose text matches."""
    quoted = _xpath_literal(text)
    return (
        By.XPATH,
        f"//*[self::input or self::select or self::textarea][@id=//label[normalize-space(.)={quoted}]/@for]"
        f" | //label[normalize-space(.)={quoted}]//*[self::input or self::select or self::textarea]",
    )


def by_text(text: str, tag: str = "*") -> Locator:
    """Element by exact visible text — only when the text is the thing under test (Gate 7)."""
    return (By.XPATH, f"//{tag}[normalize-space(.)={_xpath_literal(text)}]")


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ', "\'", '.join(f"'{p}'" for p in parts) + ")"
