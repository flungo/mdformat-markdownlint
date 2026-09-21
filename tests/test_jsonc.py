"""The reader parses JSONC as jsonc-parser does.

Each table restates what jsonc-parser, the parser markdownlint-cli2 uses,
returned for the same text, run through the corpus's pinned release.
"""

from __future__ import annotations

import pytest

from mdformat_markdownlint._jsonc import parse_jsonc


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"a": 1, // c\n "b": [1,2,],}', {"a": 1, "b": [1, 2]}),
        ('{"a": "// not a comment", /* x */ "b": 2}', {"a": "// not a comment", "b": 2}),
        ('{"a": 1, "a": 2}', {"a": 2}),
        ('{"a": "\\u0041\\n"}', {"a": "A\n"}),
        ('{"a":1}\n\n', {"a": 1}),
        ("null", None),
        ("[1,2]", [1, 2]),
    ],
)
def test_jsonc_accepts_what_jsonc_parser_accepts(text: str, expected: object) -> None:
    assert parse_jsonc(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "{a: 1}",
        '{"a": 1,, }',
        "",
        "// only comment",
        '{"a": 1} trailing',
        '{"a": NaN}',
        '{"a": 0x10}',
        "{\"a\": 'x'}",
        '{"a": +1}',
        '{"a": .5}',
        '{"a": 01}',
        '{"a": "multi\nline"}',
        "{,}",
        '{"a": [,]}',
        '{"a": 1 /* open',
    ],
)
def test_jsonc_rejects_what_jsonc_parser_rejects(text: str) -> None:
    with pytest.raises(ValueError):
        parse_jsonc(text)
