"""Read the markdownlint configuration for a file the way markdownlint-cli2 does.

Every behaviour the plugin has starts from the configuration markdownlint-cli2
would lint the file with, so the reading is one module, and it follows that
tool's code rather than either tool's documentation: ``markdownlint-cli2.mjs``
(``getAndProcessDirInfo``, ``enumerateParents``, ``createDirInfos`` and
``mergeOptions``) for which files are read and how they combine, and
``markdownlint/lib/markdownlint.mjs`` (``readConfig``, ``extendConfig`` and
``resolveConfigExtends``) for ``extends``. The parsers match the ones those
modules use: jsonc-parser, smol-toml and js-yaml, whose default schema is the
YAML 1.2 core schema. ``docs/reference/configuration.md`` states the result
for an adopter, divergences included.
"""

from __future__ import annotations

import functools
import json
import os
import re
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.constructor import ConstructorError, SafeConstructor
from ruamel.yaml.error import YAMLError
from ruamel.yaml.events import DocumentStartEvent
from ruamel.yaml.nodes import MappingNode
from ruamel.yaml.resolver import VersionedResolver

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

# The two kinds of file markdownlint-cli2 reads in a directory, each in the
# order it looks: the first present of each kind is the one read.
OPTIONS_FILE_NAMES = (
    ".markdownlint-cli2.jsonc",
    ".markdownlint-cli2.yaml",
    ".markdownlint-cli2.cjs",
    ".markdownlint-cli2.mjs",
)
CONFIG_FILE_NAMES = (
    ".markdownlint.jsonc",
    ".markdownlint.json",
    ".markdownlint.yaml",
    ".markdownlint.yml",
    ".markdownlint.cjs",
    ".markdownlint.mjs",
)
_JAVASCRIPT_SUFFIXES = (".cjs", ".mjs")


class ConfigurationError(Exception):
    """The markdownlint configuration cannot be read as markdownlint-cli2 would
    read it, so the plugin stops and says why rather than formatting under a
    configuration it has not read."""


@dataclass(frozen=True)
class Configuration:
    """What markdownlint-cli2 would lint a file with.

    ``config`` is the markdownlint configuration object, ``extends`` resolved,
    and empty where nothing sets one; ``options`` is the merged
    markdownlint-cli2 options object, empty where no options file applies;
    ``files`` is the configuration file of each directory read, nearest
    first, without the files those extend. Both mappings are read-only views.
    """

    config: Mapping[str, Any]
    options: Mapping[str, Any]
    files: tuple[Path, ...]


def configuration_for(path: Path | None = None, *, cwd: Path | None = None) -> Configuration:
    """The configuration markdownlint-cli2 would lint ``path`` with, run from
    ``cwd``; with no path, the one it gives standard input, which is the
    working directory's.

    The directories read are the file's and each parent up to the working
    directory, or up to the nearest ancestor the two share when the file is
    outside it, and then the working directory itself; nothing above the
    working directory is read. Nearer directories win.

    A directory holding no file of either kind does not take part, as
    markdownlint-cli2 folds its files into the nearest ancestor that holds
    one (``createDirInfos``): the nearest configured directory is then the
    file's own, and its configuration file beats its options file's
    ``config`` there, where it would lose to it one directory further up.
    """
    cwd = Path(os.path.abspath(cwd if cwd is not None else os.getcwd()))
    directories = [
        directory
        for directory in (_read_directory(directory) for directory in _directories(path, cwd))
        if directory.options is not None or directory.config is not None
    ]
    if not directories:
        return Configuration(config=MappingProxyType({}), options=MappingProxyType({}), files=())
    options = directories[0].options
    config = directories[0].config
    for parent in directories[1:]:
        if parent.options is not None:
            options = _merge_options(parent.options, options if options is not None else {})
        if (
            config is None
            and parent.config is not None
            and not _truthy((options or {}).get("config"))
        ):
            config = parent.config
    effective = config if _truthy(config) else (options or {}).get("config")
    if not isinstance(effective, dict):
        effective = {}
    return Configuration(
        config=MappingProxyType(effective),
        options=MappingProxyType(options if options is not None else {}),
        files=tuple(file for directory in directories for file in directory.files),
    )


def clear_cache() -> None:
    """Forget every directory read, so a changed file is read again."""
    _read_directory.cache_clear()


def _directories(path: Path | None, cwd: Path) -> list[Path]:
    if path is None:
        return [cwd]
    start = Path(os.path.abspath(path)).parent
    ancestry = {cwd, *cwd.parents}
    directories = [start]
    current = start
    while current not in ancestry:
        parent = current.parent
        if parent == current:
            break
        current = parent
        directories.append(current)
    if current != cwd:
        directories.append(cwd)
    return directories


@dataclass(frozen=True)
class _Directory:
    options: dict[str, Any] | None
    config: dict[str, Any] | None
    files: tuple[Path, ...]


@functools.lru_cache(maxsize=None)
def _read_directory(directory: Path) -> _Directory:
    files: list[Path] = []
    options = None
    options_file = _first_present(directory, OPTIONS_FILE_NAMES)
    if options_file is not None:
        files.append(options_file)
        _refuse_javascript(options_file)
        options = _read_options(options_file)
    config = None
    config_file = _first_present(directory, CONFIG_FILE_NAMES)
    if config_file is not None:
        files.append(config_file)
        _refuse_javascript(config_file)
        config = _read_config(config_file)
    return _Directory(options, config, tuple(files))


def _first_present(directory: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def _refuse_javascript(path: Path) -> None:
    if path.suffix in _JAVASCRIPT_SUFFIXES:
        raise ConfigurationError(
            f"{path}: a JavaScript configuration file is not read; write the "
            "configuration in the JSONC or YAML form so that it can be"
        )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigurationError(f"Unable to read '{path}'; {error.strerror}") from error


def _read_options(path: Path) -> dict[str, Any] | None:
    """A ``.markdownlint-cli2.*`` file: JSONC or YAML by its name, as
    markdownlint-cli2's ``readJsonc`` and ``readYaml`` read it, with the
    ``extends`` of its ``config`` resolved from its own location."""
    text = _read_text(path)
    try:
        value = parse_jsonc(text) if path.suffix == ".jsonc" else parse_yaml(text)
    except (ValueError, YAMLError) as error:
        raise ConfigurationError(f"Unable to use configuration file '{path}'; {error}") from error
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigurationError(
            f"Unable to use configuration file '{path}'; it holds "
            f"{_describe(value)} where an options object is expected"
        )
    config = value.get("config")
    if isinstance(config, dict) and _truthy(config.get("extends")):
        value["config"] = _extend(config, path, ())
    return value


def _read_config(path: Path, seen: tuple[Path, ...] = ()) -> dict[str, Any]:
    """A ``.markdownlint.*`` file, or a file ``extends`` names: parsed by the
    first of JSONC, TOML and YAML that accepts it, whatever its name, as
    markdownlint's ``readConfig`` does, with its own ``extends`` resolved from
    its own location and its own keys winning over what it extends."""
    return _extend(_parse_configuration(path, _read_text(path)), path, seen)


def _parse_configuration(path: Path, text: str) -> dict[str, Any]:
    failures = []
    for parser in (parse_jsonc, tomllib.loads, parse_yaml):
        try:
            value = parser(text)
        except Exception as error:  # noqa: BLE001 - each parser's failure is reported
            failures.append(f"{parser.__name__}: {error}")
            continue
        return value if isinstance(value, dict) else {}
    raise ConfigurationError(f"Unable to parse '{path}'; " + "; ".join(failures))


def _extend(config: dict[str, Any], path: Path, seen: tuple[Path, ...]) -> dict[str, Any]:
    extends = config.get("extends")
    if not _truthy(extends):
        return config
    if not isinstance(extends, str):
        raise ConfigurationError(
            f"{path}: extends must name a file or a module, not {_describe(extends)}"
        )
    target = _resolve_extends(path, extends)
    if target in seen or target == path:
        raise ConfigurationError(f"{path}: extends {extends!r}, which leads back to itself")
    base = _read_config(target, (*seen, path))
    merged = {**base, **config}
    del merged["extends"]
    return merged


_TILDE = re.compile(r"^~($|/|\\)")


def _expand_tilde(reference: str) -> str:
    """``~`` at the start of a path, alone or before a separator, replaced
    by the home directory, as markdownlint's ``expandTildePath`` does before
    it reads a file or resolves an ``extends``; unlike ``os.path.expanduser``,
    ``~name`` is left as written, and so is everything when no home directory
    is known."""
    home = os.path.expanduser("~")
    if home == "~":
        return reference
    return _TILDE.sub(lambda match: home + match.group(1), reference)


def _resolve_extends(config_file: Path, reference: str) -> Path:
    """Where ``extends`` points: the path beside the configuration file when
    that exists, else the module Node's resolution finds from the file's
    directory, else the path, whose reading then reports it missing."""
    reference = _expand_tilde(reference)
    directory = config_file.parent
    candidate = Path(os.path.normpath(directory / reference))
    if candidate.exists():
        return candidate
    module = _resolve_module(reference, directory)
    return module if module is not None else candidate


_MODULE_FILE_EXTENSIONS = ("", ".js", ".json", ".node")
_MODULE_INDEX_NAMES = ("index.js", "index.json", "index.node")


def _resolve_module(reference: str, directory: Path) -> Path | None:
    if reference.startswith((".", "/", "\\")) or os.path.isabs(reference):
        return None
    for lookup in _module_lookup_paths(directory):
        if not lookup.is_dir():
            continue
        base = lookup / reference
        found = _load_as_file(base) or _load_as_directory(base)
        if found is not None:
            return found
    return None


def _module_lookup_paths(directory: Path) -> Iterator[Path]:
    for ancestor in (directory, *directory.parents):
        if ancestor.name != "node_modules":
            yield ancestor / "node_modules"
    for entry in os.environ.get("NODE_PATH", "").split(os.pathsep):
        if entry:
            yield Path(entry)
    home = os.path.expanduser("~")
    if home != "~":
        yield Path(home) / ".node_modules"
        yield Path(home) / ".node_libraries"


def _load_as_file(base: Path) -> Path | None:
    for extension in _MODULE_FILE_EXTENSIONS:
        candidate = base.with_name(base.name + extension)
        if candidate.is_file():
            return candidate
    return None


def _load_index(base: Path) -> Path | None:
    for name in _MODULE_INDEX_NAMES:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def _load_as_directory(base: Path) -> Path | None:
    manifest = base / "package.json"
    if manifest.is_file():
        try:
            main = json.loads(manifest.read_text(encoding="utf-8")).get("main")
        except (ValueError, AttributeError, OSError):
            main = None
        if isinstance(main, str) and main:
            target = Path(os.path.normpath(base / main))
            found = _load_as_file(target) or _load_index(target)
            if found is not None:
                return found
    return _load_index(base)


def _merge_options(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """markdownlint-cli2's ``mergeOptions``: the second's keys replace the
    first's, except ``config``, whose rule keys are combined, each rule's
    value replaced whole."""
    merged = {**first, **second}
    first_config = first.get("config")
    second_config = second.get("config")
    if _truthy(first_config) or _truthy(second_config):
        merged["config"] = {**_spreadable(first_config), **_spreadable(second_config)}
    return merged


def _spreadable(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _truthy(value: Any) -> bool:
    """JavaScript's truthiness, which decides what markdownlint-cli2 treats as
    present: an empty object is present; ``null``, ``false``, zero, ``NaN``
    and the empty string are not."""
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)):
        # NaN is the one number unequal to itself, which is how a float is
        # found to be NaN without importing math for it.
        return value != 0 and value == value
    return value != ""


def _describe(value: Any) -> str:
    return {
        list: "an array",
        str: "a string",
        bool: "a boolean",
        int: "a number",
        float: "a number",
    }.get(type(value), type(value).__name__)


# --- JSONC, as jsonc-parser reads it for markdownlint-cli2 ------------------


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


# --- YAML, as js-yaml's load reads it for markdownlint-cli2 -----------------


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
