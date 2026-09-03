"""Runtime settings for the QA framework.

Precedence (highest first):
  CLI flags -> environment variables -> qa/.env -> config/environments.py defaults.

Secrets (test credentials) come only from environment variables or the .env
file. They are never hardcoded and never written into reports (see redacted()).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from config.environments import DEFAULT_ENV, ENVIRONMENTS

QA_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE lines, # comments). Real env vars win."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _bool(value: Optional[str], default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _size(value: Optional[str], default=(1440, 900)) -> tuple[int, int]:
    if not value:
        return default
    try:
        width, height = value.lower().split("x")
        return int(width), int(height)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    env_name: str
    base_url: str
    api_base_url: str
    api_health_path: str
    browser: str
    headless: bool
    default_timeout: float
    page_load_timeout: float
    window_size: tuple[int, int]
    reports_dir: Path
    downloads_dir: Path
    test_user_email: Optional[str]
    test_user_password: Optional[str]
    admin_email: Optional[str]
    admin_password: Optional[str]

    def credentials(self, role: str) -> tuple[Optional[str], Optional[str]]:
        if role == "test_user":
            return self.test_user_email, self.test_user_password
        if role == "admin":
            return self.admin_email, self.admin_password
        raise ValueError(f"Unknown credential role: {role!r}")

    def redacted(self) -> dict:
        """Settings safe to write into reports: no credentials."""
        return {
            "env_name": self.env_name,
            "base_url": self.base_url,
            "api_base_url": self.api_base_url,
            "browser": self.browser,
            "headless": self.headless,
            "default_timeout": self.default_timeout,
            "page_load_timeout": self.page_load_timeout,
            "window_size": "x".join(str(v) for v in self.window_size),
            "reports_dir": str(self.reports_dir),
            "test_user_configured": bool(self.test_user_email and self.test_user_password),
            "admin_configured": bool(self.admin_email and self.admin_password),
        }


def load_settings(**overrides) -> Settings:
    """Build Settings. Keyword overrides with value None are ignored."""
    _load_dotenv(QA_ROOT / ".env")
    env = os.environ
    env_name = overrides.pop("env_name", None) or env.get("QA_ENV") or DEFAULT_ENV
    defaults = ENVIRONMENTS.get(env_name, {})

    reports_dir = Path(overrides.pop("reports_dir", None) or env.get("QA_REPORTS_DIR") or "reports")
    if not reports_dir.is_absolute():
        reports_dir = QA_ROOT / reports_dir

    settings = Settings(
        env_name=env_name,
        base_url=(env.get("QA_BASE_URL") or defaults.get("base_url") or "").rstrip("/"),
        api_base_url=(env.get("QA_API_BASE_URL") or defaults.get("api_base_url") or "").rstrip("/"),
        api_health_path=env.get("QA_API_HEALTH_PATH") or defaults.get("api_health_path") or "/health",
        browser=(env.get("QA_BROWSER") or "chrome").lower(),
        headless=_bool(env.get("QA_HEADLESS"), True),
        default_timeout=float(env.get("QA_TIMEOUT") or 10),
        page_load_timeout=float(env.get("QA_PAGE_LOAD_TIMEOUT") or 30),
        window_size=_size(env.get("QA_WINDOW_SIZE")),
        reports_dir=reports_dir,
        downloads_dir=reports_dir / "downloads",
        test_user_email=env.get("QA_TEST_USER_EMAIL") or None,
        test_user_password=env.get("QA_TEST_USER_PASSWORD") or None,
        admin_email=env.get("QA_ADMIN_EMAIL") or None,
        admin_password=env.get("QA_ADMIN_PASSWORD") or None,
    )
    clean = {key: value for key, value in overrides.items() if value is not None}
    if "base_url" in clean:
        clean["base_url"] = clean["base_url"].rstrip("/")
    if "api_base_url" in clean:
        clean["api_base_url"] = clean["api_base_url"].rstrip("/")
    return replace(settings, **clean) if clean else settings
