"""JSONC as jsonc-parser reads it for markdownlint-cli2.

markdownlint-cli2 parses its ``.markdownlint-cli2.jsonc`` files, and every
``.markdownlint.*`` file first, with jsonc-parser: JSON with line and block
comments and a trailing comma before a closing bracket, and an error for
anything else the parser reports, which markdownlint-cli2 turns into a
failed run. ``tests/test_jsonc.py`` restates what jsonc-parser returned for
the same text.
"""

from __future__ import annotations

import json
from typing import Any

def parse_jsonc(text: str) -> Any:
    """JSON with line and block comments and trailing commas, and nothing
    else jsonc-parser reports: ``NaN``, single quotes, a leading comma and
    text after the value are errors, as they are there."""
    return json.loads(_strip_jsonc(text), parse_constant=_reject_constant)


def _reject_constant(token: str) -> Any:
    raise ValueError(f"{token} is not a JSON value")


def _strip_jsonc(text: str) -> str:
    out: list[str] = []
    last = ""  # the last significant character emitted
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 1
                j += 1
            out.append(text[i : j + 1])
            last = '"'
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise ValueError("unterminated block comment")
            out.append(" ")
            i = j + 2
        elif char == "," and last not in ("", "[", "{", ","):
            j = _skip_insignificant(text, i + 1)
            if j < n and text[j] in "}]":
                i += 1
            else:
                out.append(char)
                last = char
                i += 1
        else:
            out.append(char)
            if not char.isspace():
                last = char
            i += 1
    return "".join(out)


def _skip_insignificant(text: str, i: int) -> int:
    n = len(text)
    while True:
        while i < n and text[i].isspace():
            i += 1
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            return i
