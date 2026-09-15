"""One test per corpus document: lint, format without and with the plugin, lint again."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import (
    Case,
    Input,
    cases,
    count_by_rule,
    format_file,
    lint_file,
    materialise,
    select,
)

CASES = cases()
DOCUMENTS = [(case, document) for case in CASES for document in case.inputs]


def test_the_corpus_is_not_empty() -> None:
    assert DOCUMENTS, "the corpus has no documents"


@pytest.mark.parametrize(
    "case,document",
    DOCUMENTS,
    ids=[f"{case.name}/{document.name}" for case, document in DOCUMENTS],
)
def test_document(case: Case, document: Input, tmp_path: Path, markdownlint: Path) -> None:
    label = f"{case.name}/{document.name}"
    subject = case.rule or "any rule"
    runs: dict[str, tuple[list, list]] = {}
    for run, with_plugin in (("without the plugin", False), ("with the plugin", True)):
        # A fresh copy of the whole case per run, pooled documents included, so
        # its configuration travels with it; a case that extends the config
        # package by name resolves it from here too, since the corpus's
        # markdownlint-cli2 sits beside the package `npm ci --prefix tests`
        # links from the tree.
        work = tmp_path / run.replace(" ", "-")
        materialise(case, work)
        target = work / document.name
        original = target.read_bytes()

        before = select(lint_file(markdownlint, target), case.rule)
        assert len(before) == document.findings, (
            f"{label}: expected {document.findings} finding(s) for {subject} before "
            f"formatting, found {len(before)}: {before}"
        )
        result = format_file(target, with_plugin=with_plugin)
        assert result.returncode == 0, f"mdformat failed on {label} {run}:\n{result.stderr}"
        after = select(lint_file(markdownlint, target), case.rule)
        if document.unchanged:
            assert target.read_bytes() == original, (
                f"{label}: declared unchanged, but formatting {run} rewrote it"
            )
        if document.rewritten:
            assert target.read_bytes() != original, (
                f"{label}: declared rewritten, but formatting {run} left it as it was"
            )
        runs[run] = (before, after)

    before, alone = runs["without the plugin"]
    _, bridged = runs["with the plugin"]

    if case.status == "guaranteed":
        assert not alone, (
            f"{label}: guaranteed, but mdformat alone leaves {alone}; "
            "if the plugin holds the rule, the case is bridged"
        )
        assert not bridged, (
            f"{label}: guaranteed by mdformat alone, but with the plugin the formatted "
            f"file reports {bridged}: the plugin broke it"
        )
    elif case.status == "bridged":
        if document.findings:
            assert alone, (
                f"{label}: bridged, but mdformat alone already satisfies {case.rule}; "
                "the case is guaranteed"
            )
        assert not bridged, (
            f"{label}: bridged, but with the plugin the formatted file still reports {bridged}"
        )
    elif case.status == "neutral":
        expected = count_by_rule(before)
        assert count_by_rule(alone) == expected, (
            f"{label}: neutral, but mdformat alone changed the findings"
        )
        assert count_by_rule(bridged) == expected, (
            f"{label}: neutral, but the plugin changed the findings"
        )
    else:  # pragma: no cover
        raise AssertionError(f"unhandled status {case.status}")
