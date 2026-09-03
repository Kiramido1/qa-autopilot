"""Assertions that raise AssertionFailure with expected-vs-actual evidence.

Keep assertions strong: a weakened or removed assertion hides defects, which
is exactly what this framework exists to surface.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from core.exceptions import AssertionFailure


def fail(message: str) -> None:
    raise AssertionFailure(message)


def _detail(message: str, expected: Any, actual: Any) -> str:
    return f"{message}\n  expected: {expected!r}\n  actual:   {actual!r}"


def assert_true(condition: Any, message: str) -> None:
    if not condition:
        raise AssertionFailure(_detail(message, True, condition))


def assert_false(condition: Any, message: str) -> None:
    if condition:
        raise AssertionFailure(_detail(message, False, condition))


def assert_equal(actual: Any, expected: Any, message: str = "values differ") -> None:
    if actual != expected:
        raise AssertionFailure(_detail(message, expected, actual))


def assert_not_equal(actual: Any, unexpected: Any, message: str = "values should differ") -> None:
    if actual == unexpected:
        raise AssertionFailure(_detail(message, f"anything but {unexpected!r}", actual))


def assert_in(member: Any, container: Iterable, message: str = "member not found") -> None:
    if member not in container:
        raise AssertionFailure(_detail(message, f"{member!r} in container", container))


def assert_not_in(member: Any, container: Iterable, message: str = "unexpected member") -> None:
    if member in container:
        raise AssertionFailure(_detail(message, f"{member!r} not in container", container))


def assert_matches(text: str, pattern: str, message: str = "text does not match") -> None:
    if not re.search(pattern, text or ""):
        raise AssertionFailure(_detail(message, f"match /{pattern}/", text))


def assert_url_contains(driver, fragment: str, message: str = "unexpected URL") -> None:
    url = driver.current_url
    if fragment not in url:
        raise AssertionFailure(_detail(message, f"url containing {fragment!r}", url))


def assert_visible(page, locator, message: str = "element not visible", timeout: float = 5.0) -> None:
    if not page.is_visible(locator, timeout):
        raise AssertionFailure(_detail(message, f"visible {locator}", "not visible within timeout"))


def assert_status(response, expected: int, message: str = "unexpected HTTP status") -> None:
    if response.status_code != expected:
        body = response.text[:500] if hasattr(response, "text") else ""
        raise AssertionFailure(
            _detail(f"{message} for {response.request.method} {response.url}", expected, response.status_code) + f"\n  body:     {body!r}"
        )
