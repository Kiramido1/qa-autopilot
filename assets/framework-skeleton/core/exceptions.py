"""Framework exception types. The runner maps them to result statuses:

  AssertionFailure -> FAIL   (expected vs actual mismatch: the app or the expectation is wrong)
  TestSkipped      -> SKIP   (missing precondition, reported with its reason — never silent)
  anything else    -> ERROR  (locator, timeout, driver, network... needs triage like a failure)
"""


class QAError(Exception):
    """Base class for framework errors."""


class AssertionFailure(QAError):
    """Raised by core.assertions when expected and actual behavior differ."""


class TestSkipped(QAError):
    """Raised via ctx.skip(reason) when a precondition is not available."""


class PageNotReady(QAError):
    """A page object's readiness check did not pass in time."""


class ConfigurationError(QAError):
    """Settings, discovery or environment problems that prevent running at all."""
