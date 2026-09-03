"""Thin HTTP client for integration checks (Python requests -> API -> backend -> DB).

Use it where an API call gives stronger, faster evidence than a browser test:
auth behavior, authorization boundaries, contract checks, data setup/cleanup,
and confirming what the backend returned when the UI shows something odd.
Every exchange is recorded with secrets redacted (headers, bodies and query
strings — see core/redact.py) so it can be attached as evidence.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import requests

from core.redact import redact_body, redact_headers, redact_url


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 15.0, history: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._history: deque = deque(maxlen=history)

    # ---- auth ------------------------------------------------------------
    def set_bearer_token(self, token: Optional[str]) -> None:
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.session.headers.pop("Authorization", None)

    def set_cookies_from_driver(self, driver) -> None:
        """Reuse the browser's authenticated session for API evidence of what the UI just did."""
        for cookie in driver.get_cookies():
            self.session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain"), path=cookie.get("path", "/"))

    # ---- requests --------------------------------------------------------
    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.request(method.upper(), url, **kwargs)
        self._history.append(self._record(response))
        return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self.session.close()

    # ---- evidence --------------------------------------------------------
    def last_exchange(self) -> Optional[dict]:
        return self._history[-1] if self._history else None

    def history(self) -> list[dict]:
        return list(self._history)

    @staticmethod
    def _record(response: requests.Response, body_limit: int = 2000) -> dict:
        request = response.request
        return {
            "method": request.method,
            "url": redact_url(request.url),
            "request_headers": redact_headers(request.headers),
            "request_body": redact_body(request.body, body_limit),
            "status": response.status_code,
            "elapsed_ms": round(response.elapsed.total_seconds() * 1000),
            "response_headers": redact_headers(response.headers),
            "response_body": redact_body(response.text, body_limit),
        }
