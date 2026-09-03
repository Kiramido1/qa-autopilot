"""WebDriver factory.

- Explicit waits only: the implicit wait is forced to 0 so timeouts are
  deliberate and visible (core/waits.py).
- Driver binaries come from Selenium Manager unless QA_CHROMEDRIVER_PATH /
  QA_GECKODRIVER_PATH point at explicit binaries (offline CI).
- QA_REMOTE_URL switches to a Remote WebDriver (Selenium Grid, BrowserStack,
  Sauce Labs...). QA_MOBILE_DEVICE enables Chrome mobile emulation for the
  responsive checks Gate 1 asks about.
- Downloads go to settings.downloads_dir so download tests can assert on files.
- Chrome/Edge expose the browser console (driver.get_log("browser")) and the
  network log (driver.get_log("performance")) used as failure evidence.
"""

from __future__ import annotations

import json
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
from core.redact import redact_url

SUPPORTED_BROWSERS = ("chrome", "firefox", "edge")


def create_driver(settings, browser: Optional[str] = None, headless: Optional[bool] = None):
    name = (browser or settings.browser).lower()
    headless = settings.headless if headless is None else headless
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    width, height = settings.window_size

    if name == "chrome":
        options = _chrome_options(settings, headless, width, height)
        driver = _remote(settings, options) or _chrome(options)
    elif name == "edge":
        options = _edge_options(settings, headless, width, height)
        driver = _remote(settings, options) or _edge(options)
    elif name == "firefox":
        options = _firefox_options(settings, headless, width, height)
        driver = _remote(settings, options) or _firefox(options)
    else:
        raise ConfigurationError(f"Unsupported browser {name!r}; choose one of {SUPPORTED_BROWSERS}")

    driver.set_page_load_timeout(settings.page_load_timeout)
    driver.implicitly_wait(0)
    if not headless and not settings.mobile_device:
        driver.set_window_size(width, height)
    return driver


def _remote(settings, options):
    if not settings.remote_url:
        return None
    return webdriver.Remote(command_executor=settings.remote_url, options=options)


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
    if settings.mobile_device:
        options.add_experimental_option("mobileEmulation", {"deviceName": settings.mobile_device})
    options.set_capability(logging_key, {"browser": "ALL", "performance": "ALL"})
    return options


def _chrome_options(settings, headless: bool, width: int, height: int):
    options = _chromium_options(ChromeOptions(), settings, headless, width, height, "goog:loggingPrefs")
    binary = os.environ.get("QA_CHROME_BINARY")
    if binary:
        options.binary_location = binary
    return options


def _chrome(options):
    driver_path = os.environ.get("QA_CHROMEDRIVER_PATH")
    service = ChromeService(executable_path=driver_path) if driver_path else None
    return webdriver.Chrome(options=options, service=service)


def _edge_options(settings, headless: bool, width: int, height: int):
    return _chromium_options(EdgeOptions(), settings, headless, width, height, "ms:loggingPrefs")


def _edge(options):
    driver_path = os.environ.get("QA_EDGEDRIVER_PATH")
    service = EdgeService(executable_path=driver_path) if driver_path else None
    return webdriver.Edge(options=options, service=service)


def _firefox_options(settings, headless: bool, width: int, height: int):
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
    return options


def _firefox(options):
    driver_path = os.environ.get("QA_GECKODRIVER_PATH")
    service = FirefoxService(executable_path=driver_path) if driver_path else None
    return webdriver.Firefox(options=options, service=service)


# ---- metadata & evidence ---------------------------------------------------
def driver_metadata(driver) -> dict:
    """Browser name/version and driver version, for the run metadata."""
    caps = getattr(driver, "capabilities", {}) or {}
    name = caps.get("browserName")
    version = caps.get("browserVersion") or caps.get("version")
    driver_version = None
    for key in ("chrome", "msedge"):
        info = caps.get(key)
        if isinstance(info, dict) and info.get("chromedriverVersion"):
            driver_version = info["chromedriverVersion"].split(" ")[0]
    if caps.get("moz:geckodriverVersion"):
        driver_version = caps["moz:geckodriverVersion"]
    return {"name": name, "version": version, "driver_version": driver_version, "platform": caps.get("platformName")}


def browser_console_logs(driver) -> list:
    """Console entries for Chrome/Edge; empty for browsers without get_log support."""
    try:
        return list(driver.get_log("browser"))
    except Exception:  # noqa: BLE001
        return []


def network_events(driver) -> dict:
    """Failed and non-2xx requests from the Chrome/Edge performance log.

    Returns {"total_requests": n, "problems": [{url, method, status, error, type}]}.
    The performance log is drained by get_log, so call this once per failure.
    """
    try:
        entries = driver.get_log("performance")
    except Exception:  # noqa: BLE001 - Firefox / remote grids without the log
        return {"total_requests": 0, "problems": [], "available": False}

    requests: dict[str, dict] = {}
    for entry in entries:
        try:
            message = json.loads(entry["message"])["message"]
        except (KeyError, ValueError, TypeError):
            continue
        method = message.get("method", "")
        params = message.get("params", {})
        request_id = params.get("requestId")
        if not request_id:
            continue
        record = requests.setdefault(request_id, {"url": None, "method": None, "status": None, "error": None, "type": None})
        if method == "Network.requestWillBeSent":
            request = params.get("request", {})
            record["url"] = redact_url(request.get("url"))
            record["method"] = request.get("method")
            record["type"] = params.get("type")
        elif method == "Network.responseReceived":
            response = params.get("response", {})
            record["status"] = response.get("status")
            record["url"] = record["url"] or redact_url(response.get("url"))
            record["type"] = record["type"] or params.get("type")
        elif method == "Network.loadingFailed":
            record["error"] = params.get("errorText") or "loading failed"

    problems = [r for r in requests.values() if r["error"] or (isinstance(r["status"], int) and r["status"] >= 400)]
    return {"total_requests": len(requests), "problems": problems, "available": True}
