# Plan: Build out `mdformat-markdownlint`

Status: In progress — the repository skeleton, the founding decisions ([ADR-001](../decisions/001-make-markdownlint-accept-mdformat.md), [ADR-002](../decisions/002-the-compatibility-contract.md)), the compatibility matrix, the Markdown CI with the `markdown` flag on and the external link sweep verified, the package skeleton with the corpus harness, the config package with a case per setting and the corpus for every row the plugin's behaviours do not gate have landed; next are the plugin behaviours.

## Goal

Turn the freshly created repository into a published mdformat plugin, a markdownlint preset, and the corpus that proves the two tools agree, per the founding decisions.
The matrix is written first, because it fixes the scope of the corpus and the unsatisfiable set before any code exists.

## Steps

- [x] `.claude/settings.json` enabling the conventions plugins; `CLAUDE.md`; the decisions and plans directories with their indexes; ADR-001 and ADR-002.
- [x] `docs/reference/compatibility-matrix.md` with its index: every markdownlint rule and option value with its status, grounded in probes of markdownlint 0.41.1 against mdformat 1.0.0, and checked adversarially against a second, independent probe.
- [x] Adopt the Markdown CI from `flungo/github-workflows`: `markdown-lint`, `markdown-links`, `markdown-sembr` and `flungo-workflows` callers, `.markdownlint-cli2.jsonc`, and an empty `.lycheeignore` carrying its header.
- [x] Remove `markdown = false` from this repository's declaration in `flungo/terraform-github`, which attaches `LYCHEE_GITHUB_TOKEN` and requires the two lint and link contexts.
- [x] Verify the external link sweep by `workflow_dispatch` once the token exists, and curate `.lycheeignore` from that run.
  The first token-enabled run found nothing, so `.lycheeignore` stays empty.
- [x] Package skeleton: `pyproject.toml` declaring mdformat-gfm and mdformat-frontmatter as dependencies, `src/mdformat_markdownlint/`, the `mdformat.parser_extension` entry point, a repository-specific test workflow that installs both tools (`pip` for mdformat, `npm` for markdownlint-cli2), and the corpus harness with its baseline case: pytest, both tools run as subprocesses, a pinned leg and a latest leg.
- [x] The preset: the markdownlint settings mdformat's fixed choices satisfy, as a file a `.markdownlint-cli2.jsonc` can `extends`, with a corpus case per setting it carries; this repository's own configuration extends it.
- [x] Decide how an adopter obtains the preset and record it: it ships as the npm package `markdownlint-config-mdformat`, versioned independently of the plugin, and every corpus case extends it by name ([ADR-003](../decisions/003-ship-the-preset-as-an-npm-package.md)).
- [x] The corpus: one input per rule and option value, formatted then linted, asserting the matrix's status, and a test that a rule ID the corpus does not know fails.
  MD052 is enabled alongside other rules in every case, since markdownlint 0.41.1 reports nothing for it in isolation.
  The link rules need inputs the repository's link check can still read: no external URL, and no relative link or fragment that does not resolve.
  Landed one matrix section per pull request, each replacing the section's Evidence cells with its cases, and every rule the corpus knows has a case; the unsatisfiable rows wait for the refusal and the bridged rows for the behaviour that bridges them, both below.
- [ ] Plugin behaviours, each with its corpus entries: derived `number` and `compact_tables`, including compact tables whenever MD013 measures them; the markdownlint configuration read as markdownlint-cli2 reads it, `extends`, the YAML form and per-directory merging included, and the JavaScript forms refused; `ignores` matched with markdownlint-cli2's globby semantics, bare directory names, braces and negations included; comment blocks kept adjacent; single-space empty compact cells; `[//]: #` definitions preserved; `.mdformat.toml` validated against the derived options; refusal of unsatisfiable settings.
- [ ] Review the corpus for coverage once the plugin's entries exist: every rule and every value of each option has a case, and each case's documents exercise every construct the rule reports, with a count that proves it; in the same pass, move every document more than one case could run into the shared pool under `tests/documents/`.
- [ ] Upstream filings: an empty-cell fix and the task-list escape that breaks a link whose text is `x` to mdformat-gfm; a comment-adjacency option and an exclusion hook proposed to mdformat; the plugin shrinks as each lands.
- [ ] Publish `mdformat-markdownlint` to PyPI and `markdownlint-config-mdformat` to npm, each from its own tag prefix with trusted publishing, with the release procedure recorded as a runbook; choose the licence first.
- [ ] Decide adoption for the fleet's own repositories in their own ADRs; this repository's adoption of itself comes first.
  The vehicle is a reusable `mdformat` check workflow in the Markdown family of `flungo/github-workflows`, which the proposed ADR under § Follow-ups decides and a dedicated session builds once the packages publish, so the publish step ends by telling that session.

## Follow-ups

Work that continues outside this repository once the steps above complete:

- [flungo/github-workflows#56](https://github.com/flungo/github-workflows/pull/56) — the proposed ADR-019, adopting mdformat as the fleet's Markdown formatter through this project's plugin and preset, held as a draft until the packages publish; it records why mdformat alone was not adopted and what the plugin changes.
- [The session that finishes it](https://claude.ai/code/session_013xbn92MwX5afzrqnG2xxue) — owns that pull request, builds the workflow with its reference and runbook entries when told the packages are published, flips the ADR to accepted, and hands the per-repository adoption on.
- [The session completing this plan](https://claude.ai/code/session_01Knz8gEB94rkpnQbKpmPN3c) — carries the steps above from the plugin behaviours onward, and is the one that tells the session above when the packages are published.
