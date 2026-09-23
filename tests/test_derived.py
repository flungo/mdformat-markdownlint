"""The plugin derives `number` and `compact_tables` from the markdownlint configuration.

How a rule's setting is resolved was first observed by running the corpus's
pinned markdownlint-cli2 on a document that reports differently under MD029
disabled, at its default style and at `ordered`, so each expectation on
`rule_setting` restates that run; what each setting derives is the
compatibility matrix's table, ADR-005 the rule behind it, and the corpus
proves each derivation end to end. The end-to-end tests here prove the derived value replaces mdformat's
own, which no corpus case can, since the harness passes no option.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import mdformat
import pytest

from conftest import CONTRACT_EXTENSIONS, MARKDOWNLINT_CLI2_PACKAGE, PLUGIN_EXTENSION
from mdformat_markdownlint import Derived, UnsatisfiableError, clear_cache, derive
from mdformat_markdownlint._derived import RULE_KEYS, apply, rule_setting

EXTENSIONS = {*CONTRACT_EXTENSIONS, PLUGIN_EXTENSION}
ZERO_START = "0. a\n1. b\n1. c\n"
COMPACT = "| A | B |\n| -- | -- |\n| a | longer cell |\n"
ALIGNED = "| A   | B           |\n| --- | ----------- |\n| a   | longer cell |\n"


@pytest.fixture(autouse=True)
def _fresh_cache() -> None:
    clear_cache()


# --- a rule's setting, as markdownlint resolves it ---------------------------


@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, {}),
        ({"MD029": True}, {}),
        ({"MD029": "warning"}, {}),
        ({"MD029": 2}, {}),
        ({"MD029": ["ordered"]}, {}),
        ({"MD029": {}}, {}),
        ({"MD029": {"style": "ordered"}}, {"style": "ordered"}),
        ({"md029": {"style": "ordered"}}, {"style": "ordered"}),
        ({"ol-prefix": {"style": "ordered"}}, {"style": "ordered"}),
        ({"ol": {"style": "ordered"}}, {"style": "ordered"}),
        ({"MD029": {"style": "ordered", "severity": "warning"}}, {"style": "ordered"}),
        ({"MD029": {"style": "ordered", "enabled": True}}, {"style": "ordered"}),
        ({"ol": False, "MD029": {"style": "ordered"}}, {"style": "ordered"}),
        ({"MD029": {"style": "one"}, "md029": {"style": "ordered"}}, {"style": "ordered"}),
        ({"md029": {"style": "ordered"}, "MD029": {"style": "one"}}, {"style": "one"}),
        ({"MD029": {"style": "ordered"}, "ol-prefix": {"style": "one"}}, {"style": "one"}),
        ({"default": False, "ol-prefix": {"style": "ordered"}}, {"style": "ordered"}),
        ({"default": 0, "MD029": {}}, {}),
        ({"MD029": False}, None),
        ({"MD029": 0}, None),
        ({"MD029": ""}, None),
        ({"MD029": None}, None),
        ({"MD029": {"style": "ordered", "enabled": False}}, None),
        ({"MD029": {"style": "ordered", "enabled": None}}, None),
        ({"MD029": {"style": "ordered"}, "ol": False}, None),
        ({"default": False}, None),
        ({"DEFAULT": False}, None),
        ({"MD013": {"style": "ordered"}}, {}),
    ],
)
def test_a_rules_setting_is_resolved_as_markdownlint_resolves_it(
    config: dict[str, Any], expected: dict[str, Any] | None
) -> None:
    setting = rule_setting(config, "MD029")
    assert (None if setting is None else dict(setting)) == expected


def test_the_rule_names_and_tags_are_the_installed_markdownlints() -> None:
    """The keys a setting may sit under are copied from markdownlint's rule
    modules, so the installed release, the latest leg's included, is asked
    for them."""
    script = (
        'const path = require("path");'
        'const rules = path.join(path.dirname(require.resolve("markdownlint")), "rules.mjs");'
        "import(rules).then((m) => console.log(JSON.stringify(m.default.map("
        "(r) => [r.names, r.tags]))));"
    )
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=MARKDOWNLINT_CLI2_PACKAGE,
        capture_output=True,
        text=True,
        check=True,
    )
    installed = {
        names[0]: tuple(key.upper() for key in (*names, *tags))
        for names, tags in json.loads(proc.stdout)
    }
    assert {rule: installed[rule] for rule in RULE_KEYS} == dict(RULE_KEYS)


# --- what each setting derives -----------------------------------------------


@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, Derived(number=None, compact_tables=None)),
        ({"default": False}, Derived(number=None, compact_tables=None)),
        ({"MD029": {"style": "one"}}, Derived(number=False, compact_tables=None)),
        ({"MD029": {"style": "ordered"}}, Derived(number=True, compact_tables=None)),
        ({"ol": {"style": "ordered"}}, Derived(number=True, compact_tables=None)),
        ({"MD029": {"style": "one_or_ordered"}}, Derived(number=None, compact_tables=None)),
        ({"MD029": True}, Derived(number=None, compact_tables=None)),
        ({"MD029": {"style": None}}, Derived(number=None, compact_tables=None)),
        ({"MD029": {"style": "zero", "enabled": False}}, Derived(number=None, compact_tables=None)),
        ({"MD029": {"style": "one", "enabled": False}}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": "compact"}}, Derived(number=None, compact_tables=True)),
        ({"MD060": {"style": "aligned"}}, Derived(number=None, compact_tables=False)),
        ({"table-column-style": {"style": "aligned"}}, Derived(number=None, compact_tables=False)),
        ({"MD060": {"style": "any"}}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": ""}}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": 0}}, Derived(number=None, compact_tables=None)),
        ({"MD060": True}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": "aligned", "aligned_delimiter": True}}, Derived(number=None, compact_tables=False)),
        ({"MD060": {"style": "any", "aligned_delimiter": True}}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": "compact", "aligned_delimiter": False}}, Derived(number=None, compact_tables=True)),
        ({"MD060": {"style": "tight"}, "table": False}, Derived(number=None, compact_tables=None)),
        ({"MD060": {"style": "compact"}, "table": False}, Derived(number=None, compact_tables=None)),
        ({"MD013": True}, Derived(number=None, compact_tables=None)),
        ({"default": False, "MD060": {"style": "compact"}}, Derived(number=None, compact_tables=True)),
        (
            {"MD029": {"style": "one"}, "MD060": {"style": "aligned"}},
            Derived(number=False, compact_tables=False),
        ),
    ],
)
def test_what_a_configuration_derives(config: dict[str, Any], expected: Derived) -> None:
    assert derive(config) == expected


@pytest.mark.parametrize(
    "config,message",
    [
        ({"MD029": {"style": "zero"}}, r"MD029 at style 'zero' cannot be satisfied: mdformat writes every item"),
        ({"ol": {"style": "zero"}}, r"MD029 at style 'zero' cannot be satisfied"),
        ({"MD029": {"style": "bogus"}}, r"MD029 at style 'bogus' is not one the plugin knows, 'one', 'ordered'"),
        ({"MD029": {"style": "ONE"}}, r"MD029 at style 'ONE' is not one the plugin knows"),
        ({"MD029": {"style": 1}}, r"MD029 at style 1 is not one the plugin knows"),
        ({"MD060": {"style": "tight"}}, r"MD060 at style 'tight' cannot be satisfied: mdformat writes a space"),
        ({"MD060": {"style": "Compact"}}, r"MD060 at style 'Compact' is not one the plugin knows, 'any', 'aligned'"),
        ({"MD060": {"style": 1}}, r"MD060 at style 1 is not one the plugin knows"),
        (
            {"MD060": {"style": "compact", "aligned_delimiter": True}},
            r"MD060 at style 'compact' with aligned_delimiter cannot be satisfied",
        ),
    ],
)
def test_a_setting_mdformat_cannot_satisfy_or_the_plugin_does_not_know_is_refused(
    config: dict[str, Any], message: str
) -> None:
    with pytest.raises(UnsatisfiableError, match=message):
        derive(config)


@pytest.mark.parametrize(
    "derived,expected",
    [
        (
            Derived(number=False, compact_tables=False),
            {
                "number": False,
                "wrap": 72,
                "compact_tables": False,
                "plugin": {"tables": {"compact_tables": False}, "gfm": {}},
            },
        ),
        (
            Derived(number=True, compact_tables=True),
            {
                "number": True,
                "wrap": 72,
                "compact_tables": True,
                "plugin": {"tables": {"compact_tables": True}, "gfm": {}},
            },
        ),
        (
            Derived(number=None, compact_tables=True),
            {
                "number": True,
                "wrap": 72,
                "compact_tables": True,
                "plugin": {"tables": {"compact_tables": True}, "gfm": {}},
            },
        ),
        (
            Derived(number=False, compact_tables=None),
            {"number": False, "wrap": 72, "plugin": {"tables": {"compact_tables": True}, "gfm": {}}},
        ),
        (
            Derived(number=None, compact_tables=None),
            {"number": True, "wrap": 72, "plugin": {"tables": {"compact_tables": True}, "gfm": {}}},
        ),
    ],
)
def test_a_derived_value_replaces_the_option_and_leaves_the_rest(
    derived: Derived, expected: dict[str, Any]
) -> None:
    given = {"number": True, "wrap": 72, "plugin": {"tables": {"compact_tables": True}, "gfm": {}}}
    assert apply(given, derived) == expected
    assert given == {
        "number": True,
        "wrap": 72,
        "plugin": {"tables": {"compact_tables": True}, "gfm": {}},
    }, "the caller's options are not mutated"


def test_apply_reads_an_option_mapping_with_no_plugin_entry() -> None:
    assert apply({}, Derived(number=None, compact_tables=True)) == {
        "compact_tables": True,
        "plugin": {"tables": {"compact_tables": True}},
    }


# --- through mdformat --------------------------------------------------------


def configure(root: Path, config: dict[str, Any]) -> None:
    (root / ".markdownlint-cli2.jsonc").write_text(json.dumps({"config": config}))


def test_number_is_derived_over_the_option_given(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD029": {"style": "ordered"}})
    assert mdformat.text(ZERO_START, options={"number": False}, extensions=EXTENSIONS) == "0. a\n1. b\n2. c\n"
    clear_cache()
    configure(tmp_path, {"MD029": {"style": "one"}})
    assert mdformat.text(ZERO_START, options={"number": True}, extensions=EXTENSIONS) == "0. a\n1. b\n1. c\n"


def test_number_is_mdformats_own_where_the_configuration_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD029": False})
    assert mdformat.text(ZERO_START, options={"number": True}, extensions=EXTENSIONS) == "0. a\n1. b\n2. c\n"
    assert mdformat.text(ZERO_START, extensions=EXTENSIONS) == "0. a\n1. b\n1. c\n"


@pytest.mark.parametrize(
    "options",
    [
        {"compact_tables": True},
        {"plugin": {"tables": {"compact_tables": True}}},
    ],
    ids=["api", "cli-or-toml"],
)
def test_aligned_is_derived_over_compact_tables_given_either_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options: dict[str, Any]
) -> None:
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD060": {"style": "aligned"}})
    assert mdformat.text(COMPACT, options=options, extensions=EXTENSIONS) == ALIGNED


def test_compact_is_derived_over_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD060": {"style": "compact"}})
    assert mdformat.text(ALIGNED, extensions=EXTENSIONS) == COMPACT


def test_the_derivation_is_per_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each file is formatted under its own directory's configuration, and an
    option derived for one file does not leak into the next."""
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD029": {"style": "one"}})
    ordered = tmp_path / "ordered"
    ordered.mkdir()
    configure(ordered, {"MD029": {"style": "ordered"}})
    first = ordered / "a.md"
    first.write_text(ZERO_START)
    second = tmp_path / "b.md"
    second.write_text(ZERO_START)
    mdformat.file(first, extensions=EXTENSIONS)
    mdformat.file(second, extensions=EXTENSIONS)
    assert first.read_text() == "0. a\n1. b\n2. c\n"
    assert second.read_text() == "0. a\n1. b\n1. c\n"


def test_a_refused_setting_stops_the_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    configure(tmp_path, {"MD029": {"style": "zero"}})
    with pytest.raises(UnsatisfiableError, match="MD029 at style 'zero'"):
        mdformat.text(ZERO_START, extensions=EXTENSIONS)


def test_nothing_is_derived_at_markdownlints_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no configuration, or one that leaves both rules at their default,
    mdformat's own decisions stand (ADR-005)."""
    monkeypatch.chdir(tmp_path)
    assert mdformat.text(ZERO_START, extensions=EXTENSIONS) == "0. a\n1. b\n1. c\n"
    assert mdformat.text(COMPACT, extensions=EXTENSIONS) == ALIGNED
    assert mdformat.text(ZERO_START, options={"number": True}, extensions=EXTENSIONS) == "0. a\n1. b\n2. c\n"
    assert mdformat.text(ALIGNED, options={"compact_tables": True}, extensions=EXTENSIONS) == COMPACT
