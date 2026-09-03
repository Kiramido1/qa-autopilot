"""The objects tests and hooks receive.

TestContext: browser, waits and API client are created lazily, so browser-less
tests stay fast and a driver failure is attributed to the test that needed it.
SessionContext / ModuleContext: what setup_session / setup_module receive,
with a `store` dict that tests read through ctx.session.store / ctx.module.store.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, Optional

from core.exceptions import TestSkipped
from core.screenshots import take_screenshot
from core.session import SessionStore, login_once
from core.trace import set_tracer


class Credentials(NamedTuple):
    email: str
    password: str


class _HookContext:
    """Shared base for session/module hook contexts."""

    def __init__(self, settings, artifacts, log, store: Optional[dict] = None):
        self.settings = settings
        self.artifacts = artifacts
        self.log = log
        self.store: dict = store if store is not None else {}
        self._api: Any = None
        self._cleanups: list[tuple[Callable, tuple, dict]] = []

    @property
    def api(self):
        if self._api is None:
            from integration.api_client import ApiClient

            self._api = ApiClient(self.settings.api_base_url or self.settings.base_url)
        return self._api

    def add_cleanup(self, fn: Callable, *args, **kwargs) -> None:
        self._cleanups.append((fn, args, kwargs))

    def run_cleanups(self, log) -> None:
        for fn, args, kwargs in reversed(self._cleanups):
            try:
                fn(*args, **kwargs)
            except Exception as error:  # noqa: BLE001
                log.warning("cleanup %s failed: %r", getattr(fn, "__name__", fn), error)
        self._cleanups.clear()


class SessionContext(_HookContext):
    """Given to setup_session/teardown_session; one per run (per worker in --parallel)."""

    def __init__(self, settings, artifacts, log, store: Optional[dict] = None):
        super().__init__(settings, artifacts, log, store)
        self.sessions = SessionStore()  # login_once() cache


class ModuleContext(_HookContext):
    """Given to setup_module/teardown_module; one per test module."""

    def __init__(self, name: str, session: SessionContext, log):
        super().__init__(session.settings, session.artifacts, log)
        self.name = name
        self.session = session


class TestContext:
    def __init__(self, test, settings, artifacts, log, session: Optional[SessionContext] = None, module: Optional[ModuleContext] = None):
        self.test = test
        self.settings = settings
        self.artifacts = artifacts
        self.log = log
        self.session = session or SessionContext(settings, artifacts, log)
        self.module = module
        self.attachments: list[str] = []
        self.observations: dict = {}
        self.trace_files: list[str] = []
        self.browser_info: Optional[dict] = None
        self.aborted: Optional[str] = None
        self._driver: Any = None
        self._waits: Any = None
        self._api: Any = None
        self._cleanups: list[tuple[Callable, tuple, dict]] = []
        self._lock = threading.Lock()
        self._trace_count = 0

    # ---- lazily created collaborators ----------------------------------
    @property
    def driver(self):
        if self._driver is None:
            from core.driver import create_driver, driver_metadata

            self.log.debug("Starting %s (headless=%s)", self.settings.browser, self.settings.headless)
            self._driver = create_driver(self.settings)
            self.browser_info = driver_metadata(self._driver)
            if self.settings.trace:
                set_tracer(self._trace_screenshot)
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
    def skip(self, reason: str) -> NoReturn:
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
        self.attachments.append(self.artifacts.relative(path))
        return path

    def screenshot(self, name: str = "screenshot.png") -> Optional[Path]:
        if self._driver is None:
            return None
        path = take_screenshot(self._driver, self.artifacts.test_dir(self.test.id) / name)
        if path:
            self.attachments.append(self.artifacts.relative(path))
        return path

    def login_once(self, role: str, login: Callable[[], None]) -> bool:
        """Log in through the UI once per role per run, then reuse cookies/storage (see core/session.py).

        `login` is a zero-argument callable that drives the real login UI, e.g.
            ctx.login_once("test_user", lambda: flows.authentication.login(ctx.driver, ctx.settings, *creds))
        Returns True when a cached session was injected instead. --fresh-session disables reuse.
        """
        reused = login_once(self.session.sessions, self.driver, self.settings.base_url, role, login, self.settings.fresh_session)
        self.log.debug("session for %s: %s", role, "reused" if reused else "created")
        return reused

    def observe(self, name: str, value) -> None:
        """Record an observation (non-failing finding) in the result, e.g. accessibility notes."""
        self.observations[name] = value

    def a11y_scan(self, name: str = "a11y.json", context: Optional[str] = None) -> dict:
        """Run axe-core on the current page; observations only, never a failure."""
        from core.a11y import run_axe

        result = run_axe(self.driver, self.settings.reports_dir.parent / ".cache", context)
        self.attach(name, result)
        self.observe("a11y", {"violations": len(result.get("violations", [])), "summary": result.get("summary"), "file": name})
        return result

    # ---- runner hooks --------------------------------------------------
    def _trace_screenshot(self, action: str, detail: str) -> None:
        if self._driver is None:
            return
        self._trace_count += 1
        safe = "".join(c if c.isalnum() else "_" for c in detail)[:40]
        path = self.artifacts.test_dir(self.test.id) / "trace" / f"{self._trace_count:03d}-{action}-{safe}.png"
        if take_screenshot(self._driver, path):
            self.trace_files.append(self.artifacts.relative(path))

    def abort(self, reason: str) -> None:
        """Called by the watchdog: quit the driver so a hung test raises and the run continues."""
        with self._lock:
            self.aborted = reason
            driver, self._driver = self._driver, None
        if driver is not None:
            try:
                driver.quit()
            except Exception:  # noqa: BLE001
                pass

    def evidence_context(self) -> dict:
        context = {
            "test_id": self.test.id,
            "feature": self.test.feature,
            "priority": self.test.priority,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "browser": self.settings.browser,
            "browser_info": self.browser_info,
            "headless": self.settings.headless,
            "base_url": self.settings.base_url,
            "aborted": self.aborted,
        }
        if self._api is not None:
            context["last_api_exchange"] = self._api.last_exchange()
        return context

    def finish(self, log) -> None:
        set_tracer(None)
        for fn, args, kwargs in reversed(self._cleanups):
            try:
                fn(*args, **kwargs)
            except Exception as error:  # noqa: BLE001 - cleanup must not change the result
                log.warning("cleanup %s failed: %r", getattr(fn, "__name__", fn), error)
        self._cleanups.clear()
        with self._lock:
            driver, self._driver = self._driver, None
        if driver is not None:
            try:
                driver.quit()
            except Exception as error:  # noqa: BLE001
                log.warning("driver.quit failed: %r", error)
        self._waits = None
