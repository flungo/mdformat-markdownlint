"""YAML as js-yaml's ``load`` reads it for markdownlint-cli2.

js-yaml's default schema is the YAML 1.2 core schema, which neither Python
library reads as it stands, so this is a loader built on ruamel.yaml that
resolves and constructs the core schema and nothing else (ADR-004):
``yes`` and ``on`` are strings, ``012`` is twelve, ``0o17`` is octal, there
is no merge key, no timestamp and no other tag, a key is a string, a
duplicated key is an error and so is an empty document.
``tests/test_yaml.py`` restates what js-yaml returned for the same text.
"""

from __future__ import annotations

import re
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.constructor import ConstructorError, SafeConstructor
from ruamel.yaml.events import DocumentStartEvent
from ruamel.yaml.nodes import MappingNode
from ruamel.yaml.resolver import VersionedResolver

_CORE_TAGS = frozenset(
    f"tag:yaml.org,2002:{name}" for name in ("null", "bool", "int", "float", "str", "seq", "map")
)


class _CoreResolver(VersionedResolver):
    """The YAML 1.2 core schema, js-yaml's default, whatever version the
    document declares: ``yes`` and ``on`` are strings, ``012`` is twelve,
    ``0o17`` is octal, and nothing else resolves implicitly."""

    _core: dict[str | None, list[tuple[str, re.Pattern[str]]]] = {}

    @property
    def versioned_resolver(self) -> dict[str | None, list[tuple[str, re.Pattern[str]]]]:
        return self._core


def _add_core_resolver(tag: str, regexp: re.Pattern[str], first: list[str]) -> None:
    for char in first:
        _CoreResolver._core.setdefault(char, []).append((tag, regexp))


_add_core_resolver("tag:yaml.org,2002:null", re.compile(r"^(?:~|null|Null|NULL|)$"), ["~", "n", "N", ""])
_add_core_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)
_add_core_resolver(
    "tag:yaml.org,2002:int",
    re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$"),
    list("-+0123456789"),
)
_add_core_resolver(
    "tag:yaml.org,2002:float",
    re.compile(
        r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
        r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"
    ),
    list("-+.0123456789"),
)


def _js_key(key: Any) -> str:
    """A key as a JavaScript object stores it: a string."""
    if isinstance(key, str):
        return key
    if key is None:
        return "null"
    if key is True or key is False:
        return "true" if key else "false"
    if isinstance(key, float):
        return f"{key:g}"
    return str(key)


class _CoreConstructor(SafeConstructor):
    """Only the core schema's tags construct, so an explicit ``!!binary``,
    ``!!set`` or ``!!timestamp`` is an error; there is no merge key, so
    ``<<`` is a key; a duplicated key is an error; and a key is a string, as
    a JavaScript object's is."""

    yaml_constructors = {
        tag: constructor
        for tag, constructor in SafeConstructor.yaml_constructors.items()
        if tag in _CORE_TAGS or tag is None
    }

    def flatten_mapping(self, node: Any) -> None:
        return

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[str, Any]:
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None, None, f"expected a mapping node, but found {node.id}", node.start_mark
            )
        mapping: dict[str, Any] = {}
        for key_node, value_node in node.value:
            key = _js_key(self.construct_object(key_node, deep=True))
            if key in mapping:
                raise ConstructorError(None, None, "duplicated mapping key", key_node.start_mark)
            mapping[key] = self.construct_object(value_node, deep=True)
        return mapping

    def construct_yaml_int(self, node: Any) -> int:
        value = self.construct_scalar(node)
        if value.startswith("0o"):
            return int(value[2:], 8)
        if value.startswith("0x"):
            return int(value[2:], 16)
        return int(value)

    def construct_yaml_float(self, node: Any) -> float:
        value = self.construct_scalar(node)
        lowered = value.lower()
        if lowered.endswith(".inf"):
            return float("-inf") if lowered.startswith("-") else float("inf")
        if lowered.endswith(".nan"):
            return float("nan")
        return float(value)


_CoreConstructor.add_constructor("tag:yaml.org,2002:int", _CoreConstructor.construct_yaml_int)
_CoreConstructor.add_constructor("tag:yaml.org,2002:float", _CoreConstructor.construct_yaml_float)


def _core_yaml() -> YAML:
    loader = YAML(typ="safe", pure=True)
    loader.Resolver = _CoreResolver
    loader.Constructor = _CoreConstructor
    return loader


def parse_yaml(text: str) -> Any:
    """One YAML document in the 1.2 core schema; an empty stream is an error,
    as js-yaml's ``load`` makes it, where ruamel.yaml alone reads it and a
    ``null`` document alike as ``None``."""
    if not any(isinstance(event, DocumentStartEvent) for event in _core_yaml().parse(text)):
        raise ValueError("expected a document, but the input is empty")
    return _core_yaml().load(text)
