"""Explicit, named waits. No sleep-based synchronization anywhere in the framework.

Every wait describes the state it is waiting for, and a timeout raises a
TimeoutException that names that state and the current URL — so a
SYNCHRONIZATION_FAILURE is distinguishable from a real defect during triage.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]


def describe(locator: Locator) -> str:
    return f"{locator[0]}={locator[1]!r}"


class Waits:
    def __init__(self, driver, timeout: float = 10.0, poll: float = 0.25):
        self.driver = driver
        self.timeout = timeout
        self.poll = poll

    # ---- core ---------------------------------------------------------
    def until(self, condition: Callable, message: str, timeout: Optional[float] = None):
        limit = self.timeout if timeout is None else timeout
        try:
            return WebDriverWait(self.driver, limit, poll_frequency=self.poll).until(condition)
        except TimeoutException as error:
            raise TimeoutException(f"{message} (waited {limit}s; url={self._url()})") from error

    def _url(self) -> str:
        try:
            return self.driver.current_url
        except Exception:  # noqa: BLE001
            return "<unavailable>"

    # ---- elements -----------------------------------------------------
    def present(self, locator: Locator, timeout: Optional[float] = None):
        return self.until(EC.presence_of_element_located(locator), f"element present: {describe(locator)}", timeout)

    def visible(self, locator: Locator, timeout: Optional[float] = None):
        return self.until(EC.visibility_of_element_located(locator), f"element visible: {describe(locator)}", timeout)

    def clickable(self, locator: Locator, timeout: Optional[float] = None):
        return self.until(EC.element_to_be_clickable(locator), f"element clickable: {describe(locator)}", timeout)

    def absent(self, locator: Locator, timeout: Optional[float] = None) -> bool:
        return self.until(EC.invisibility_of_element_located(locator), f"element absent: {describe(locator)}", timeout)

    def all_visible(self, locator: Locator, timeout: Optional[float] = None) -> list:
        return self.until(EC.visibility_of_all_elements_located(locator), f"elements visible: {describe(locator)}", timeout)

    def count_at_least(self, locator: Locator, minimum: int, timeout: Optional[float] = None) -> list:
        def enough(driver):
            found = driver.find_elements(*locator)
            return found if len(found) >= minimum else False

        return self.until(enough, f"at least {minimum} element(s): {describe(locator)}", timeout)

    def text_present(self, locator: Locator, text: str, timeout: Optional[float] = None) -> bool:
        return self.until(EC.text_to_be_present_in_element(locator, text), f"text {text!r} in {describe(locator)}", timeout)

    def attribute_equals(self, locator: Locator, attribute: str, value: str, timeout: Optional[float] = None):
        def matches(driver):
            element = driver.find_element(*locator)
            return element if element.get_attribute(attribute) == value else False

        return self.until(matches, f"{describe(locator)}[{attribute}] == {value!r}", timeout)

    def loading_gone(self, locator: Locator, timeout: Optional[float] = None) -> bool:
        """Wait for a spinner / skeleton / progress indicator to disappear."""
        return self.absent(locator, timeout)

    # ---- navigation ---------------------------------------------------
    def page_ready(self, timeout: Optional[float] = None) -> bool:
        return self.until(lambda d: d.execute_script("return document.readyState") == "complete", "document.readyState complete", timeout)

    def url_contains(self, fragment: str, timeout: Optional[float] = None) -> bool:
        return self.until(EC.url_contains(fragment), f"url contains {fragment!r}", timeout)

    def url_changes(self, old_url: str, timeout: Optional[float] = None) -> bool:
        return self.until(EC.url_changes(old_url), f"url changes from {old_url!r}", timeout)

    def title_contains(self, text: str, timeout: Optional[float] = None) -> bool:
        return self.until(EC.title_contains(text), f"title contains {text!r}", timeout)

    def frame(self, locator: Locator, timeout: Optional[float] = None):
        """Wait for an iframe and switch into it. Call driver.switch_to.default_content() afterwards."""
        return self.until(EC.frame_to_be_available_and_switch_to_it(locator), f"frame available: {describe(locator)}", timeout)

    def alert(self, timeout: Optional[float] = None):
        return self.until(EC.alert_is_present(), "alert present", timeout)
