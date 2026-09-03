"""Framework exception types. The runner maps them to result statuses:

AssertionFailure -> FAIL   (expected vs actual mismatch: the app or the expectation is wrong)
TestSkipped      -> SKIP   (missing precondition, reported with its reason — never silent)
TestTimeout      -> ERROR  (the per-test watchdog fired; the driver was quit to unblock the run)
HookError        -> ERROR  (setup_module / setup_session failed; every dependent test is ERROR)
anything else    -> ERROR  (locator, timeout, driver, network... needs triage like a failure)
"""


class QAError(Exception):
    """Base class for framework errors."""


class AssertionFailure(QAError):
    """Raised by core.assertions when expected and actual behavior differ."""


class TestSkipped(QAError):
    """Raised via ctx.skip(reason) when a precondition is not available."""


class TestTimeout(QAError):
    """The per-test watchdog expired (see --timeout)."""


class HookError(QAError):
    """A module or session hook failed."""


class PageNotReady(QAError):
    """A page object's readiness check did not pass in time."""


class ConfigurationError(QAError):
    """Settings, discovery or environment problems that prevent running at all."""
