"""mdformat plugin that keeps mdformat's output in agreement with a markdownlint configuration.

The plugin registers as the ``markdownlint`` parser extension. It reads the
markdownlint configuration for the file being formatted the way
markdownlint-cli2 does, and its behaviours, each landing with the corpus
entries that prove it per the build-out plan, act on what it read; until they
land it changes nothing, and the corpus's baseline case is what a formatted
file must still satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from markdown_it import MarkdownIt
from mdformat.renderer.typing import Postprocess, Render

from mdformat_markdownlint._configuration import (
    Configuration,
    ConfigurationError,
    clear_cache,
    configuration_for,
)

__all__ = [
    "CHANGES_AST",
    "CONFIGURATION_OPTION",
    "POSTPROCESSORS",
    "RENDERERS",
    "Configuration",
    "ConfigurationError",
    "clear_cache",
    "configuration_for",
    "update_mdit",
]

# The plugin never changes the document's AST: everything it will do is a
# rendering decision or an option derived from the markdownlint configuration.
CHANGES_AST = False

# Renderers replace mdformat's own for a node type and are exclusive across
# plugins; postprocessors chain. Nothing is bridged yet, so both are empty.
RENDERERS: Mapping[str, Render] = {}
POSTPROCESSORS: Mapping[str, Postprocess] = {}

# Where the configuration read for the file lives on the parser, for every
# behaviour that acts on it: ``mdit.options[CONFIGURATION_OPTION]``.
CONFIGURATION_OPTION = "mdformat_markdownlint"


def update_mdit(mdit: MarkdownIt) -> None:
    """Read the markdownlint configuration for the file mdformat is formatting
    and keep it on the parser.

    mdformat builds a parser per file and names the file in its options;
    standard input and the API's text carry no name and get the working
    directory's configuration, as markdownlint-cli2 gives standard input.
    """
    filename = mdit.options.get("mdformat", {}).get("filename", "")
    path = Path(filename) if filename and filename != "-" else None
    mdit.options[CONFIGURATION_OPTION] = configuration_for(path)
