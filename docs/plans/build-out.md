# Plan: Build out `mdformat-markdownlint`

Status: In progress — the repository skeleton, the founding decisions ([ADR-001](../decisions/001-make-markdownlint-accept-mdformat.md), [ADR-002](../decisions/002-the-compatibility-contract.md)), and the Markdown CI callers have landed; next is the compatibility matrix, then the `markdown` flag in `flungo/terraform-github`, then the package.

## Goal

Turn the freshly created repository into a published mdformat plugin, a markdownlint preset, and the corpus that proves the two tools agree, per the founding decisions.
The matrix is written first, because it fixes the scope of the corpus and the unsatisfiable set before any code exists.

## Steps

- [x] `.claude/settings.json` enabling the conventions plugins; `CLAUDE.md`; the decisions and plans directories with their indexes; ADR-001 and ADR-002.
- [ ] `docs/reference/compatibility-matrix.md` with its index: every markdownlint rule and option value with its status, grounded in probes of markdownlint 0.41.1 against mdformat 1.0.0, and checked adversarially against a second, independent probe.
- [x] Adopt the Markdown CI from `flungo/github-workflows`: `markdown-lint`, `markdown-links`, `markdown-sembr` and `flungo-workflows` callers, `.markdownlint-cli2.jsonc`, and an empty `.lycheeignore` carrying its header.
- [ ] Remove `markdown = false` from this repository's declaration in `flungo/terraform-github`, which attaches `LYCHEE_GITHUB_TOKEN` and requires the two lint and link contexts.
- [ ] Verify the external link sweep by `workflow_dispatch` once the token exists, and curate `.lycheeignore` from that run.
- [ ] Package skeleton: `pyproject.toml` declaring mdformat-gfm and mdformat-frontmatter as dependencies, `src/mdformat_markdownlint/`, the `mdformat.parser_extension` entry point, a repository-specific test workflow that installs both tools (`pip` for mdformat, `npm` for markdownlint-cli2).
- [ ] The preset: the markdownlint settings mdformat's fixed choices satisfy, as a file a `.markdownlint-cli2.jsonc` can `extends`.
- [ ] The corpus and its harness: one input per rule and option value, formatted then linted, asserting the matrix's status; pinned and latest versions of both tools.
  MD052 is enabled alongside other rules in every case, since markdownlint 0.41.1 reports nothing for it in isolation.
- [ ] Plugin behaviours, each with its corpus entries: derived `number` and `compact_tables`, including compact tables whenever MD013 measures them; the markdownlint configuration read as markdownlint-cli2 reads it, `extends`, the YAML form and per-directory merging included, and the JavaScript forms refused; `ignores` matched with markdownlint-cli2's globby semantics, bare directory names, braces and negations included; comment blocks kept adjacent; single-space empty compact cells; `[//]: #` definitions preserved; `.mdformat.toml` validated against the derived options; refusal of unsatisfiable settings.
- [ ] Upstream filings: an empty-cell fix and the task-list escape that breaks a link whose text is `x` to mdformat-gfm; a comment-adjacency option and an exclusion hook proposed to mdformat; the plugin shrinks as each lands.
- [ ] Publish to PyPI, with the release procedure recorded as a runbook.
- [ ] Decide adoption for the fleet's own repositories in their own ADRs; this repository's adoption of itself comes first.
