"""What the JavaScript tools decide by truthiness, so the plugin decides it the same way."""

from __future__ import annotations

from typing import Any


def truthy(value: Any) -> bool:
    """JavaScript's truthiness, which decides what markdownlint-cli2 and
    markdownlint treat as present or enabled: an empty object or array is
    present; ``null``, ``false``, zero, ``NaN`` and the empty string are not."""
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)):
        # NaN is the one number unequal to itself, which is how a float is
        # found to be NaN without importing math for it.
        return value != 0 and value == value
    return value != ""
