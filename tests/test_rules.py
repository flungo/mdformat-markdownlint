"""A rule ID the corpus does not know is a failure, not a skip (ADR-002).

The corpus knows the rules markdownlint 0.41.1 ships, `KNOWN_RULES`, and each
has its rows in the compatibility matrix. Three things hold that set honest:
the installed markdownlint ships exactly those rules, which is what fails the
latest leg when a release adds or drops one; a case cannot name a rule outside
it; and a finding for a rule outside it fails the document it is on, rather
than being filtered away by the case's rule.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import (
    KNOWN_RULES,
    lint_file,
    load_case,
    markdownlint_rules,
    matrix_rules,
)


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
