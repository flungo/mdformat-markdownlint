"""A rule ID the corpus does not know is a failure, not a skip (ADR-002).

The corpus knows the rules markdownlint 0.41.1 ships, `KNOWN_RULES`, and each
has its rows in the compatibility matrix. Three things hold that set honest:
the installed markdownlint ships exactly those rules, which is what fails the
latest leg when a release adds or drops one; a case cannot name a rule outside
it; and a finding for a rule outside it fails the document it is on, rather
than being filtered away by the case's rule. And every rule the corpus knows
has a case, so a rule can be added to the set only with its cases.

The same holds for a rule the corpus does know: a document reports no rule
but its case's unless its entry lists the rule as incidental, and a listed
rule that no run reports is a stale entry, so a document trips exactly the
rules its entry says it does.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import (
    KNOWN_RULES,
    cases,
    lint_file,
    load_case,
    markdownlint_rules,
    matrix_rules,
)
from test_corpus import test_document as check_document


def test_markdownlint_ships_exactly_the_rules_the_corpus_knows(markdownlint: Path) -> None:
    shipped = markdownlint_rules()
    assert shipped - KNOWN_RULES == set(), (
        f"markdownlint ships {sorted(shipped - KNOWN_RULES)}, which the corpus does not know"
    )
    assert KNOWN_RULES - shipped == set(), (
        f"the corpus knows {sorted(KNOWN_RULES - shipped)}, which markdownlint no longer ships"
    )


def test_the_matrix_has_a_row_for_every_known_rule_and_no_other() -> None:
    assert matrix_rules() == KNOWN_RULES


def test_a_case_naming_an_unknown_rule_does_not_load(tmp_path: Path) -> None:
    case = tmp_path / "md002"
    case.mkdir()
    (case / "case.toml").write_text(
        'status = "neutral"\nrule = "MD002"\n\n[inputs."document.md"]\nfindings = 1\n'
    )
    (case / "document.md").write_text("# A heading\n")
    with pytest.raises(ValueError, match="does not know the rule 'MD002'"):
        load_case(case)


def test_a_finding_for_an_unknown_rule_fails_the_document(
    tmp_path: Path, markdownlint: Path
) -> None:
    # A custom rule under an ID the corpus does not know, reporting on every
    # document, stands in for the rule a future markdownlint adds.
    (tmp_path / "unknown.cjs").write_text(
        "module.exports = {\n"
        '  names: ["MD999", "unknown-to-the-corpus"],\n'
        '  description: "A rule the corpus does not know",\n'
        '  tags: ["test"],\n'
        '  parser: "none",\n'
        '  function: (params, onError) => onError({ lineNumber: 1, detail: "reported" }),\n'
        "};\n"
    )
    (tmp_path / ".markdownlint-cli2.jsonc").write_text(
        '{ "customRules": ["./unknown.cjs"] }\n'
    )
    document = tmp_path / "document.md"
    document.write_text("# A heading\n")
    with pytest.raises(pytest.fail.Exception, match="MD999.*does not know"):
        lint_file(markdownlint, document)


def test_every_known_rule_has_a_case() -> None:
    covered = {case.rule for case in cases() if case.rule}
    assert KNOWN_RULES - covered == set(), (
        f"the corpus knows {sorted(KNOWN_RULES - covered)} but has no case for them"
    )


def write_case(directory: Path, manifest: str, document: str) -> None:
    """A case of one document, `document.md`, under markdownlint's defaults."""
    directory.mkdir()
    (directory / "case.toml").write_text(manifest)
    (directory / "document.md").write_text(document)


def test_a_document_listing_an_unknown_rule_as_incidental_does_not_load(tmp_path: Path) -> None:
    write_case(
        tmp_path / "md026",
        'status = "neutral"\nrule = "MD026"\n\n[inputs."document.md"]\nfindings = 1\n'
        'incidental = ["MD002"]\n',
        "# A heading ending in a period.\n",
    )
    with pytest.raises(ValueError, match="does not know the rule 'MD002'"):
        load_case(tmp_path / "md026")


def test_a_document_listing_its_subject_as_incidental_does_not_load(tmp_path: Path) -> None:
    write_case(
        tmp_path / "md026",
        'status = "neutral"\nrule = "MD026"\n\n[inputs."document.md"]\nfindings = 1\n'
        'incidental = ["MD026"]\n',
        "# A heading ending in a period.\n",
    )
    with pytest.raises(ValueError, match="the case's own rule"):
        load_case(tmp_path / "md026")


def test_a_case_naming_no_rule_refuses_incidental(tmp_path: Path) -> None:
    write_case(
        tmp_path / "baseline",
        'status = "guaranteed"\n\n[inputs."document.md"]\nfindings = 0\n'
        'incidental = ["MD026"]\n',
        "# A heading\n",
    )
    with pytest.raises(ValueError, match="counts every finding"):
        load_case(tmp_path / "baseline")


def test_a_document_reporting_a_rule_beside_its_subject_fails(
    tmp_path: Path, markdownlint: Path
) -> None:
    # Text above the first heading is MD041's, not MD026's, and the entry
    # does not list it.
    write_case(
        tmp_path / "md026",
        'status = "neutral"\nrule = "MD026"\n\n[inputs."document.md"]\nfindings = 1\n'
        "unchanged = true\n",
        "Text before the heading.\n\n# A heading ending in a period.\n",
    )
    case = load_case(tmp_path / "md026")
    with pytest.raises(AssertionError, match=r"reports \['MD041'\] before formatting, beside MD026"):
        check_document(case, case.inputs[0], tmp_path / "work", markdownlint)


def test_a_rule_listed_as_incidental_that_no_run_reports_fails(
    tmp_path: Path, markdownlint: Path
) -> None:
    write_case(
        tmp_path / "md026",
        'status = "neutral"\nrule = "MD026"\n\n[inputs."document.md"]\nfindings = 1\n'
        'incidental = ["MD041"]\nunchanged = true\n',
        "# A heading ending in a period.\n",
    )
    case = load_case(tmp_path / "md026")
    with pytest.raises(AssertionError, match=r"lists \['MD041'\] as incidental, but no run reports"):
        check_document(case, case.inputs[0], tmp_path / "work", markdownlint)
