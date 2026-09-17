"""The link check reads every corpus document except the ones lychee.toml lists.

Each listed path is a document whose construct is a link the check would
reject, so the list is kept honest: every entry names a corpus or pooled
document that exists, and nothing outside the corpus.
"""

from __future__ import annotations

import sys

from conftest import CORPUS_DIR, DOCUMENTS_DIR, TESTS_DIR

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

REPO_DIR = TESTS_DIR.parent
LYCHEE_CONFIG = REPO_DIR / "lychee.toml"


def excluded_paths() -> list[str]:
    with LYCHEE_CONFIG.open("rb") as handle:
        return tomllib.load(handle).get("exclude_path", [])


def test_every_excluded_path_is_a_corpus_document_that_exists() -> None:
    for entry in excluded_paths():
        path = REPO_DIR / entry
        assert path.is_file(), f"lychee.toml excludes {entry}, which does not exist"
        assert path.suffix == ".md" and (
            path.parent == DOCUMENTS_DIR or path.parent.parent == CORPUS_DIR
        ), f"lychee.toml excludes {entry}, which is not a corpus document"
