"""Thin HTTP client for integration checks (Python requests -> API -> backend -> DB).

Use it where an API call gives stronger, faster evidence than a browser test:
auth behavior, authorization boundaries, contract checks, data setup/cleanup,
and confirming what the backend returned when the UI shows something odd.
Every exchange is recorded (with secrets redacted) so it can be attached as evidence.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

import requests

REDACTED_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


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
            "url": request.url,
            "request_headers": {
                k: ("<redacted>" if k.lower() in REDACTED_HEADERS else v) for k, v in request.headers.items()
            },
            "request_body": (request.body[:body_limit] if isinstance(request.body, (str, bytes)) else request.body),
            "status": response.status_code,
            "elapsed_ms": round(response.elapsed.total_seconds() * 1000),
            "response_headers": {
                k: ("<redacted>" if k.lower() in REDACTED_HEADERS else v) for k, v in response.headers.items()
            },
            "response_body": response.text[:body_limit],
        }
