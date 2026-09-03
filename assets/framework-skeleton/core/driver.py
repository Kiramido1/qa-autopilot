"""WebDriver factory.

- Explicit waits only: the implicit wait is forced to 0 so timeouts are
  deliberate and visible (core/waits.py).
- Driver binaries come from Selenium Manager unless QA_CHROMEDRIVER_PATH /
  QA_GECKODRIVER_PATH point at explicit binaries (offline CI).
- Downloads go to settings.downloads_dir so download tests can assert on files.
- Chrome/Edge expose the browser console through driver.get_log("browser").
"""
from __future__ import annotations

import os
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from core.exceptions import ConfigurationError

SUPPORTED_BROWSERS = ("chrome", "firefox", "edge")


def create_driver(settings, browser: Optional[str] = None, headless: Optional[bool] = None):
    name = (browser or settings.browser).lower()
    headless = settings.headless if headless is None else headless
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    width, height = settings.window_size

    if name == "chrome":
        driver = _chrome(settings, headless, width, height)
    elif name == "edge":
        driver = _edge(settings, headless, width, height)
    elif name == "firefox":
        driver = _firefox(settings, headless, width, height)
    else:
        raise ConfigurationError(f"Unsupported browser {name!r}; choose one of {SUPPORTED_BROWSERS}")

    driver.set_page_load_timeout(settings.page_load_timeout)
    driver.implicitly_wait(0)
    if not headless:
        driver.set_window_size(width, height)
    return driver


def _chromium_options(options, settings, headless: bool, width: int, height: int, logging_key: str):
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    if os.environ.get("QA_CHROME_NO_SANDBOX", "").lower() in ("1", "true", "yes"):
        options.add_argument("--no-sandbox")
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(settings.downloads_dir),
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True,
        },
    )
    options.set_capability(logging_key, {"browser": "ALL"})
    return options


def _chrome(settings, headless: bool, width: int, height: int):
    options = _chromium_options(ChromeOptions(), settings, headless, width, height, "goog:loggingPrefs")
    binary = os.environ.get("QA_CHROME_BINARY")
    if binary:
        options.binary_location = binary
    driver_path = os.environ.get("QA_CHROMEDRIVER_PATH")
    service = ChromeService(executable_path=driver_path) if driver_path else None
    return webdriver.Chrome(options=options, service=service)


def _edge(settings, headless: bool, width: int, height: int):
    options = _chromium_options(EdgeOptions(), settings, headless, width, height, "ms:loggingPrefs")
    driver_path = os.environ.get("QA_EDGEDRIVER_PATH")
    service = EdgeService(executable_path=driver_path) if driver_path else None
    return webdriver.Edge(options=options, service=service)


def _firefox(settings, headless: bool, width: int, height: int):
    options = FirefoxOptions()
    if headless:
        options.add_argument("-headless")
    options.add_argument(f"--width={width}")
    options.add_argument(f"--height={height}")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", str(settings.downloads_dir))
    options.set_preference("browser.download.useDownloadDir", True)
    binary = os.environ.get("QA_FIREFOX_BINARY")
    if binary:
        options.binary_location = binary
    driver_path = os.environ.get("QA_GECKODRIVER_PATH")
    service = FirefoxService(executable_path=driver_path) if driver_path else None
    return webdriver.Firefox(options=options, service=service)


def browser_console_logs(driver) -> list:
    """Console entries for Chrome/Edge; empty for browsers without get_log support."""
    try:
        return list(driver.get_log("browser"))
    except Exception:  # noqa: BLE001
        return []
