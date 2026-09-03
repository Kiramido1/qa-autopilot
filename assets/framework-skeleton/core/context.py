"""The object every test function receives.

Browser, waits and API client are created lazily, so browser-less tests stay
fast and a driver failure is attributed to the test that needed it.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from core.exceptions import TestSkipped
from core.screenshots import take_screenshot


class Credentials(NamedTuple):
    email: str
    password: str


class TestContext:
    def __init__(self, test, settings, artifacts, log):
        self.test = test
        self.settings = settings
        self.artifacts = artifacts
        self.log = log
        self.attachments: list[str] = []
        self._driver = None
        self._waits = None
        self._api = None
        self._cleanups: list[tuple[Callable, tuple, dict]] = []

    # ---- lazily created collaborators ----------------------------------
    @property
    def driver(self):
        if self._driver is None:
            from core.driver import create_driver

            self.log.debug("Starting %s (headless=%s)", self.settings.browser, self.settings.headless)
            self._driver = create_driver(self.settings)
        return self._driver

    @property
    def waits(self):
        if self._waits is None:
            from core.waits import Waits

            self._waits = Waits(self.driver, self.settings.default_timeout)
        return self._waits

    @property
    def api(self):
        if self._api is None:
            from integration.api_client import ApiClient

            self._api = ApiClient(self.settings.api_base_url or self.settings.base_url)
        return self._api

    @property
    def driver_if_created(self):
        return self._driver

    # ---- test helpers --------------------------------------------------
    def skip(self, reason: str) -> None:
        raise TestSkipped(reason)

    def require_credentials(self, role: str = "test_user") -> Credentials:
        email, password = self.settings.credentials(role)
        if not email or not password:
            self.skip(f"no credentials configured for role {role!r} (set the QA_* variables)")
        return Credentials(email, password)

    def add_cleanup(self, fn: Callable, *args, **kwargs) -> None:
        """Register teardown work (delete created records, log out...). Runs LIFO, even after failure."""
        self._cleanups.append((fn, args, kwargs))

    def attach(self, name: str, content) -> Path:
        path = self.artifacts.attach(self.test.id, name, content)
        self.attachments.append(str(path))
        return path

    def screenshot(self, name: str = "screenshot.png") -> Optional[Path]:
        if self._driver is None:
            return None
        path = take_screenshot(self._driver, self.artifacts.test_dir(self.test.id) / name)
        if path:
            self.attachments.append(str(path))
        return path

    def evidence_context(self) -> dict:
        context = {
            "test_id": self.test.id,
            "feature": self.test.feature,
            "priority": self.test.priority,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "browser": self.settings.browser,
            "headless": self.settings.headless,
            "base_url": self.settings.base_url,
        }
        if self._api is not None:
            context["last_api_exchange"] = self._api.last_exchange()
        return context

    def finish(self, log) -> None:
        for fn, args, kwargs in reversed(self._cleanups):
            try:
                fn(*args, **kwargs)
            except Exception as error:  # noqa: BLE001 - cleanup must not change the result
                log.warning("cleanup %s failed: %r", getattr(fn, "__name__", fn), error)
        self._cleanups.clear()
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception as error:  # noqa: BLE001
                log.warning("driver.quit failed: %r", error)
            self._driver = None
            self._waits = None
