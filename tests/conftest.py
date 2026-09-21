"""The corpus harness: format a case with the plugin, lint it, assert its status.

Both tools run as the subprocesses an adopter runs, so a case exercises the
entry point, mdformat's option handling and markdownlint-cli2's configuration
discovery rather than an in-process shortcut. The case format and the
assertion each status makes are documented in docs/reference/corpus.md.

Neither tool is launched per document. A document's share of the work is under
two milliseconds of linting and less formatting, against a quarter-second of
process startup, so the corpus is built into one tree and each tool is run over
it whole: markdownlint-cli2 applies the configuration nearest each file, which
is the case's own, and mdformat formats each file independently of the rest
(ADR-005). `run_document` keeps the per-document pipeline for a case built
outside the corpus and for attributing a batched failure.
"""

from __future__ import annotations

import importlib.metadata
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
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
        # Every document declares the fixed point or the rewrite, so neither is
        # assumed: exactly one of the two is true.
        if not isinstance(unchanged, bool) or not isinstance(rewritten, bool):
            raise ValueError(
                f"{manifest}: inputs.{name}.unchanged and .rewritten must be true or false"
            )
        if unchanged == rewritten:
            raise ValueError(
                f"{manifest}: inputs.{name} declares exactly one of unchanged and rewritten, "
                "so the fixed point or the rewrite is asserted rather than assumed"
            )
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
    # A case extends the config package by name, as an adopter does, and each
    # tool resolves the name by Node's rules from the configuration file's
    # directory, so the copy carries the node_modules the corpus installed
    # beside its configuration, as an adopter's checkout does.
    (work / "node_modules").symlink_to(TESTS_DIR / "node_modules", target_is_directory=True)


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


# The two runs every document is put through, in the order the assertions read
# them: a status claims no more than the run that earns it.
RUNS = (("without the plugin", False), ("with the plugin", True))


@dataclass(frozen=True)
class DocumentRuns:
    """What the pipeline observed for one document: the findings before
    formatting, which are the same for both runs because both start from the
    same bytes, and then per run the findings after formatting, whether the
    bytes changed, and the stderr of a format that did not exit zero."""

    before: tuple[Finding, ...]
    after: dict[str, tuple[Finding, ...]]
    changed: dict[str, bool]
    format_failures: dict[str, str]


def build_tree(loaded: list[Case], root: Path) -> None:
    """Materialise every case under `root`, one directory per case, so a case's
    configuration sits beside its documents exactly as it does in the corpus."""
    root.mkdir(parents=True)
    for case in loaded:
        materialise(case, root / case.name)


def document_paths(loaded: list[Case]) -> list[str]:
    """Every document's path within a built tree, `<case>/<document>`.

    Both tools are given these rather than a glob over the tree: a case's copy
    carries a link to the corpus's `node_modules`, so anything that walks the
    tree reaches the README of every installed package.
    """
    return [
        f"{case.name}/{document.name}" for case in loaded for document in case.inputs
    ]


def lint_tree(markdownlint: Path, tree: Path, paths: list[str]) -> dict[str, list[Finding]]:
    """Lint every document of a built tree in one run, keyed `<case>/<document>`.

    markdownlint-cli2 resolves configuration by walking up from each file, so a
    case directory's own `.markdownlint-cli2.jsonc` governs its documents and
    no others; the tree's root holds none for anything to inherit.
    """
    proc = subprocess.run(
        [str(markdownlint), *paths],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"markdownlint-cli2 failed on {tree}:\n{proc.stdout}\n{proc.stderr}"
        )
    findings: dict[str, list[Finding]] = {}
    for line in (proc.stdout + proc.stderr).splitlines():
        match = _FINDING.match(line)
        if match:
            findings.setdefault(match["file"].replace("\\", "/"), []).append(
                Finding(
                    line=int(match["line"]),
                    rule=match["rule"],
                    detail=match["detail"],
                )
            )
    return findings


def format_tree(tree: Path, paths: list[str], *, with_plugin: bool) -> FormatResult:
    """Format every document of a built tree in one run. mdformat treats each
    file independently, so this is the per-file run repeated, not a new one."""
    extensions = CONTRACT_EXTENSIONS + ((PLUGIN_EXTENSION,) if with_plugin else ())
    command = [sys.executable, "-m", "mdformat"]
    for extension in extensions:
        command += ["--extensions", extension]
    command += paths
    proc = subprocess.run(
        command, cwd=tree, capture_output=True, text=True, check=False
    )
    return FormatResult(returncode=proc.returncode, stderr=proc.stderr)


def attribute_format_failure(
    loaded: list[Case], root: Path, *, with_plugin: bool
) -> dict[str, str]:
    """Which documents a failed tree format belongs to, found by formatting a
    fresh tree one document at a time. Only a non-zero exit reaches here, so the
    cost is paid on the way to a failure report and nowhere else."""
    build_tree(loaded, root)
    failures: dict[str, str] = {}
    for case in loaded:
        for document in case.inputs:
            result = format_file(root / case.name / document.name, with_plugin=with_plugin)
            if result.returncode != 0:
                failures[f"{case.name}/{document.name}"] = result.stderr
    return failures


def run_corpus(loaded: list[Case], markdownlint: Path, root: Path) -> dict[str, DocumentRuns]:
    """Put the whole corpus through the pipeline, five subprocesses in all:
    lint the unformatted tree once, then per run format a tree and lint it."""
    paths = document_paths(loaded)
    pristine = root / "pristine"
    build_tree(loaded, pristine)
    before = lint_tree(markdownlint, pristine, paths)

    after: dict[str, dict[str, list[Finding]]] = {}
    changed: dict[str, dict[str, bool]] = {}
    failures: dict[str, dict[str, str]] = {}
    for run, with_plugin in RUNS:
        tree = root / run.replace(" ", "-")
        build_tree(loaded, tree)
        result = format_tree(tree, paths, with_plugin=with_plugin)
        failures[run] = (
            attribute_format_failure(
                loaded, root / f"attribute-{run.replace(' ', '-')}", with_plugin=with_plugin
            )
            if result.returncode != 0
            else {}
        )
        after[run] = lint_tree(markdownlint, tree, paths)
        changed[run] = {
            f"{case.name}/{document.name}": (
                (tree / case.name / document.name).read_bytes()
                != (pristine / case.name / document.name).read_bytes()
            )
            for case in loaded
            for document in case.inputs
        }

    return {
        key: DocumentRuns(
            before=tuple(before.get(key, ())),
            after={run: tuple(after[run].get(key, ())) for run, _ in RUNS},
            changed={run: changed[run][key] for run, _ in RUNS},
            format_failures={
                run: failures[run][key] for run, _ in RUNS if key in failures[run]
            },
        )
        for case in loaded
        for key in (f"{case.name}/{document.name}" for document in case.inputs)
    }


def run_document(
    case: Case, document: Input, root: Path, markdownlint: Path
) -> DocumentRuns:
    """The same pipeline for one document, a copy of its whole case per run.

    The corpus goes through `run_corpus`; this is for a case built outside it,
    which has no tree to join.
    """
    before: tuple[Finding, ...] | None = None
    after: dict[str, tuple[Finding, ...]] = {}
    changed: dict[str, bool] = {}
    failures: dict[str, str] = {}
    for run, with_plugin in RUNS:
        work = root / run.replace(" ", "-")
        materialise(case, work)
        target = work / document.name
        original = target.read_bytes()
        if before is None:
            before = tuple(lint_file(markdownlint, target))
        result = format_file(target, with_plugin=with_plugin)
        if result.returncode != 0:
            failures[run] = result.stderr
        after[run] = tuple(lint_file(markdownlint, target))
        changed[run] = target.read_bytes() != original
    assert before is not None
    return DocumentRuns(
        before=before, after=after, changed=changed, format_failures=failures
    )


def select(findings: Sequence[Finding], rule: str | None) -> list[Finding]:
    """The findings a case is about: every finding when it names no rule."""
    if rule is None:
        return list(findings)
    return [finding for finding in findings if finding.rule == rule]


def count_by_rule(findings: Sequence[Finding]) -> Counter[str]:
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


@pytest.fixture(scope="session")
def corpus(
    markdownlint: Path, tmp_path_factory: pytest.TempPathFactory
) -> dict[str, DocumentRuns]:
    """Every document's runs, from one pass over the whole corpus."""
    return run_corpus(
        cases(), markdownlint, tmp_path_factory.mktemp("corpus")
    )
