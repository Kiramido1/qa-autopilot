"""File upload via the real <input type=file> (send_keys), the way Selenium supports it.

The input is often hidden behind a styled button; send_keys works on hidden
file inputs, so no JavaScript is needed to un-hide it.
"""

from __future__ import annotations

from pathlib import Path

from selenium.webdriver.common.by import By

from components.base_component import BaseComponent
from core.trace import trace


class FileUploader(BaseComponent):
    root_locator = (By.CSS_SELECTOR, "[data-testid='file-uploader']")
    INPUT = (By.CSS_SELECTOR, "input[type='file']")
    UPLOADED = (By.CSS_SELECTOR, "[data-testid='uploaded-file']")

    def upload(self, *paths: str | Path):
        resolved = [str(Path(p).resolve()) for p in paths]
        for p in resolved:
            if not Path(p).is_file():
                raise FileNotFoundError(p)
        self.wait.present(self.INPUT).send_keys("\n".join(resolved))
        trace("upload", ", ".join(Path(p).name for p in resolved))
        return self

    def uploaded_names(self) -> list[str]:
        return [e.text.strip() for e in self.find_all(self.UPLOADED)]

    def wait_for_uploaded(self, name: str, timeout: float | None = None):
        return self.wait.until(lambda d: name in self.uploaded_names(), f"uploaded file {name!r} listed", timeout)
