"""JavaScript's truthiness, as the plugin decides it where the tools do.

The table restates what `!!value` gives in Node for each JSON value, and the
oracle test runs Node on the same values so the table cannot drift from it.
"""

from __future__ import annotations

import json
import math
import subprocess
from typing import Any

import pytest

from conftest import MARKDOWNLINT_CLI2_PACKAGE
from mdformat_markdownlint._javascript import truthy

JSON_VALUES: list[tuple[Any, bool]] = [
    (None, False),
    (False, False),
    (True, True),
    (0, False),
    (0.0, False),
    (-0.0, False),
    (1, True),
    (-1, True),
    (0.5, True),
    ("", False),
    ("0", True),
    ("false", True),
    (" ", True),
    ([], True),
    ([0], True),
    ({}, True),
    ({"a": False}, True),
]


@pytest.mark.parametrize("value,expected", JSON_VALUES + [(math.nan, False), (math.inf, True)])
def test_truthiness_is_javascripts(value: Any, expected: bool) -> None:
    assert truthy(value) is expected


def test_the_table_is_what_node_gives() -> None:
    script = "process.stdin.on('data', (d) => console.log(JSON.stringify(JSON.parse(d).map((v) => !!v))));"
    proc = subprocess.run(
        ["node", "-e", script],
        input=json.dumps([value for value, _ in JSON_VALUES]),
        cwd=MARKDOWNLINT_CLI2_PACKAGE,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc.stdout) == [expected for _, expected in JSON_VALUES]
