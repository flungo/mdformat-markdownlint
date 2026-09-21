"""One test per corpus document: lint, format without and with the plugin, lint again.

The runs come from one pass over the whole corpus (`conftest.run_corpus`); the
assertions below read that pass and are the same ones a case built outside the
corpus meets through `check_document`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import (
    RUNS,
    Case,
    DocumentRuns,
    Input,
    cases,
    count_by_rule,
    run_document,
    select,
)

CASES = cases()
DOCUMENTS = [(case, document) for case in CASES for document in case.inputs]


def test_the_corpus_is_not_empty() -> None:
    assert DOCUMENTS, "the corpus has no documents"


def check_document(case: Case, document: Input, runs: DocumentRuns) -> None:
    """Assert the document's status against what the pipeline observed."""
    label = f"{case.name}/{document.name}"
    subject = case.rule or "any rule"
    reported: set[str] = set()

    def beside_the_subject(findings: tuple, when: str) -> None:
        """A document reports no rule but the case's and the ones its entry
        lists as incidental; a case naming no rule counts every finding, so
        its status asserts them all and nothing is beside the subject."""
        reported.update(finding.rule for finding in findings)
        if case.rule is None:
            return
        stray = {finding.rule for finding in findings} - {case.rule} - document.incidental
        assert not stray, (
            f"{label}: reports {sorted(stray)} {when}, beside {subject}; a document trips "
            "no rule but its subject unless its entry lists the rule as incidental"
        )

    beside_the_subject(runs.before, "before formatting")
    before = select(runs.before, case.rule)
    assert len(before) == document.findings, (
        f"{label}: expected {document.findings} finding(s) for {subject} before "
        f"formatting, found {len(before)}: {before}"
    )

    outcomes: dict[str, list] = {}
    for run, _ in RUNS:
        assert run not in runs.format_failures, (
            f"mdformat failed on {label} {run}:\n{runs.format_failures[run]}"
        )
        beside_the_subject(runs.after[run], f"after formatting {run}")
        outcomes[run] = select(runs.after[run], case.rule)
        if document.unchanged:
            assert not runs.changed[run], (
                f"{label}: declared unchanged, but formatting {run} rewrote it"
            )
        if document.rewritten:
            assert runs.changed[run], (
                f"{label}: declared rewritten, but formatting {run} left it as it was"
            )

    alone = outcomes["without the plugin"]
    bridged = outcomes["with the plugin"]

    # The list is exact in both directions: a rule it names that no run
    # reports is a stale entry, and would let the document stop reporting it
    # unnoticed.
    unreported = document.incidental - reported
    assert not unreported, (
        f"{label}: lists {sorted(unreported)} as incidental, but no run reports them; "
        "remove them from the entry"
    )

    # The document's status: the case's, unless the entry excepts it.
    status = document.status
    if status == "guaranteed":
        assert not alone, (
            f"{label}: guaranteed, but mdformat alone leaves {alone}; "
            "if the plugin holds the rule, the case is bridged"
        )
        assert not bridged, (
            f"{label}: guaranteed by mdformat alone, but with the plugin the formatted "
            f"file reports {bridged}: the plugin broke it"
        )
    elif status == "bridged":
        if document.findings:
            assert alone, (
                f"{label}: bridged, but mdformat alone already satisfies {case.rule}; "
                "the case is guaranteed"
            )
        assert not bridged, (
            f"{label}: bridged, but with the plugin the formatted file still reports {bridged}"
        )
    elif status == "neutral":
        expected = count_by_rule(before)
        assert count_by_rule(alone) == expected, (
            f"{label}: neutral, but mdformat alone changed the findings"
        )
        assert count_by_rule(bridged) == expected, (
            f"{label}: neutral, but the plugin changed the findings"
        )
    else:  # pragma: no cover
        raise AssertionError(f"unhandled status {status}")


def check_case_from_scratch(
    case: Case, document: Input, work: Path, markdownlint: Path
) -> None:
    """Run one document's own pipeline and assert it, for a case built outside
    the corpus and so absent from the tree the session fixture builds."""
    check_document(case, document, run_document(case, document, work, markdownlint))


@pytest.mark.parametrize(
    "case,document",
    DOCUMENTS,
    ids=[f"{case.name}/{document.name}" for case, document in DOCUMENTS],
)
def test_document(
    case: Case, document: Input, corpus: dict[str, DocumentRuns]
) -> None:
    check_document(case, document, corpus[f"{case.name}/{document.name}"])
