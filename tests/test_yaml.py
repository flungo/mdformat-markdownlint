"""The reader parses YAML as js-yaml does.

Each expectation restates what js-yaml, the parser markdownlint-cli2 uses,
returned for the same text, run through the corpus's pinned release; the
loader that makes ruamel.yaml agree is decided in ADR-004.
"""

from __future__ import annotations

import math

import pytest

from mdformat_markdownlint._yaml import parse_yaml


def test_yaml_uses_the_core_schema_js_yaml_uses() -> None:
    document = parse_yaml(
        "a: yes\nb: on\nc: true\nd: 0o17\ne: 1_000\nf: 0x1F\ng: ~\nh: 2001-01-01\n"
        "j: 1e3\nk: 012\nl: \"x\"\nm: [1, two]\nn: {p: q}\no: -0o7\np: 0b101\nq: +12\n"
        "r: True\ns: FALSE\nt: y\nu: off\nv: Null\nw:\nx: 1.\ny: .5\n"
    )
    assert document == {
        "a": "yes", "b": "on", "c": True, "d": 15, "e": "1_000", "f": 31, "g": None,
        "h": "2001-01-01", "j": 1000.0, "k": 12, "l": "x", "m": [1, "two"], "n": {"p": "q"},
        "o": "-0o7", "p": "0b101", "q": 12, "r": True, "s": False, "t": "y", "u": "off",
        "v": None, "w": None, "x": 1.0, "y": 0.5,
    }
    assert isinstance(document["j"], float) and isinstance(document["q"], int)


def test_yaml_special_floats_keys_and_merge_keys_as_js_yaml_has_them() -> None:
    document = parse_yaml("a: .nan\nb: .inf\nc: -.Inf\n1: one\ntrue: two\nnull: three\nbase: &b {x: 1}\nd:\n  <<: *b\n  y: 2\n")
    assert math.isnan(document["a"]) and document["b"] == math.inf and document["c"] == -math.inf
    assert document["1"] == "one" and document["true"] == "two" and document["null"] == "three"
    assert document["d"] == {"<<": {"x": 1}, "y": 2}


@pytest.mark.parametrize(
    "text",
    ["", "# comment only\n", "a: 1\na: 2\n", "a: 1\n---\nb: 2\n", "a:\n\tb: 1\n", "a: !!binary aGk=\n", "a: !!set {x, y}\n"],
)
def test_yaml_rejects_what_js_yaml_rejects(text: str) -> None:
    with pytest.raises(Exception, match=r"empty|duplicated|single document|cannot start any token|tag"):
        parse_yaml(text)
