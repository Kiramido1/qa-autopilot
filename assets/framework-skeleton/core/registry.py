"""Test registry: the @test decorator, module hooks and the metadata the runner uses.

Every test declares an ID, feature, priority and tags up front so the runner
can select by risk (P0 first), build the traceability matrix and produce
evidence keyed by test ID.

    from core.registry import test

    @test(id="AUTH-001", feature="authentication", priority="P0", tags=("smoke", "regression"))
    def test_login_with_valid_credentials(ctx):
        ...

Module hooks are plain functions in a test module:

    def setup_module(module):      # runs once before the module's tests; module.store is shared
        module.store["item_id"] = module.api.post("/api/items", json={...}).json()["id"]

    def teardown_module(module):   # runs once after, even when tests failed

Session hooks live in tests/session_hooks.py: setup_session(session) / teardown_session(session).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Optional

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
    file: str = ""


@dataclass
class ModuleHooks:
    name: str
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    tests: list = field(default_factory=list)


TESTS: list[TestCase] = []
MODULES: dict[str, ModuleHooks] = {}


def reset() -> None:
    TESTS.clear()
    MODULES.clear()


def register_module(module) -> ModuleHooks:
    hooks = MODULES.setdefault(module.__name__, ModuleHooks(name=module.__name__))
    hooks.setup = getattr(module, "setup_module", None)
    hooks.teardown = getattr(module, "teardown_module", None)
    hooks.tests = [case for case in TESTS if case.module == module.__name__]
    return hooks


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
            file=getattr(getattr(func, "__code__", None), "co_filename", ""),
        )
        TESTS.append(case)
        setattr(func, "__qa_test__", case)  # noqa: B010 - attribute on a plain function
        return func

    return decorator
