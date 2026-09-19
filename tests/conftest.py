"""The corpus harness: format a case with the plugin, lint it, assert its status.

Both tools run as the subprocesses an adopter runs, so a case exercises the
entry point, mdformat's option handling and markdownlint-cli2's configuration
discovery rather than an in-process shortcut. The case format and the
assertion each status makes are documented in docs/reference/corpus.md.
"""

from __future__ import annotations

import importlib.metadata
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

TESTS_DIR = Path(__file__).resolve().parent
CORPUS_DIR = TESTS_DIR / "corpus"
# Documents more than one case runs, each named from case.toml by `from` and
# copied into the case's temporary copy, so a document that behaves in a known
# way under several configurations is written once and every case that names
# it is the same bytes.
DOCUMENTS_DIR = TESTS_DIR / "documents"
MARKDOWNLINT_CLI2 = TESTS_DIR / "node_modules" / ".bin" / "markdownlint-cli2"
# The package the binary belongs to: Node resolves markdownlint from here, so
# the rule list read for the corpus is the one markdownlint-cli2 runs.
MARKDOWNLINT_CLI2_PACKAGE = TESTS_DIR / "node_modules" / "markdownlint-cli2"
MATRIX = TESTS_DIR.parent / "docs" / "reference" / "compatibility-matrix.md"

# The rules the corpus knows: every rule markdownlint 0.41.1 ships, each with
# its rows in the compatibility matrix. A rule ID outside this set is a
# failure, not a skip (ADR-002): a case naming one does not load, a finding
# markdownlint reports for one fails the document it is on, and the rule list
# the installed markdownlint ships is compared with it whole, so a rule a new
# release adds or drops fails the latest leg before an adopter meets it.
KNOWN_RULES = frozenset(
    f"MD{number:03d}"
    for number in range(1, 61)
    if number not in {2, 6, 8, 15, 16, 17, 57}
)

# The extension set the compatibility contract is stated for, and the plugin's
# own extension, passed explicitly so a run does not depend on what else is
# installed. Each case is formatted twice, without and with the plugin, so a
# status claims no more than the run that earns it: guaranteed holds by
# mdformat alone, bridged holds only once the plugin is added.
CONTRACT_EXTENSIONS = ("gfm", "tables", "frontmatter")
PLUGIN_EXTENSION = "markdownlint"

# The statuses ADR-002 defines that the harness can assert today. Unsatisfiable
# joins them when the plugin's refusal lands.
STATUSES = ("guaranteed", "neutral", "bridged")

_FINDING = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<column>\d+))? "
    r"(?P<severity>error|warning) (?P<rule>MD\d{3})/(?P<names>\S+) (?P<detail>.*)$"
)


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    detail: str


@dataclass(frozen=True)
class Input:
    """One document of a case: where its bytes come from, the case's own
    directory or the shared pool; the status it asserts, the case's unless the
    document is a construct the row excepts; how many findings it reports
    before formatting, for the case's rule or for any rule when the case names
    none; the rules beside the case's that it reports on some run
    (`incidental`), each on the construct itself, and outside which no rule
    may appear; and whether mdformat must write it back byte for byte
    (`unchanged`) or must not (`rewritten`)."""

    name: str
    source: Path
    status: str
    findings: int
    incidental: frozenset[str]
    unchanged: bool
    rewritten: bool

    @property
    def shared(self) -> bool:
        return self.source.parent == DOCUMENTS_DIR


@dataclass(frozen=True)
class Case:
    name: str
    directory: Path
    status: str
    rule: str | None
    inputs: tuple[Input, ...]


@dataclass(frozen=True)
class FormatResult:
    returncode: int
    stderr: str


def load_case(directory: Path) -> Case:
    manifest = directory / "case.toml"
    with manifest.open("rb") as handle:
        data = tomllib.load(handle)
    status = data.get("status")
    if status not in STATUSES:
        raise ValueError(
            f"{manifest}: status must be one of {STATUSES}, not {status!r}"
        )
    rule = data.get("rule")
    if rule is not None and rule not in KNOWN_RULES:
        raise ValueError(
            f"{manifest}: the corpus does not know the rule {rule!r}; a rule it knows "
            "is one markdownlint ships, MD001 to MD060 less the retired IDs"
        )
    if status == "bridged" and rule is None:
        raise ValueError(f"{manifest}: a bridged case names the rule the plugin holds")
    table = data.get("inputs")
    if not isinstance(table, dict) or not table:
        raise ValueError(f"{manifest}: a case lists each of its documents under [inputs.<file>]")
    present = sorted(path.name for path in directory.glob("*.md"))
    local = sorted(
        name for name, spec in table.items() if not (isinstance(spec, dict) and "from" in spec)
    )
    if local != present:
        raise ValueError(
            f"{manifest}: [inputs] lists {local} of its own but the directory holds {present}"
        )
    inputs = []
    for name, spec in table.items():
        shared = spec.get("from") if isinstance(spec, dict) else None
        if shared is None:
            source = directory / name
        else:
            if not isinstance(shared, str) or "/" in shared or not shared.endswith(".md"):
                raise ValueError(
                    f"{manifest}: inputs.{name}.from names a document in {DOCUMENTS_DIR}"
                )
            source = DOCUMENTS_DIR / shared
            if not source.is_file():
                raise ValueError(f"{manifest}: inputs.{name}.from names {source}, which is missing")
        # A document may carry its own status where its construct is the
        # exception to the rule's row under the same configuration, so a case
        # stays named for the configuration its documents share; a case naming
        # no rule counts every finding, and an override there says nothing.
        own_status = spec.get("status", status) if isinstance(spec, dict) else None
        if own_status not in STATUSES:
            raise ValueError(
                f"{manifest}: inputs.{name}.status must be one of {STATUSES}, not {own_status!r}"
            )
        if own_status != status and rule is None:
            raise ValueError(
                f"{manifest}: inputs.{name}.status overrides the case's, but a case naming "
                "no rule counts every finding and has no row for a document to except"
            )
        findings = spec.get("findings") if isinstance(spec, dict) else None
        incidental = spec.get("incidental", []) if isinstance(spec, dict) else None
        unchanged = spec.get("unchanged", False) if isinstance(spec, dict) else None
        rewritten = spec.get("rewritten", False) if isinstance(spec, dict) else None
        if not isinstance(findings, int) or isinstance(findings, bool) or findings < 0:
            raise ValueError(f"{manifest}: inputs.{name}.findings must be a count")
        # The rules the document reports beside the case's, listed so that a
        # rule outside the list fails it rather than being filtered away with
        # the findings the case is not about; a case naming no rule counts
        # every finding, so nothing is beside it.
        if not isinstance(incidental, list) or not all(
            isinstance(item, str) for item in incidental
        ):
            raise ValueError(f"{manifest}: inputs.{name}.incidental lists rule IDs")
        if incidental and rule is None:
            raise ValueError(
                f"{manifest}: inputs.{name}.incidental lists rules beside the case's, but a "
                "case naming no rule counts every finding and has none beside it"
            )
        unknown = sorted(set(incidental) - KNOWN_RULES)
        if unknown:
            raise ValueError(
                f"{manifest}: the corpus does not know the rule {unknown[0]!r}, which "
                f"inputs.{name}.incidental lists"
            )
        if rule in incidental:
            raise ValueError(
                f"{manifest}: inputs.{name}.incidental lists {rule}, the case's own rule"
            )
        if len(set(incidental)) != len(incidental):
            raise ValueError(f"{manifest}: inputs.{name}.incidental lists a rule twice")
        if not isinstance(unchanged, bool) or not isinstance(rewritten, bool):
            raise ValueError(
                f"{manifest}: inputs.{name}.unchanged and .rewritten must be true or false"
            )
        if unchanged and rewritten:
            raise ValueError(f"{manifest}: inputs.{name} cannot be both unchanged and rewritten")
        inputs.append(
            Input(
                name=name,
                source=source,
                status=own_status,
                findings=findings,
                incidental=frozenset(incidental),
                unchanged=unchanged,
                rewritten=rewritten,
            )
        )
    if rule is not None and not any(item.findings for item in inputs):
        raise ValueError(
            f"{manifest}: a case naming a rule needs a document that violates it, "
            "or it proves nothing"
        )
    return Case(
        name=directory.name,
        directory=directory,
        status=status,
        rule=rule,
        inputs=tuple(inputs),
    )


def cases() -> list[Case]:
    loaded = [load_case(path) for path in sorted(CORPUS_DIR.iterdir()) if path.is_dir()]
    used = {item.source for case in loaded for item in case.inputs if item.shared}
    unused = sorted(path.name for path in DOCUMENTS_DIR.glob("*.md") if path not in used)
    if unused:
        raise ValueError(f"{DOCUMENTS_DIR}: no case names {unused}; a pooled document is shared or removed")
    return loaded


def materialise(case: Case, work: Path) -> None:
    """Copy the case directory to `work`, then the pooled documents it names
    under the names its manifest gives them, so the copy is a whole case."""
    shutil.copytree(case.directory, work)
    for item in case.inputs:
        if item.shared:
            shutil.copyfile(item.source, work / item.name)


def format_file(path: Path, *, with_plugin: bool) -> FormatResult:
    """Run mdformat on one file, in place, with the contract's extension set,
    and with this plugin added when asked."""
    extensions = CONTRACT_EXTENSIONS + ((PLUGIN_EXTENSION,) if with_plugin else ())
    command = [sys.executable, "-m", "mdformat"]
    for extension in extensions:
        command += ["--extensions", extension]
    command.append(path.name)
    proc = subprocess.run(
        command, cwd=path.parent, capture_output=True, text=True, check=False
    )
    return FormatResult(returncode=proc.returncode, stderr=proc.stderr)


def lint_file(markdownlint: Path, path: Path) -> list[Finding]:
    """Run markdownlint-cli2 on one file from its own directory, so the case's
    own configuration, if any, is the one it reads."""
    proc = subprocess.run(
        [str(markdownlint), path.name],
        cwd=path.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"markdownlint-cli2 failed on {path}:\n{proc.stdout}\n{proc.stderr}"
        )
    findings = []
    for line in (proc.stdout + proc.stderr).splitlines():
        match = _FINDING.match(line)
        if match:
            findings.append(
                Finding(
                    line=int(match["line"]),
                    rule=match["rule"],
                    detail=match["detail"],
                )
            )
    unknown = sorted({finding.rule for finding in findings} - KNOWN_RULES)
    if unknown:
        pytest.fail(
            f"markdownlint reported {unknown} on {path}, which the corpus does not "
            "know: a new rule needs its rows in the matrix and its cases here"
        )
    return findings


def select(findings: list[Finding], rule: str | None) -> list[Finding]:
    """The findings a case is about: every finding when it names no rule."""
    if rule is None:
        return findings
    return [finding for finding in findings if finding.rule == rule]


def count_by_rule(findings: list[Finding]) -> Counter[str]:
    return Counter(finding.rule for finding in findings)


def markdownlint_rules() -> frozenset[str]:
    """The rule IDs the installed markdownlint ships, read from its rule
    module by path since the package does not export the list, and resolved
    from markdownlint-cli2's own directory so it is the markdownlint that
    binary runs."""
    script = (
        'const path = require("path");'
        'const rules = path.join(path.dirname(require.resolve("markdownlint")), "rules.mjs");'
        "import(rules).then((m) => console.log(m.default.map((r) => r.names[0]).join(\"\\n\")));"
    )
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=MARKDOWNLINT_CLI2_PACKAGE,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"listing markdownlint's rules failed:\n{proc.stderr}")
    return frozenset(proc.stdout.split())


def matrix_rules() -> frozenset[str]:
    """The rule IDs the compatibility matrix has a row for."""
    return frozenset(re.findall(r"^\| (MD\d{3}) ", MATRIX.read_text(), re.MULTILINE))


def markdownlint_version() -> str:
    proc = subprocess.run(
        [str(MARKDOWNLINT_CLI2), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or proc.stderr).strip().splitlines()[0]


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Name the versions a run is against, so a CI log is the record of them."""
    python_side = ", ".join(
        f"{name} {importlib.metadata.version(name)}"
        for name in ("mdformat", "mdformat-gfm", "mdformat-frontmatter")
    )
    node_side = (
        markdownlint_version()
        if MARKDOWNLINT_CLI2.exists()
        else f"{MARKDOWNLINT_CLI2} is missing"
    )
    return [f"corpus versions: {python_side}; {node_side}"]


@pytest.fixture(scope="session")
def markdownlint() -> Path:
    if not MARKDOWNLINT_CLI2.exists():
        pytest.fail(
            f"{MARKDOWNLINT_CLI2} is missing: install the corpus's markdownlint "
            "side with `npm ci --prefix tests` (docs/runbooks/running-the-corpus.md)"
        )
    return MARKDOWNLINT_CLI2
