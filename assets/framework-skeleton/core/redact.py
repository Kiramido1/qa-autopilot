"""Redaction of secrets in evidence.

Headers, JSON/form bodies, query strings and free text all pass through here
before they are written to a report. Rule 15 wants API evidence attached to
every conclusion; this module is what makes attaching it safe.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REDACTED = "<redacted>"

SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
    "x-xsrf-token",
}

# Any key (JSON field, form field, query parameter) matching this is redacted.
SENSITIVE_KEY = re.compile(
    r"(pass(word|wd|phrase)?|pwd|secret|token|auth(orization)?|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|session(id)?|cookie|credential|otp|pin)",
    re.IGNORECASE,
)

# key: "value" / key=value / "key": value inside otherwise unparsable text.
_TEXT_PATTERN = re.compile(
    r"(?P<key>\"?[A-Za-z0-9_.-]*"
    r"(?:pass(?:word|wd|phrase)?|pwd|secret|token|authorization|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"client[_-]?secret|credential|otp)"
    r"[A-Za-z0-9_.-]*\"?\s*[:=]\s*)"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^&\s,}\]]+)",
    re.IGNORECASE,
)


def is_sensitive_key(key: Any) -> bool:
    return bool(SENSITIVE_KEY.search(str(key)))


def redact_headers(headers: Mapping[str, Any] | None) -> dict:
    if not headers:
        return {}
    return {k: (REDACTED if k.lower() in SENSITIVE_HEADERS or is_sensitive_key(k) else v) for k, v in headers.items()}


def redact_url(url: str | None) -> str | None:
    """Redact sensitive query parameters (token=, api_key=, password=...)."""
    if not url:
        return url
    parts = urlsplit(url)
    if not parts.query:
        return url
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    cleaned = [(k, REDACTED if is_sensitive_key(k) else v) for k, v in pairs]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(cleaned), parts.fragment))


def redact_data(value: Any) -> Any:
    """Recursively redact dict keys that look sensitive."""
    if isinstance(value, Mapping):
        return {k: (REDACTED if is_sensitive_key(k) else redact_data(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_data(v) for v in value]
    return value


def redact_text(text: str | None) -> str | None:
    if not text:
        return text
    return _TEXT_PATTERN.sub(lambda m: f"{m.group('key')}{REDACTED}", text)


def redact_body(body: Any, limit: int = 2000) -> Any:
    """Redact a request/response body of unknown shape, then truncate."""
    if body is None:
        return None
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            return f"<{len(body)} bytes>"
    if isinstance(body, (dict, list)):
        return redact_data(body)
    text = str(body)
    stripped = text.strip()
    if stripped[:1] in ("{", "["):
        try:
            return redact_data(json.loads(stripped))
        except ValueError:
            pass
    if "=" in stripped and "&" in stripped and " " not in stripped and "\n" not in stripped:
        pairs = parse_qsl(stripped, keep_blank_values=True)
        if pairs:
            return urlencode([(k, REDACTED if is_sensitive_key(k) else v) for k, v in pairs])
    redacted = redact_text(text) or ""
    return redacted[:limit] + ("…" if len(redacted) > limit else "")
