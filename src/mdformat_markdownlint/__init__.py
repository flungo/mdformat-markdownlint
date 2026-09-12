"""mdformat plugin that keeps mdformat's output in agreement with a markdownlint configuration.

The plugin registers as the ``markdownlint`` parser extension. Its behaviours
land one at a time, each with the corpus entries that prove it, per the
build-out plan; until then it changes nothing, and the corpus's baseline case
is what a formatted file must still satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping

from markdown_it import MarkdownIt
from mdformat.renderer.typing import Postprocess, Render

# The plugin never changes the document's AST: everything it will do is a
# rendering decision or an option derived from the markdownlint configuration.
CHANGES_AST = False

# Renderers replace mdformat's own for a node type and are exclusive across
# plugins; postprocessors chain. Nothing is bridged yet, so both are empty.
RENDERERS: Mapping[str, Render] = {}
POSTPROCESSORS: Mapping[str, Postprocess] = {}


def update_mdit(mdit: MarkdownIt) -> None:
    """Hook for the options the plugin derives from the markdownlint configuration.

    Nothing is derived yet.
    """
