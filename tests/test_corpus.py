"""One test per corpus case: format without and with the plugin, lint, assert the status."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import (
    Finding,
    cases,
    count_by_rule,
    format_file,
    lint_file,
    load_case,
    select,
)

CASES = cases()


def test_the_corpus_is_not_empty() -> None:
    assert CASES, "the corpus has no cases"


def _format_and_lint(
    case_dir: Path, work: Path, markdownlint: Path, *, with_plugin: bool
) -> tuple[list[Finding], list[Finding]]:
    """Lint the case's input, format a fresh copy of it, lint it again."""
    shutil.copytree(case_dir, work)
    target = work / "input.md"
    before = lint_file(markdownlint, target)
    result = format_file(target, with_plugin=with_plugin)
    assert result.returncode == 0, (
        f"mdformat failed on {case_dir.name} "
        f"({'with' if with_plugin else 'without'} the plugin):\n{result.stderr}"
    )
    return before, lint_file(markdownlint, target)


@pytest.mark.parametrize("case_dir", CASES, ids=[path.name for path in CASES])
def test_case(case_dir: Path, tmp_path: Path, markdownlint: Path) -> None:
    case = load_case(case_dir)
    before, alone = _format_and_lint(
        case.directory, tmp_path / "without", markdownlint, with_plugin=False
    )
    _, with_plugin = _format_and_lint(
        case.directory, tmp_path / "with", markdownlint, with_plugin=True
    )
    alone = select(alone, case.rule)
    with_plugin = select(with_plugin, case.rule)

    if case.status == "guaranteed":
        if case.rule is None:
            # A case naming no rule is a baseline case: a document that lints
            # clean before formatting must lint clean after it (ADR-002).
            assert not before, f"{case.name}: the input is not clean before formatting: {before}"
        assert not alone, (
            f"{case.name}: guaranteed, but mdformat alone reports {alone}; "
            "if the plugin holds the rule, the case is bridged"
        )
        assert not with_plugin, (
            f"{case.name}: guaranteed by mdformat alone, but with the plugin the "
            f"formatted file reports {with_plugin}: the plugin broke it"
        )
    elif case.status == "bridged":
        assert alone, (
            f"{case.name}: bridged, but mdformat alone already satisfies {case.rule}; "
            "the case is guaranteed"
        )
        assert not with_plugin, (
            f"{case.name}: bridged, but with the plugin the formatted file still "
            f"reports {with_plugin}"
        )
    elif case.status == "neutral":
        expected = count_by_rule(select(before, case.rule))
        assert count_by_rule(alone) == expected, (
            f"{case.name}: neutral, but mdformat alone changed the findings"
        )
        assert count_by_rule(with_plugin) == expected, (
            f"{case.name}: neutral, but the plugin changed the findings"
        )
    else:  # pragma: no cover
        raise AssertionError(f"unhandled status {case.status}")
