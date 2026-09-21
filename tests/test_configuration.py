"""The plugin reads the markdownlint configuration as markdownlint-cli2 does.

Each expectation on which files are read and how they combine was first
observed by running the corpus's pinned markdownlint-cli2 on the same layout
and reading which rules it reported, so a test here restates that run rather
than a reading of the code. The parsers have their own tests beside this
file, against what jsonc-parser and js-yaml returned for the same text.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

import mdformat_markdownlint
from mdformat_markdownlint import ConfigurationError, clear_cache, configuration_for

BREAKABLE = "word " * 30


@pytest.fixture(autouse=True)
def _fresh_cache() -> None:
    clear_cache()


def write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def config_for(root: Path, relative: str, cwd: str = ".") -> dict:
    return dict(configuration_for(root / relative, cwd=root / cwd).config)


# --- which files, in which directories ---------------------------------------


def test_no_configuration_anywhere_is_empty(tmp_path: Path) -> None:
    write(tmp_path, "a.md", "")
    configuration = configuration_for(tmp_path / "a.md", cwd=tmp_path)
    assert dict(configuration.config) == {}
    assert dict(configuration.options) == {}
    assert configuration.files == ()


def test_no_path_reads_the_working_directory(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    assert dict(configuration_for(cwd=tmp_path).config) == {"MD041": False}


@pytest.mark.parametrize(
    ("names", "kind"),
    [
        ((".markdownlint-cli2.jsonc", ".markdownlint-cli2.yaml"), "options"),
        ((".markdownlint.jsonc", ".markdownlint.json", ".markdownlint.yaml", ".markdownlint.yml"), "config"),
    ],
)
def test_the_first_present_name_of_each_kind_is_read(tmp_path: Path, names: tuple[str, ...], kind: str) -> None:
    for index, name in enumerate(names):
        body = f'{{ "MD013": {{ "line_length": {100 + index} }} }}'
        write(tmp_path, name, f'{{ "config": {body} }}' if kind == "options" else body)
    write(tmp_path, "a.md", "")
    for index, name in enumerate(names):
        clear_cache()
        assert config_for(tmp_path, "a.md") == {"MD013": {"line_length": 100 + index}}
        (tmp_path / name).unlink()


def test_a_javascript_options_file_is_refused_by_name(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.mjs", "export default { config: {} };")
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match=r"\.markdownlint-cli2\.mjs: a JavaScript configuration"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


def test_a_javascript_config_file_is_refused_even_beside_an_options_file(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", "{}")
    write(tmp_path, ".markdownlint.cjs", "module.exports = {};")
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match=r"\.markdownlint\.cjs: a JavaScript configuration"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


def test_a_jsonc_options_file_beside_a_javascript_one_is_the_one_read(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    write(tmp_path, ".markdownlint-cli2.cjs", "module.exports = {};")
    write(tmp_path, "a.md", "")
    assert config_for(tmp_path, "a.md") == {"MD041": False}


def test_directories_are_read_from_the_file_up_to_the_working_directory(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false, "MD013": false } }')
    write(tmp_path, "root/.markdownlint-cli2.jsonc", '{ "config": { "MD013": { "line_length": 200 } } }')
    write(tmp_path, "root/sub/deep/c.md", BREAKABLE)
    configuration = configuration_for(tmp_path / "root/sub/deep/c.md", cwd=tmp_path / "root")
    # Nothing above the working directory is read: MD041 stays at its default.
    assert dict(configuration.config) == {"MD013": {"line_length": 200}}
    assert configuration.files == (tmp_path / "root/.markdownlint-cli2.jsonc",)


def test_a_file_outside_the_working_directory_gets_its_configuration_as_the_weakest(tmp_path: Path) -> None:
    write(tmp_path, "root/.markdownlint-cli2.jsonc", '{ "config": { "MD041": false, "MD013": { "line_length": 200 } } }')
    write(tmp_path, "outside/.markdownlint-cli2.jsonc", '{ "config": { "MD013": { "tables": false } } }')
    write(tmp_path, "outside/i.md", BREAKABLE)
    write(tmp_path, "j.md", BREAKABLE)
    assert config_for(tmp_path, "outside/i.md", cwd="root") == {"MD041": False, "MD013": {"tables": False}}
    # A file above the working directory reads its own directory and then the working directory's.
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD013": false } }')
    clear_cache()
    assert config_for(tmp_path, "j.md", cwd="root") == {"MD041": False, "MD013": False}


# --- how the files combine ---------------------------------------------------


def test_options_files_merge_rule_by_rule_with_each_rule_replaced_whole(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD013": { "line_length": 200 }, "MD041": false } }')
    write(tmp_path, "sub/.markdownlint-cli2.jsonc", '{ "config": { "MD013": { "tables": false } } }')
    write(tmp_path, "sub/b.md", BREAKABLE)
    assert config_for(tmp_path, "sub/b.md") == {"MD013": {"tables": False}, "MD041": False}


def test_options_keys_outside_config_are_replaced_by_the_nearer_file(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "ignores": ["a/**"], "noInlineConfig": true }')
    write(tmp_path, "sub/.markdownlint-cli2.jsonc", '{ "ignores": ["b/**"] }')
    write(tmp_path, "sub/b.md", "")
    options = configuration_for(tmp_path / "sub/b.md", cwd=tmp_path).options
    assert dict(options) == {"ignores": ["b/**"], "noInlineConfig": True}


def test_an_empty_options_object_inherits_everything(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD013": { "line_length": 200 }, "MD041": false } }')
    write(tmp_path, "sub/.markdownlint-cli2.jsonc", "{}")
    write(tmp_path, "sub/f.md", BREAKABLE)
    assert config_for(tmp_path, "sub/f.md") == {"MD013": {"line_length": 200}, "MD041": False}


def test_a_config_file_replaces_the_merged_configuration_outright(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD013": { "line_length": 200 }, "MD041": false } }')
    write(tmp_path, "replace/.markdownlint.jsonc", '{ "MD041": false }')
    write(tmp_path, "replace/d.md", BREAKABLE)
    assert config_for(tmp_path, "replace/d.md") == {"MD041": False}


def test_a_config_file_beside_an_options_file_wins(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    write(tmp_path, "both/.markdownlint-cli2.jsonc", '{ "config": { "MD013": false } }')
    write(tmp_path, "both/.markdownlint.jsonc", '{ "MD041": false }')
    write(tmp_path, "both/e.md", BREAKABLE)
    assert config_for(tmp_path, "both/e.md") == {"MD041": False}


def test_a_config_file_beside_an_options_file_applies_below_until_an_options_file_intervenes(tmp_path: Path) -> None:
    # Observed: markdownlint-cli2 folds a directory holding no file of either
    # kind into the nearest ancestor that does, so the ancestor's own
    # configuration file wins there as it does for the ancestor's own files,
    # while any options file below, even one setting no config, makes the
    # ancestor's options file's config win instead.
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD013": false } }')
    write(tmp_path, ".markdownlint.jsonc", '{ "MD041": false }')
    write(tmp_path, "a.md", BREAKABLE)
    write(tmp_path, "empty/deeper/c.md", BREAKABLE)
    write(tmp_path, "optsonly/.markdownlint-cli2.jsonc", '{ "ignores": [] }')
    write(tmp_path, "optsonly/d.md", BREAKABLE)
    write(tmp_path, "optsconfig/.markdownlint-cli2.jsonc", '{ "config": { "MD012": false } }')
    write(tmp_path, "optsconfig/e.md", BREAKABLE)
    assert config_for(tmp_path, "a.md") == {"MD041": False}
    assert config_for(tmp_path, "empty/deeper/c.md") == {"MD041": False}
    assert config_for(tmp_path, "optsonly/d.md") == {"MD013": False}
    assert config_for(tmp_path, "optsconfig/e.md") == {"MD013": False, "MD012": False}


def test_a_parent_config_file_is_inherited_only_until_an_options_file_sets_config(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint.jsonc", '{ "MD041": false }')
    write(tmp_path, "inherits/.markdownlint-cli2.jsonc", '{ "ignores": [] }')
    write(tmp_path, "inherits/a.md", "")
    write(tmp_path, "sets/.markdownlint-cli2.jsonc", '{ "config": { "MD013": false } }')
    write(tmp_path, "sets/b.md", "")
    assert config_for(tmp_path, "inherits/a.md") == {"MD041": False}
    assert config_for(tmp_path, "sets/b.md") == {"MD013": False}


def test_an_empty_config_file_resets_to_the_defaults(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    write(tmp_path, "yamlempty/.markdownlint.yaml", "")
    write(tmp_path, "yamlempty/e.md", "")
    assert config_for(tmp_path, "yamlempty/e.md") == {}


def test_an_empty_yaml_options_file_is_an_error(tmp_path: Path) -> None:
    write(tmp_path, "yamlopts/.markdownlint-cli2.yaml", "")
    write(tmp_path, "yamlopts/f.md", "")
    with pytest.raises(ConfigurationError, match="expected a document, but the input is empty"):
        configuration_for(tmp_path / "yamlopts/f.md", cwd=tmp_path)


def test_a_null_options_file_is_absent(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    write(tmp_path, "sub/.markdownlint-cli2.jsonc", "null")
    write(tmp_path, "sub/a.md", "")
    assert config_for(tmp_path, "sub/a.md") == {"MD041": False}


def test_an_options_file_that_holds_no_object_is_refused(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", "[1, 2]")
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match="holds an array where an options object is expected"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


# --- extends -----------------------------------------------------------------


def test_extends_resolves_a_path_beside_the_file_and_the_file_wins(tmp_path: Path) -> None:
    write(tmp_path, "shared/base.jsonc", '{ "MD013": false, "MD041": false }')
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "extends": "./shared/base.jsonc", "MD041": true } }')
    write(tmp_path, "a.md", "")
    assert config_for(tmp_path, "a.md") == {"MD013": False, "MD041": True}


def test_extends_resolves_a_module_by_nodes_rules_from_the_files_directory(tmp_path: Path) -> None:
    write(tmp_path, "node_modules/preset-a/package.json", '{ "name": "preset-a", "main": "a.jsonc" }')
    write(tmp_path, "node_modules/preset-a/a.jsonc", '{ "MD013": false, "MD041": true }')
    write(tmp_path, "node_modules/preset-b/package.json", '{ "name": "preset-b", "main": "index.js" }')
    write(tmp_path, "node_modules/preset-b/index.js", '{ "extends": "preset-a", "MD041": false }')
    write(tmp_path, "ext/local.jsonc", '{ "extends": "preset-b" }')
    write(tmp_path, "ext/.markdownlint-cli2.jsonc", '{ "config": { "extends": "./local.jsonc" } }')
    write(tmp_path, "ext/g.md", "")
    write(tmp_path, "ext/inner/.markdownlint.yaml", "extends: preset-b\n")
    write(tmp_path, "ext/inner/h.md", "")
    assert config_for(tmp_path, "ext/g.md") == {"MD013": False, "MD041": False}
    assert config_for(tmp_path, "ext/inner/h.md") == {"MD013": False, "MD041": False}


@pytest.mark.parametrize(
    ("reference", "files"),
    [
        ("preset", {"node_modules/preset/index.js": '{ "MD041": false }'}),
        ("preset/rules", {"node_modules/preset/rules.json": '{ "MD041": false }'}),
        ("preset/rules.jsonc", {"node_modules/preset/rules.jsonc": '{ "MD041": false }'}),
        ("@scope/preset", {"node_modules/@scope/preset/package.json": '{ "main": "lib" }', "node_modules/@scope/preset/lib/index.json": '{ "MD041": false }'}),
    ],
)
def test_extends_finds_a_module_as_a_file_or_a_directory(tmp_path: Path, reference: str, files: dict[str, str]) -> None:
    for relative, text in files.items():
        write(tmp_path, relative, text)
    write(tmp_path, "docs/.markdownlint.jsonc", f'{{ "extends": "{reference}" }}')
    write(tmp_path, "docs/a.md", "")
    assert config_for(tmp_path, "docs/a.md") == {"MD041": False}


def test_extends_looks_in_node_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(tmp_path, "elsewhere/preset/index.js", '{ "MD041": false }')
    monkeypatch.setenv("NODE_PATH", str(tmp_path / "elsewhere"))
    write(tmp_path, "docs/.markdownlint.jsonc", '{ "extends": "preset" }')
    write(tmp_path, "docs/a.md", "")
    assert config_for(tmp_path, "docs/a.md") == {"MD041": False}


def test_extends_expands_a_leading_tilde(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    write(tmp_path, "home/base.yaml", "MD041: false\n")
    write(tmp_path, "docs/.markdownlint.jsonc", '{ "extends": "~/base.yaml" }')
    write(tmp_path, "docs/a.md", "")
    assert config_for(tmp_path, "docs/a.md") == {"MD041": False}


def test_an_extends_that_resolves_nowhere_names_the_path_it_tried(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "extends": "missing-preset" } }')
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match="missing-preset"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


def test_an_extends_cycle_is_an_error(tmp_path: Path) -> None:
    write(tmp_path, "a.jsonc", '{ "extends": "./b.jsonc" }')
    write(tmp_path, "b.jsonc", '{ "extends": "./a.jsonc" }')
    write(tmp_path, ".markdownlint.jsonc", '{ "extends": "./a.jsonc" }')
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match="leads back to itself"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


# --- the formats -------------------------------------------------------------


def test_a_config_file_is_parsed_as_jsonc_then_toml_then_yaml_whatever_its_name(tmp_path: Path) -> None:
    write(tmp_path, "json/.markdownlint.yaml", '{ "MD041": false, } // trailing comma and comment')
    write(tmp_path, "json/a.md", "")
    write(tmp_path, "toml/.markdownlint.json", "MD041 = false\n")
    write(tmp_path, "toml/a.md", "")
    write(tmp_path, "yaml/.markdownlint.jsonc", "MD041: false\n")
    write(tmp_path, "yaml/a.md", "")
    write(tmp_path, "scalar/.markdownlint.yaml", "just text\n")
    write(tmp_path, "scalar/a.md", "")
    assert config_for(tmp_path, "json/a.md") == {"MD041": False}
    assert config_for(tmp_path, "toml/a.md") == {"MD041": False}
    assert config_for(tmp_path, "yaml/a.md") == {"MD041": False}
    assert config_for(tmp_path, "scalar/a.md") == {}


def test_an_options_file_is_parsed_by_its_name_alone(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", "config:\n  MD041: false\n")
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match=r"Unable to use configuration file"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


def test_a_config_file_no_parser_accepts_names_every_parser(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint.jsonc", "{ this is nothing\n")
    write(tmp_path, "a.md", "")
    with pytest.raises(ConfigurationError, match=r"Unable to parse .*parse_jsonc.*loads.*parse_yaml"):
        configuration_for(tmp_path / "a.md", cwd=tmp_path)


# --- the plugin --------------------------------------------------------------


def test_update_mdit_keeps_the_files_configuration_on_the_parser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(tmp_path, ".markdownlint-cli2.jsonc", '{ "config": { "MD041": false } }')
    write(tmp_path, "sub/.markdownlint.jsonc", '{ "MD013": false }')
    write(tmp_path, "sub/a.md", "")
    monkeypatch.chdir(tmp_path)
    for filename, expected in (("sub/a.md", {"MD013": False}), ("", {"MD041": False}), ("-", {"MD041": False})):
        mdit = MarkdownIt()
        mdit.options["mdformat"] = {"filename": filename}
        mdformat_markdownlint.update_mdit(mdit)
        assert dict(mdit.options[mdformat_markdownlint.CONFIGURATION_OPTION].config) == expected


def test_mdformat_stops_on_a_javascript_configuration_and_says_so(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.mjs", "export default {};")
    document = write(tmp_path, "a.md", "# Title\n")
    proc = subprocess.run(
        [sys.executable, "-m", "mdformat", "--extensions", "markdownlint", "a.md"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert proc.returncode != 0
    assert ".markdownlint-cli2.mjs: a JavaScript configuration file is not read" in proc.stderr
    assert document.read_text() == "# Title\n"


def test_mdformat_formats_under_a_readable_configuration(tmp_path: Path) -> None:
    write(tmp_path, ".markdownlint-cli2.yaml", "config:\n  MD041: false\n")
    document = write(tmp_path, "a.md", "Title\n=====\n")
    proc = subprocess.run(
        [sys.executable, "-m", "mdformat", "--extensions", "markdownlint", "a.md"],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert document.read_text() == "# Title\n"
