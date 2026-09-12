"""The plugin is installed, registered, and loadable with the contract's extensions."""

from __future__ import annotations

import mdformat
import mdformat.plugins

import mdformat_markdownlint
from conftest import CONTRACT_EXTENSIONS, PLUGIN_EXTENSION


def test_the_entry_point_registers_the_plugin() -> None:
    assert mdformat.plugins.PARSER_EXTENSIONS[PLUGIN_EXTENSION] is mdformat_markdownlint


def test_formatting_with_the_plugin_enabled() -> None:
    extensions = {*CONTRACT_EXTENSIONS, PLUGIN_EXTENSION}
    assert mdformat.text("# Title\n", extensions=extensions) == "# Title\n"
