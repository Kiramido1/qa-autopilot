"""Failure evidence and attachments for a run.

Every FAIL/ERROR gets a screenshot, page source, current URL, browser console
log, failed/non-2xx network requests, traceback and test context under
reports/<run-id>/artifacts/<test-id>/. Triage (Gate 14) then works from
evidence instead of memory.

Paths in reports are relative to the run directory, so a report uploaded from
CI still points at files that exist next to it.
"""

from __future__ import annotations

import json
import re
import traceback
from pathlib import Path
from typing import Optional, Union

from core.redact import redact_data, redact_text
from core.screenshots import take_screenshot


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unnamed"


class RunArtifacts:
    def __init__(self, reports_dir: Path, run_id: str):
        self.run_id = run_id
        self.root = reports_dir / run_id
        self.artifacts_dir = self.root / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def relative(self, path: Union[Path, str]) -> str:
        path = Path(path)
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def test_dir(self, test_id: str) -> Path:
        directory = self.artifacts_dir / _safe_name(test_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def attach(self, test_id: str, name: str, content: Union[str, bytes, dict, list, None]) -> Path:
        """Save extra evidence a test wants to keep (API payloads, table dumps, ...).

        Dict/list/str content is redacted (password, token, secret... keys) before it is written."""
        path = self.test_dir(test_id) / _safe_name(name)
        if isinstance(content, (dict, list)) or content is None:
            path.write_text(json.dumps(redact_data(content), indent=2, default=str), encoding="utf-8")
        elif isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(redact_text(str(content)) or "", encoding="utf-8")
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
        evidence["exception"] = self._write(directory / f"{prefix}exception.txt", trace)

        if driver is not None:
            shot = take_screenshot(driver, directory / f"{prefix}screenshot.png")
            if shot:
                evidence["screenshot"] = self.relative(shot)
            try:
                url = driver.current_url
                evidence["url"] = url
                self._write(directory / f"{prefix}url.txt", url)
            except Exception as error:  # noqa: BLE001
                evidence["url_error"] = repr(error)
            try:
                evidence["page_source"] = self._write(directory / f"{prefix}page_source.html", driver.page_source)
            except Exception as error:  # noqa: BLE001
                evidence["page_source_error"] = repr(error)
            try:
                logs = driver.get_log("browser")
                evidence["browser_console"] = self._write(
                    directory / f"{prefix}browser_console.json", json.dumps(logs, indent=2, default=str)
                )
            except Exception:  # noqa: BLE001 - Firefox does not support get_log
                pass
            try:
                from core.driver import network_events

                network = network_events(driver)
                if network.get("available"):
                    evidence["network"] = self._write(directory / f"{prefix}network.json", json.dumps(network, indent=2, default=str))
                    evidence["network_problems"] = len(network["problems"])
            except Exception:  # noqa: BLE001
                pass

        if extra:
            evidence["context"] = self._write(directory / f"{prefix}context.json", json.dumps(extra, indent=2, default=str))
        return evidence

    def _write(self, path: Path, content: str) -> str:
        path.write_text(content, encoding="utf-8")
        return self.relative(path)
