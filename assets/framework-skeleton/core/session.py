"""Authenticated-session reuse: log in through the UI once per role, then
inject cookies + web storage into later tests.

Cuts runtime and removes one whole class of flakiness (every test re-driving
the login form). Disabled with --fresh-session for tests that are *about*
logging in.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

_STORAGE_DUMP = """
const dump = (s) => { const o = {}; for (let i = 0; i < s.length; i++) { const k = s.key(i); o[k] = s.getItem(k); } return o; };
return {local: dump(window.localStorage), session: dump(window.sessionStorage)};
"""
_STORAGE_RESTORE = """
const [local, session] = arguments;
window.localStorage.clear(); window.sessionStorage.clear();
for (const [k, v] of Object.entries(local)) window.localStorage.setItem(k, v);
for (const [k, v] of Object.entries(session)) window.sessionStorage.setItem(k, v);
"""


class SessionStore:
    """Per-process cache of captured browser states keyed by role."""

    def __init__(self) -> None:
        self._states: dict[str, dict] = {}

    def has(self, role: str) -> bool:
        return role in self._states

    def get(self, role: str) -> Optional[dict]:
        return self._states.get(role)

    def put(self, role: str, state: dict) -> None:
        self._states[role] = state

    def clear(self) -> None:
        self._states.clear()


_COOKIE_KEYS = ("name", "value", "path", "domain", "secure", "httpOnly", "expiry", "sameSite")


def sanitize_cookie(cookie: dict) -> dict:
    """A cookie as the browser reported it, reduced to what add_cookie() accepts everywhere.

    Firefox reports SameSite=None for cookies the server set without a SameSite
    attribute, then refuses to re-add such a cookie over plain HTTP unless it is
    Secure ("rejected because it has the SameSite=None attribute but is missing
    the secure attribute", Firefox 154+). Dropping the attribute restores the
    browser default, which is what the server asked for in the first place.
    """
    clean = {k: v for k, v in cookie.items() if k in _COOKIE_KEYS}
    if clean.get("expiry") is not None:
        clean["expiry"] = int(clean["expiry"])
    same_site = clean.get("sameSite")
    if same_site not in ("Strict", "Lax", "None") or (same_site == "None" and not clean.get("secure")):
        clean.pop("sameSite", None)
    return clean


def capture_state(driver) -> dict:
    cookies = [sanitize_cookie(cookie) for cookie in driver.get_cookies()]
    try:
        storage = driver.execute_script(_STORAGE_DUMP) or {}
    except Exception:  # noqa: BLE001 - about:blank / sandboxed pages
        storage = {}
    return {"url": driver.current_url, "cookies": cookies, "local": storage.get("local", {}), "session": storage.get("session", {})}


def restore_state(driver, base_url: str, state: dict) -> None:
    driver.get(base_url)  # cookies can only be added for the current origin
    driver.delete_all_cookies()
    for cookie in state.get("cookies", []):
        try:
            driver.add_cookie(cookie)
        except Exception:  # noqa: BLE001 - domain mismatch / attribute rejected: retry with the minimal cookie
            driver.add_cookie({k: v for k, v in cookie.items() if k not in ("domain", "sameSite", "expiry")})
    try:
        driver.execute_script(_STORAGE_RESTORE, state.get("local", {}), state.get("session", {}))
    except Exception:  # noqa: BLE001
        pass
    driver.get(state.get("url") or base_url)


def login_once(
    store: SessionStore,
    driver,
    base_url: str,
    role: str,
    login: Callable[[], None],
    fresh: bool = False,
) -> bool:
    """Reuse the captured state for `role` when available; otherwise run `login` and capture it.

    Returns True when the cached session was reused.
    """
    cached = store.get(role)
    if not fresh and cached is not None:
        restore_state(driver, base_url, cached)
        return True
    login()
    store.put(role, capture_state(driver))
    return False
