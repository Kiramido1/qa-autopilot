"""Deterministic, isolated test data.

Unique values keep tests independent of each other and of leftover records;
boundary helpers make min/max/just-outside cases explicit instead of ad hoc.
"""

from __future__ import annotations

import random
import string
import time


def unique_suffix() -> str:
    stamp = time.strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{stamp}-{rand}"


def unique_email(prefix: str = "qa", domain: str = "example.test") -> str:
    return f"{prefix}+{unique_suffix()}@{domain}"


def unique_name(prefix: str = "QA") -> str:
    return f"{prefix} {unique_suffix()}"


def string_of_length(length: int, char: str = "a") -> str:
    return char * length


def boundary_values(minimum: int, maximum: int) -> dict:
    """Numeric boundaries around an inclusive [minimum, maximum] range."""
    return {
        "below_min": minimum - 1,
        "at_min": minimum,
        "above_min": minimum + 1,
        "below_max": maximum - 1,
        "at_max": maximum,
        "above_max": maximum + 1,
    }


def boundary_strings(min_len: int, max_len: int) -> dict:
    return {
        "empty": "",
        "whitespace": "   ",
        "below_min": string_of_length(max(min_len - 1, 0)),
        "at_min": string_of_length(min_len),
        "at_max": string_of_length(max_len),
        "above_max": string_of_length(max_len + 1),
    }


# Inputs every text field should survive (rendering, validation, persistence).
SPECIAL_INPUTS = {
    "unicode": "Ünïcødé 测试 عربى 🚀",
    "html_markup": "<b>bold</b> <script>alert(1)</script>",
    "quotes": 'O\'Brien "quoted" `back`',
    "sql_like": "' OR '1'='1",
    "leading_trailing_space": "  padded  ",
    "very_long": string_of_length(5000),
}
