# CLAUDE.md — mdformat-markdownlint

An [mdformat](https://github.com/hukkin/mdformat) plugin, a [markdownlint](https://github.com/DavidAnson/markdownlint) preset, and the corpus that proves the two agree: a repository keeps one style configuration, markdownlint's, and mdformat's output lints clean against it.
The shape is that of eslint-config-prettier — the linter is configured to accept the formatter's fixed decisions, and the plugin bridges only what a static preset cannot ([ADR-001](docs/decisions/001-make-markdownlint-accept-mdformat.md)).
What an adopter may rely on, rule by rule, is the compatibility contract ([ADR-002](docs/decisions/002-the-compatibility-contract.md)).

> **Status: build-out under way.**
> The skeleton, the founding decisions, the [compatibility matrix](docs/reference/compatibility-matrix.md), the Markdown CI with its two lint and link contexts required on `main`, the package skeleton and the corpus harness exist; the plugin's behaviours, the preset and the corpus cases are tracked in [`docs/plans/build-out.md`](docs/plans/build-out.md).
> Nothing is published yet: the package registers as the `markdownlint` extension and changes nothing until its behaviours land, and the prototype the matrix's Evidence column refers to lives outside the repository until then.

## Repo layout

```text
pyproject.toml              The package: flit_core build, the mdformat.parser_extension entry
                            point, and dependency bounds that hold adopters at the verified minor.
src/mdformat_markdownlint/  The plugin.
tests/                      The corpus and its harness (docs/reference/corpus.md): one directory
                            per case under corpus/, both tools run as subprocesses, the pinned
                            releases in constraints.txt and package.json.
docs/
  decisions/   ADRs — numbered, never deleted or renumbered. README.md is the index.
  plans/       One-time procedures with status tracking; retired when complete. README.md is the index.
  reference/   Lookup docs — the compatibility matrix and the corpus reference. README.md is the index.
  runbooks/    Repeatable procedures — running the corpus, bumping a pin. README.md is the index.
```

The preset is added by the build-out plan and described here when it lands.

**The compatibility matrix and the corpus must agree** ([ADR-002](docs/decisions/002-the-compatibility-contract.md)).
A status that changes in one changes in the other in the same pull request; until the corpus exists, the matrix's Evidence column says how each row is known.

## Conventions

This repository adopts Fabrizio's conventions at project scope through [`.claude/settings.json`](.claude/settings.json), from the [`flungo-plugins` marketplace](https://github.com/flungo/claude-plugins):

- **`git-conventions`** — never commit to `main`; a feature branch per change, landed via pull request; Conventional Commits; linear history, squash or rebase, no fixup commits; force-push feature branches only.
- **`docs-standards`** — the Diátaxis `docs/` split with a `README.md` index per directory kept current in the same commit; Nygard ADRs; the two-PR plan lifecycle; the 🤖 Agent and Verify callouts.
- **`markdown-standards`** — semantic line breaks (one sentence per source line, `MD013` off), unambiguous cross-references, unique names for cross-referenced headings, compact tables, and fixing a lint or link finding at its source rather than suppressing it.
- **`writing-styles`** — the instructional-writing style for reference docs: state the current truth, never the document's own history.

The plugins complement this file; where this repository differs, this file wins.

## Markdown validation CI

The checks those conventions pair with, adopted from [flungo/github-workflows](https://github.com/flungo/github-workflows) and pinned `@v2`: markdownlint (`.markdownlint-cli2.jsonc`), a blocking offline check of relative links and heading anchors on every pull request, a daily external-URL sweep that reports through a single auto-updated issue, and `markdown-sembr` for the one semantic-line-break MUST rule, two sentences never sharing a source line.
The `flungo-workflows` caller raises an issue here if the repository ever pins a frozen major.

The conventions themselves stay in `markdown-standards`; only repo-specific facts belong here:

- **Tool version — read it from a CI run, never from a note.**
  The shared workflow tracks the linter action's major tag, so the markdownlint version floats; take it from the first line of the markdownlint job's log and match it locally before chasing findings.
  That floating version will also be one of the two this project's corpus pins, so a bump the fleet's CI picks up becomes a change this repository tests before its adopters see it.
- **`.markdownlint-cli2.jsonc` will be the first adopter of this project's own preset.**
  Today it carries the fleet's three settings itself.
  Once the preset exists the file extends it and keeps what is this repository's own: `MD013` off and `MD024` `siblings_only` are content choices that belong to no preset, and `MD060` `compact` holds through the plugin's derived option rather than mdformat alone, so all three stay here.
- **The repository's Markdown follows mdformat's decisions wherever markdownlint is indifferent.**
  Every ordered-list item is `1.`, since numbering the source churns on insertion, and a table's delimiter row is `--` per column.
  `mdformat --check --compact-tables` over the documents then disagrees only on empty compact cells, which mdformat writes as two spaces and MD060 rejects; that is the plugin's bridge, pending, and until it lands those cells stay single-spaced.
- **`.lycheeignore`** is populated only from this repo's own token-enabled `workflow_dispatch` runs, per the rules in its header.
- **The corpus inputs under `tests/corpus/` are exempt from the lint and sembr checks, not from the link check.**
  They exist to violate rules, so `.markdownlint-cli2.jsonc` ignores them and the sembr check inherits that; lychee still reads them, so an input carries no external URL and no unresolvable link.

## The corpus

The repository's own CI beyond the Markdown checks is [`pytest.yml`](.github/workflows/pytest.yml): the test suite, every case under `tests/corpus/` and the plugin's own tests, on a pinned leg and a latest leg per Python version.
Every case is formatted twice, without and with the plugin, so a guaranteed row is proven to hold by mdformat alone and a bridged row to hold only once the plugin is added.
What a case is and what each status asserts is [`docs/reference/corpus.md`](docs/reference/corpus.md); how to run it locally and bump a pin is [`docs/runbooks/running-the-corpus.md`](docs/runbooks/running-the-corpus.md).
A red `latest` leg is a bump waiting to be made, and the runbook says how.

## Sensitive information

This repository is public.
Never commit tokens, keys or secret values; a secret is referred to by its **name** and a placeholder, never its value.

## Working with this repo in Claude Code

GitHub interaction is through the **GitHub MCP** (`mcp__github__*`); there is no `gh` CLI in web sessions.

**Validating Markdown locally** — the commands, where to read the linter version from (a CI run, never a number written here), how to install `lychee` in a sandbox, and why the external URL sweep cannot be verified locally all come from the `markdown-standards` plugin's `validating-locally.md`.
One repo-specific argument: once the corpus's node side is installed, pass `--exclude-path tests/node_modules` to `lychee`, or it reads the READMEs of every installed module; CI never installs them, so the shared workflow needs nothing.

**Two tools are the subject here, and their versions are facts the corpus pins.**
Read the pinned releases from `tests/constraints.txt` and `tests/package.json`, never from a note in prose; the matrix's version table names the same releases and moves with them, and a run's pytest header records what that run was against.

## Active work

- [`docs/plans/build-out.md`](docs/plans/build-out.md) — the build-out from skeleton to a published package.

## Key decisions

See [`docs/decisions/README.md`](docs/decisions/README.md).
In short:

- The markdownlint configuration is the one style declaration; a preset makes markdownlint accept mdformat's fixed choices, and the plugin bridges only what a static preset cannot — derived options, `ignores`, comment adjacency, empty compact cells, preserved comment definitions, `.mdformat.toml` validation, and refusal of what cannot be satisfied ([ADR-001](docs/decisions/001-make-markdownlint-accept-mdformat.md)).
- Every rule and option value is guaranteed, neutral, bridged or unsatisfiable; the baseline is never unsatisfiable; mdformat's cosmetic decisions stand; a corpus asserts each status against pinned and latest versions of both tools ([ADR-002](docs/decisions/002-the-compatibility-contract.md)).
