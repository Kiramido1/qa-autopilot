"""Test registry: the @test decorator and the metadata the runner uses.

Every test declares an ID, feature, priority and tags up front so the runner
can select by risk (P0 first), build the traceability matrix and produce
evidence keyed by test ID.

    from core.registry import test

    @test(id="AUTH-001", feature="authentication", priority="P0", tags=("smoke", "regression"))
    def test_login_with_valid_credentials(ctx):
        ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

PRIORITIES = ("P0", "P1", "P2", "P3")


@dataclass
class TestCase:
    id: str
    name: str
    func: Callable
    feature: str
    priority: str
    tags: tuple[str, ...]
    needs_browser: bool
    module: str
    description: str = ""


TESTS: list[TestCase] = []


def test(
    id: str,
    feature: str,
    priority: str,
    tags: Iterable[str] = (),
    browser: bool = True,
    description: str = "",
):
    """Register a test function.

    browser=False marks tests that never touch Selenium (API / integration
    checks); the runner then skips driver creation for them.
    """
    if priority not in PRIORITIES:
        raise ValueError(f"{id}: priority must be one of {PRIORITIES}, got {priority!r}")

    def decorator(func: Callable) -> Callable:
        if any(existing.id == id for existing in TESTS):
            raise ValueError(f"Duplicate test id {id!r} ({func.__module__}.{func.__name__})")
        case = TestCase(
            id=id,
            name=func.__name__,
            func=func,
            feature=feature,
            priority=priority,
            tags=tuple(t.lower() for t in tags),
            needs_browser=browser,
            module=func.__module__,
            description=description or (func.__doc__ or "").strip(),
        )
        TESTS.append(case)
        func.__qa_test__ = case
        return func

    return decorator
