# The corpus

The test suite that proves the compatibility contract ([ADR-002](../decisions/002-the-compatibility-contract.md)): one input per markdownlint rule and option value, formatted with the plugin and then linted, asserting the status the [compatibility matrix](compatibility-matrix.md) gives that row.
The matrix is the human-readable form of the corpus and the two must agree; a status that changes in one changes in the other in the same pull request.

## Layout

| Path | Purpose |
| -- | -- |
| `tests/corpus/<case>/` | One directory per case, named for what it exercises |
| `tests/corpus/<case>/case.toml` | The case's status and, where it exercises one, its rule |
| `tests/corpus/<case>/input.md` | The document the case formats and lints |
| `tests/corpus/<case>/.markdownlint-cli2.jsonc` | The markdownlint configuration the case runs under; absent, markdownlint runs on its defaults |
| `tests/conftest.py` | The harness: runs both tools and asserts the status |
| `tests/test_corpus.py` | One test per case |
| `tests/test_plugin.py` | The plugin is registered under its entry point and loads with the contract's extensions |
| `tests/constraints.txt` | The mdformat releases the pinned leg installs |
| `tests/package.json` and its lockfile | The markdownlint-cli2 release the pinned leg installs |

## A case

`case.toml` carries two keys:

| Key | Values | Meaning |
| -- | -- | -- |
| `status` | `guaranteed`, `neutral`, `bridged` | The matrix status the case asserts; `unsatisfiable` joins them when the plugin's refusal lands |
| `rule` | `MD001` to `MD060`, or absent | The rule the case is about, required for a bridged case; absent, every finding counts, which is what a baseline case asserts |

The harness copies the case directory twice, lints `input.md`, formats each copy in place, one with mdformat and the `gfm`, `tables` and `frontmatter` extensions alone and one with the `markdownlint` extension added, and lints both again.
Both tools run as the subprocesses an adopter runs, from the case's own directory, so the configuration markdownlint-cli2 discovers is the case's and nothing outside the case reaches either tool.
Each format must exit zero; then the status decides what the two runs must show:

| Status | Without the plugin | With the plugin |
| -- | -- | -- |
| `guaranteed` | No finding for the rule; with no rule named, no finding at all, and none in the input either | No finding for the rule: the plugin does not break what mdformat alone holds |
| `bridged` | At least one finding for the rule: mdformat alone does not hold it | No finding for the rule: the plugin is what holds it |
| `neutral` | The findings for the rule are the same, by rule and count, as before formatting | The same |

Two runs rather than one keep a status honest.
A guaranteed case the plugin turns out to hold is misdeclared and belongs in bridged; a bridged case mdformat alone already satisfies is misdeclared and belongs in guaranteed; both fail, so a status claims no more than the run that earns it.

## What an input may contain

Inputs are test data, written to violate the rule their case names, so the repository's own Markdown checks skip `tests/corpus/`: `.markdownlint-cli2.jsonc` ignores the directory and the semantic-line-break check inherits that.
The link check does not skip them, so an input carries no external URL and no relative link or fragment that does not resolve.

## The two legs

The test suite runs twice per Python version in CI ([`pytest.yml`](../../.github/workflows/pytest.yml)):

| Leg | Installs | Purpose |
| -- | -- | -- |
| `pinned` | `tests/constraints.txt` and `tests/package-lock.json`, the releases the matrix's rows were established against and the ones its version table names | The contract as stated holds |
| `latest` | The newest release of mdformat, mdformat-gfm, mdformat-frontmatter and markdownlint-cli2, ignoring the plugin's own dependency bounds | A new rule or a changed style fails here before it reaches an adopter |

A red `latest` leg is a bump waiting to be made, not a broken pull request: [bump the pin](../runbooks/running-the-corpus.md#bumping-a-pin), fix or re-establish the rows the bump changes, and change the matrix with them.
Every run prints the versions it ran against in pytest's header, which is the record of what a given run proved.
