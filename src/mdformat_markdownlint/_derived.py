"""The mdformat options the plugin derives from the markdownlint configuration.

The compatibility matrix's section on what the plugin derives states each
derivation: ``number`` from an explicit MD029 style and ``compact_tables``
from an explicit MD060 style, and nothing from a setting the configuration
leaves at markdownlint's default, so that at the defaults mdformat's own
decisions stand (ADR-005). A rule's setting is read the way markdownlint's
``getEffectiveConfig`` (``lib/markdownlint.mjs``) resolves it, so the setting
the plugin derives from is the one the rule runs with, and the derived value
replaces what mdformat's command line or ``.mdformat.toml`` gave, since the
markdownlint configuration is the one style declaration. A value mdformat
cannot write, and one the plugin does not know, is refused: the matrix's
refusal set, for these two rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from mdformat_markdownlint._javascript import truthy

# Every key a rule's setting may sit under, upper-cased as markdownlint
# compares them: the rule's names and its tags, from its module under
# markdownlint's lib/ at the pinned release. A tag names every rule that
# carries it, so a setting under `table` reaches MD060 as `MD060` does.
# tests/test_derived.py checks the table against the installed markdownlint.
RULE_KEYS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "MD029": ("MD029", "OL-PREFIX", "OL"),
        "MD060": ("MD060", "TABLE-COLUMN-STYLE", "TABLE"),
    }
)


class UnsatisfiableError(Exception):
    """A markdownlint setting mdformat's output can never satisfy, or one the
    plugin does not know what mdformat should write for; the plugin stops
    rather than format under it (ADR-002's refusal)."""


# The values each rule's `style` takes, as its module under markdownlint's
# lib/ reads them, and what mdformat writes for each: the option it implies,
# ``None`` where mdformat's own output is accepted either way, and the reason
# it cannot be satisfied where it cannot be.
_MD029_STYLES: Mapping[str, bool | None | str] = MappingProxyType(
    {
        "one": False,
        "ordered": True,
        "one_or_ordered": None,
        "zero": "mdformat writes every item after the first as `1.`, never `0.`",
    }
)
_MD060_STYLES: Mapping[str, bool | None | str] = MappingProxyType(
    {
        "any": None,
        "aligned": False,
        "compact": True,
        "tight": "mdformat writes a space each side of every pipe",
    }
)


@dataclass(frozen=True)
class Derived:
    """The options derived: ``None`` where the configuration says nothing and
    mdformat's own value stands."""

    number: bool | None
    compact_tables: bool | None


def rule_setting(config: Mapping[str, Any], rule: str) -> Mapping[str, Any] | None:
    """The setting `rule` runs with under `config`, as markdownlint's
    ``getEffectiveConfig`` resolves it: ``None`` when the rule is disabled,
    else its options, an empty mapping when it is merely enabled.

    Keys match the rule's names and tags regardless of case, and a later key
    replaces what an earlier one set. A `default` key, wherever it sits,
    decides whether a rule no key names is enabled. A value that is an object
    enables the rule unless it carries `enabled` false, and its other members
    but `severity` are the options; any other value enables the rule when it
    is truthy and disables it otherwise, with no options either way.
    """
    enabled = True
    for key, value in config.items():
        if key.upper() == "DEFAULT":
            enabled = truthy(value)
            break
    setting: Mapping[str, Any] = MappingProxyType({})
    keys = RULE_KEYS[rule]
    for key, value in config.items():
        if key.upper() not in keys:
            continue
        if isinstance(value, dict):
            enabled = truthy(value["enabled"]) if "enabled" in value else True
            setting = MappingProxyType(
                {name: option for name, option in value.items() if name not in ("enabled", "severity")}
            )
        else:
            # An array is an object to JavaScript, present and enabled, whose
            # members sit under their indices and name no option.
            enabled = isinstance(value, list) or truthy(value)
            setting = MappingProxyType({})
    return setting if enabled else None


def derive(config: Mapping[str, Any]) -> Derived:
    """The options the configuration implies, per the compatibility matrix:
    only a style that names what mdformat is to write derives its option; a
    rule disabled, at its default or at a value that accepts what mdformat
    writes either way derives nothing, so mdformat's own value stands; a
    value mdformat cannot write, or one the plugin does not know, raises
    :class:`UnsatisfiableError`."""
    number = None
    md029 = rule_setting(config, "MD029")
    if md029 is not None:
        # MD029 reads `String(style)` and knows `one`, `ordered` and `zero`;
        # `one_or_ordered`, the documented default, and the key absent or null
        # all fall through to the same adaptive check, which accepts what
        # mdformat writes with and without `number`.
        style = md029.get("style")
        number = _implied("MD029", "one_or_ordered" if style is None else style, _MD029_STYLES)
    compact_tables = None
    md060 = rule_setting(config, "MD060")
    if md060 is not None:
        # MD060 reads `String(style || "any")`, so a falsy value is `any`.
        style = md060.get("style")
        compact_tables = _implied("MD060", style if truthy(style) else "any", _MD060_STYLES)
        if compact_tables and truthy(md060.get("aligned_delimiter")):
            raise UnsatisfiableError(
                "MD060 at style 'compact' with aligned_delimiter cannot be satisfied: "
                "mdformat writes the compact delimiter row as `--` whatever the header's "
                "width; the compatibility matrix lists the setting under the refusal set"
            )
    return Derived(number=number, compact_tables=compact_tables)


def _implied(rule: str, style: Any, styles: Mapping[str, bool | None | str]) -> bool | None:
    """What a rule's style implies, or the refusal of it."""
    if not isinstance(style, str) or style not in styles:
        raise UnsatisfiableError(
            f"{rule} at style {style!r} is not one the plugin knows, "
            f"{', '.join(repr(known) for known in styles)}: markdownlint accepts what "
            "mdformat writes under a style it does not know, but the plugin does not "
            "format under a setting it cannot read"
        )
    implied = styles[style]
    if isinstance(implied, str):
        raise UnsatisfiableError(
            f"{rule} at style {style!r} cannot be satisfied: {implied}; the compatibility "
            "matrix lists the setting under the refusal set"
        )
    return implied


def apply(options: Mapping[str, Any], derived: Derived) -> dict[str, Any]:
    """mdformat's options for the file with the derived values in place of
    what its command line, `.mdformat.toml` or API call gave.

    ``number`` is mdformat's own option. Compact tables is mdformat-gfm's,
    which its table renderer reads from two places, the command line's and
    the TOML file's `plugin.tables.compact_tables` and the API's
    `compact_tables`, and treats as set when either is, so a derived value
    is written to both.
    """
    options = dict(options)
    if derived.number is not None:
        options["number"] = derived.number
    if derived.compact_tables is not None:
        options["compact_tables"] = derived.compact_tables
        plugins = dict(options.get("plugin", {}))
        plugins["tables"] = {**plugins.get("tables", {}), "compact_tables": derived.compact_tables}
        options["plugin"] = plugins
    return options
