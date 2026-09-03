"""Screenshot helper that never masks the original failure."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def take_screenshot(driver, path: Path) -> Optional[Path]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(path))
        return path
    except Exception:  # noqa: BLE001 - a dead driver must not hide the real error
        return None
