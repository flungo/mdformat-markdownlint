# The corpus

The test suite that proves the compatibility contract ([ADR-002](../decisions/002-the-compatibility-contract.md)): one input per markdownlint rule and option value, formatted with the plugin and then linted, asserting the status the [compatibility matrix](compatibility-matrix.md) gives that row.
The matrix is the human-readable form of the corpus and the two must agree; a status that changes in one changes in the other in the same pull request.

## Layout

| Path | Purpose |
| -- | -- |
| `tests/corpus/<case>/` | One directory per case, named for what it exercises |
| `tests/corpus/<case>/case.toml` | The case's status, the rule it exercises where it does, and one entry per document |
| `tests/corpus/<case>/*.md` | The documents the case formats and lints. A rule case carries at least one that violates the rule and one already in mdformat's style that formatting must leave byte for byte; a baseline case carries one in mdformat's style and one consistent in the styles mdformat does not write, which markdownlint's defaults accept before and after formatting and the preset reports only before |
| `tests/corpus/<case>/.markdownlint-cli2.jsonc` | The markdownlint configuration the case runs under; absent, markdownlint runs on its defaults. A case about a preset setting extends the config package by name, `markdownlint-config-mdformat`, as an adopter does |
| `markdownlint-config-mdformat/` | The config package the cases extend; `tests/package.json` installs it from the tree, so `npm ci --prefix tests` links it beside the markdownlint-cli2 the harness runs, and Node's resolution finds it from a case's temporary copy |
| `tests/conftest.py` | The harness: runs both tools and asserts the status |
| `tests/test_corpus.py` | One test per document, on both runs |
| `tests/test_plugin.py` | The plugin is registered under its entry point and loads with the contract's extensions |
| `tests/constraints.txt` | The mdformat releases the pinned leg installs |
| `tests/package.json` and its lockfile | The markdownlint-cli2 release the pinned leg installs |

## A case

`case.toml` names the status and the rule, then lists every document in the directory:

| Key | Values | Meaning |
| -- | -- | -- |
| `status` | `guaranteed`, `neutral`, `bridged` | The matrix status the case asserts; `unsatisfiable` joins them when the plugin's refusal lands |
| `rule` | `MD001` to `MD060`, or absent | The rule the case is about, required for a bridged case; absent, every finding counts, which is what a baseline case asserts |
| `inputs.<file>.findings` | a count | How many findings the document reports before formatting, for the rule or for any rule when the case names none; every `.md` in the directory is listed, and a case naming a rule needs one document above zero, or it proves nothing |
| `inputs.<file>.unchanged` | `true` or `false` | Whether mdformat must write the document back byte for byte, on both runs; set on a document written in mdformat's own style |
| `inputs.<file>.rewritten` | `true` or `false` | Whether mdformat must change the document, on both runs; set on a baseline document that is consistent in styles mdformat does not write, so the case cannot quietly stop exercising the formatter |

A case about a rule carries two kinds of document.
One violates the rule, in one construct per document where the rule has several, with a compliant construct beside it that formatting must not touch; its finding count asserts that exactly the constructs the case is about are what markdownlint reports.
The other is already what mdformat writes, and is `unchanged`: it proves the setting really is the formatter's output, since a preset value that differed from it would be rewritten, and it proves formatting is stable on compliant input rather than churning it.
Two documents rather than one is deliberate: the violating document alone shows the rule is satisfied after formatting, and the compliant document shows the fixed point is where the preset says it is.

For each document the harness copies the case directory twice, lints the document, formats it in place, one copy with mdformat and the `gfm`, `tables` and `frontmatter` extensions alone and one with the `markdownlint` extension added, and lints both again.
Both tools run as the subprocesses an adopter runs, from the case's own directory, so the configuration markdownlint-cli2 discovers is the case's and nothing outside the case reaches either tool.
The findings before formatting must match the count the case declares, each format must exit zero, an `unchanged` document must come back byte for byte and a `rewritten` one must not; then the status decides what the two runs must show:

| Status | Without the plugin | With the plugin |
| -- | -- | -- |
| `guaranteed` | No finding for the rule; with no rule named, no finding at all | No finding for the rule: the plugin does not break what mdformat alone holds |
| `bridged` | For a violating document, at least one finding for the rule: mdformat alone does not hold it | No finding for the rule: the plugin is what holds it |
| `neutral` | The findings for the rule are the same, by rule and count, as before formatting | The same |

Two runs rather than one keep a status honest.
A guaranteed case the plugin turns out to hold is misdeclared and belongs in bridged; a bridged case mdformat alone already satisfies is misdeclared and belongs in guaranteed; both fail, so a status claims no more than the run that earns it.

## What a document may contain

Documents are test data, written to violate the rule their case names, so the repository's own Markdown checks skip `tests/corpus/`: `.markdownlint-cli2.jsonc` ignores the directory and the semantic-line-break check inherits that.
The link check does not skip them, so a document carries no external URL and no relative link or fragment that does not resolve.

## The two legs

The test suite runs twice per Python version in CI ([`pytest.yml`](../../.github/workflows/pytest.yml)):

| Leg | Installs | Purpose |
| -- | -- | -- |
| `pinned` | `tests/constraints.txt` and `tests/package-lock.json`, the releases the matrix's rows were established against and the ones its version table names | The contract as stated holds |
| `latest` | The newest release of mdformat, mdformat-gfm, mdformat-frontmatter and markdownlint-cli2, ignoring the plugin's own dependency bounds | A new rule or a changed style fails here before it reaches an adopter |

A red `latest` leg is a bump waiting to be made, not a broken pull request: [bump the pin](../runbooks/running-the-corpus.md#bumping-a-pin), fix or re-establish the rows the bump changes, and change the matrix with them.
Every run prints the versions it ran against in pytest's header, which is the record of what a given run proved.
