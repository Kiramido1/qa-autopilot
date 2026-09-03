"""Optional action tracing (--trace): a screenshot after every page action.

Page objects call trace("click", detail); the runner installs a tracer per
attempt that writes reports/<run>/artifacts/<test>/trace/NNN-action.png.
Off by default because it is slow; turn it on for a failure the normal
artifacts cannot explain.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

_tracer: Optional[Callable[[str, str], None]] = None


def set_tracer(tracer: Optional[Callable[[str, str], None]]) -> None:
    global _tracer
    _tracer = tracer


def trace(action: str, detail: str = "") -> None:
    if _tracer is None:
        return
    try:
        _tracer(action, detail)
    except Exception:  # noqa: BLE001 - tracing must never change a result
        pass
