# CLAUDE.md — mdformat-markdownlint

An [mdformat](https://github.com/hukkin/mdformat) plugin, a [markdownlint](https://github.com/DavidAnson/markdownlint) preset, and the corpus that proves the two agree: a repository keeps one style configuration, markdownlint's, and mdformat's output lints clean against it.
The shape is that of eslint-config-prettier — the linter is configured to accept the formatter's fixed decisions, and the plugin bridges only what a static preset cannot ([ADR-001](docs/decisions/001-make-markdownlint-accept-mdformat.md)).
What an adopter may rely on, rule by rule, is the compatibility contract ([ADR-002](docs/decisions/002-the-compatibility-contract.md)).

> **Status: build-out under way.**
> The skeleton, the founding decisions, the [compatibility matrix](docs/reference/compatibility-matrix.md) and the Markdown CI exist, with its two lint and link contexts required on `main`; the package, the preset and the corpus are tracked in [`docs/plans/build-out.md`](docs/plans/build-out.md).
> Nothing is published yet, and no plugin code is in the repository: the prototype the matrix's Evidence column refers to lives outside it until the package lands.

## Repo layout

```text
pyproject.toml              The package: flit_core build, the mdformat.parser_extension entry
                            point, and dependency bounds that hold adopters at the verified minor.
src/mdformat_markdownlint/  The plugin.
docs/
  decisions/   ADRs — numbered, never deleted or renumbered. README.md is the index.
  plans/       One-time procedures with status tracking; retired when complete. README.md is the index.
  reference/   Lookup docs — the compatibility matrix lives here. README.md is the index.
```

The preset and the corpus (`tests/`) are added by the build-out plan and described here as they land.

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
- **`.lycheeignore`** is populated only from this repo's own token-enabled `workflow_dispatch` runs, per the rules in its header.

## Sensitive information

This repository is public.
Never commit tokens, keys or secret values; a secret is referred to by its **name** and a placeholder, never its value.

## Working with this repo in Claude Code

GitHub interaction is through the **GitHub MCP** (`mcp__github__*`); there is no `gh` CLI in web sessions.

**Validating Markdown locally** — the commands, where to read the linter version from (a CI run, never a number written here), how to install `lychee` in a sandbox, and why the external URL sweep cannot be verified locally all come from the `markdown-standards` plugin's `validating-locally.md`.

**Two tools are the subject here, and their versions are facts the corpus will pin.**
Once the package exists, read the pinned versions from `pyproject.toml` and the test workflow, never from a note in prose; a note goes stale the day one of them is bumped.
Until then the matrix's version table is the only record of the versions its rows were established against.

## Active work

- [`docs/plans/build-out.md`](docs/plans/build-out.md) — the build-out from skeleton to a published package.

## Key decisions

See [`docs/decisions/README.md`](docs/decisions/README.md).
In short:

- The markdownlint configuration is the one style declaration; a preset makes markdownlint accept mdformat's fixed choices, and the plugin bridges only what a static preset cannot — derived options, `ignores`, comment adjacency, empty compact cells, preserved comment definitions, `.mdformat.toml` validation, and refusal of what cannot be satisfied ([ADR-001](docs/decisions/001-make-markdownlint-accept-mdformat.md)).
- Every rule and option value is guaranteed, neutral, bridged or unsatisfiable; the baseline is never unsatisfiable; mdformat's cosmetic decisions stand; a corpus asserts each status against pinned and latest versions of both tools ([ADR-002](docs/decisions/002-the-compatibility-contract.md)).
