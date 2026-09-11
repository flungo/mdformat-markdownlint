# ADR-001: Bridge the two tools by making markdownlint accept mdformat, not by making mdformat obey markdownlint

- **Date:** 2026-09-11
- **Status:** Accepted

## Context

A repository that formats Markdown with [mdformat](https://github.com/hukkin/mdformat) and lints it with [markdownlint](https://github.com/DavidAnson/markdownlint) has two style authorities.
Each evolves on its own: markdownlint adds rules across minor versions, and mdformat's changelog states that its formatting style is not guaranteed stable across versions.
Without something binding them, any bump on either side can produce a file the formatter insists on and the linter rejects, and the failure lands on whichever pull request runs next rather than on the bump.

The two tools have very different shapes.
markdownlint has 53 rules, most with options; it reports, and fixes only the subset of findings that carry fix information.
mdformat rewrites, and has three options that affect style: paragraph wrapping, ordered-list numbering and line endings; compact tables is an option of the mdformat-gfm tables plugin.
Everything else it does is a fixed decision: dash bullets, with an asterisk only for a list written directly after another; backtick fences; ATX headings; a seventy-underscore thematic break; indentation by marker width; reference definitions gathered at the end of the document.

Measured rule by rule against markdownlint 0.41.1, with inputs built to violate each rule under each of its option values, mdformat's fixed style satisfies about a third of the rules outright, is neutral on most of the rest, which judge content no formatter can decide, and disagrees with markdownlint in a small number of identifiable places.
The disagreements at markdownlint's own defaults: a blank line mdformat inserts after a comment-only HTML block detaches `<!-- markdownlint-disable-next-line -->` from the line it governs; a padded table lengthens every row to its widest cell, past MD013's limit; an ordered list starting at zero is renumbered into a form MD029 rejects; an indented code block becomes a fence with no language, which MD040 then asks for; and an unused `[//]: #` reference definition, which markdownlint's baseline deliberately tolerates as a comment idiom, is deleted.
Under a compact table setting, an empty cell is rendered with two spaces, which MD060's compact style rejects.

The obvious design, a plugin that reads any markdownlint configuration and makes mdformat produce what it asks for, would mean reimplementing mdformat's renderers for every fixed decision a configuration could contradict.
That is most of them, and it would recreate inside the plugin exactly the drifting second style authority the bridge exists to remove.

## Decision

**The markdownlint configuration is the one style declaration, and the bridge is built by making markdownlint accept mdformat's output.**
This is the shape of [eslint-config-prettier](https://github.com/prettier/eslint-config-prettier): the formatter's fixed decisions are conceded, the linter is configured to agree with them, and a setting the user changes away from that agreement is a conflict they chose.

eslint-config-prettier is a configuration for the linter, and this project's preset is that half.
The plugin sits on the formatter's side for a reason the analogy does not have: Prettier has no option a linter setting implies and no behaviour a linter cannot accept, so configuration alone closes its gap, whereas a markdownlint setting decides two of mdformat's options, and a few of mdformat's behaviours write a file markdownlint rejects or drop content markdownlint tolerates.
Nothing on the linter's side can change what a formatter writes.
The reverse arrangement, running mdformat inside markdownlint as a custom rule the way eslint-plugin-prettier runs Prettier, is possible, since a custom rule sees the whole document and can emit line-scoped fixes, but it is the arrangement Prettier's own documentation now discourages: formatting differences become lint findings, the run is slower, and a whole-document rewrite expressed as per-line fixes is one more place for things to break; here it would also put a Python formatter behind a Node linter.
A purely linter-side accommodation of the conflicts would mean disabling core rules and shipping custom ones that tolerate the formatter's output, and it could still reach neither directive detachment, which is markdownlint's directive handling rather than a rule, nor the deleted comment definitions, nor `ignores`.
The preset and the plugin are each the smallest thing on their own side of the agreement.

Three artefacts follow:

- **A markdownlint preset** a repository extends, carrying every rule setting that mdformat's fixed choices satisfy.
  A repository's own configuration adds its content rules and any override on top.
- **An mdformat plugin** that does only what needs a plugin: derive mdformat's real options from the markdownlint configuration, honour its `ignores`, keep a comment block attached to the block it precedes, render an empty compact cell as markdownlint expects, preserve the reference definitions markdownlint's baseline ignores, validate `.mdformat.toml` against the derived options, and refuse to run under a configuration mdformat cannot satisfy.
  It never reimplements a renderer to honour a cosmetic preference.
  It reads the configuration the way markdownlint-cli2 does, `extends` included, since applying the preset is itself an `extends`.
  The promise is stated for mdformat with the `gfm`, `tables` and `frontmatter` extensions, which the plugin declares as dependencies: without them a table is a paragraph and front matter is a heading.
- **A corpus** that proves the contract, rule by rule and option by option, against pinned versions of both tools ([ADR-002](002-the-compatibility-contract.md)).

Where a compatibility gap can be closed by an existing third-party mdformat plugin that actually closes it, that plugin is recommended rather than the gap reimplemented here.
Where mdformat or one of its plugins can take a fix upstream, the fix is proposed there, and this plugin shrinks when it lands.

## Consequences

- A repository holds one style configuration.
  `.mdformat.toml` becomes unnecessary; where one exists, the plugin checks it against what the markdownlint configuration implies.
- The plugin stays small, because most of the bridge is a static preset, and its size is bounded by mdformat's option surface rather than by markdownlint's rule surface.
- A user who wants a bullet marker or fence style mdformat does not produce cannot get it through this plugin.
  They change their markdownlint configuration to match mdformat, or they do not use mdformat.
  Refusal, not silent divergence, is the response to such a setting; it sits beside mdformat's own refusal to write a file whose rendering would change.
- Any behaviour that depends on reading the markdownlint configuration inherits that configuration's formats: the plugin reads the JSONC and YAML forms and refuses the JavaScript ones, saying so rather than guessing.
- The preset and the plugin version together against the markdownlint and mdformat versions they were verified with; a bump on either side is a change to this project first, and to its adopters only once the corpus passes.
