"""Failure evidence and attachments for a run.

Every FAIL/ERROR gets a screenshot, page source, current URL, browser console
log, traceback and test context under reports/<run-id>/artifacts/<test-id>/.
Triage (Gate 14) then works from evidence instead of memory.
"""
from __future__ import annotations

import json
import re
import traceback
from pathlib import Path
from typing import Optional, Union

from core.screenshots import take_screenshot


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unnamed"


class RunArtifacts:
    def __init__(self, reports_dir: Path, run_id: str):
        self.run_id = run_id
        self.root = reports_dir / run_id
        self.artifacts_dir = self.root / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def test_dir(self, test_id: str) -> Path:
        directory = self.artifacts_dir / _safe_name(test_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def attach(self, test_id: str, name: str, content: Union[str, bytes, dict, list]) -> Path:
        """Save extra evidence a test wants to keep (API payloads, table dumps, ...)."""
        path = self.test_dir(test_id) / _safe_name(name)
        if isinstance(content, (dict, list)):
            path.write_text(json.dumps(content, indent=2, default=str), encoding="utf-8")
        elif isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(str(content), encoding="utf-8")
        return path

    def capture_failure(
        self,
        test_id: str,
        driver,
        exc: BaseException,
        attempt: int = 1,
        extra: Optional[dict] = None,
    ) -> dict:
        """Collect everything useful about a failure. Each capture is independent,
        so a dead browser session cannot hide the exception that caused the failure."""
        directory = self.test_dir(test_id)
        prefix = f"attempt{attempt}-"
        evidence: dict = {}

        trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        evidence["exception"] = str(self._write(directory / f"{prefix}exception.txt", trace))

        if driver is not None:
            shot = take_screenshot(driver, directory / f"{prefix}screenshot.png")
            if shot:
                evidence["screenshot"] = str(shot)
            try:
                url = driver.current_url
                evidence["url"] = url
                self._write(directory / f"{prefix}url.txt", url)
            except Exception as error:  # noqa: BLE001
                evidence["url_error"] = repr(error)
            try:
                evidence["page_source"] = str(self._write(directory / f"{prefix}page_source.html", driver.page_source))
            except Exception as error:  # noqa: BLE001
                evidence["page_source_error"] = repr(error)
            try:
                logs = driver.get_log("browser")
                evidence["browser_console"] = str(
                    self._write(directory / f"{prefix}browser_console.json", json.dumps(logs, indent=2, default=str))
                )
            except Exception:  # noqa: BLE001 - Firefox does not support get_log
                pass

        if extra:
            evidence["context"] = str(
                self._write(directory / f"{prefix}context.json", json.dumps(extra, indent=2, default=str))
            )
        return evidence

    @staticmethod
    def _write(path: Path, content: str) -> Path:
        path.write_text(content, encoding="utf-8")
        return path
