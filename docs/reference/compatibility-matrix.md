# Compatibility matrix

What an adopter may rely on, for every markdownlint rule and every value of its options, when Markdown is formatted by mdformat with this plugin enabled.
Each row carries one of the four statuses [ADR-002](../decisions/002-the-compatibility-contract.md) defines, and the corpus asserts them.

| Status | Meaning |
| -- | -- |
| Guaranteed | mdformat's output cannot violate the rule under this setting |
| Neutral | mdformat never introduces a violation and never removes one; markdownlint remains the gate |
| Bridged | mdformat alone would violate it; this plugin's derived options or rendering make it hold |
| Unsatisfiable | mdformat's fixed style violates it wherever the construct appears; the plugin refuses to run under the setting |

A status describes documents that use the construct the rule governs: a document with no tables satisfies every table rule, and that says nothing about the rule.

The **Evidence** column says how a row is known.
*Corpus* is a case under `tests/corpus/` that asserts the row on every run, with and without the plugin ([the corpus reference](corpus.md)), and the word, with the value it proves where the row has several, links to the case; *probe* is a run of one or more inputs per row against the versions below; *prototype* is the plugin prototype run over the same inputs; *construction* follows from mdformat's documented style and has not been exercised; *pending* is a plugin behaviour not yet implemented, so the row states the contract the plugin will meet and nothing an adopter can use today.
The corpus replaces every other value in that column with its own case as it lands, and a row the corpus contradicts is a defect in one or the other.

| Tool | Version the rows were established against |
| -- | -- |
| markdownlint | 0.41.1, run through markdownlint-cli2 0.23.2 |
| mdformat | 1.0.0 |
| mdformat-gfm | 1.0.0, providing the `gfm` and `tables` extensions |
| mdformat-frontmatter | 2.1.2 |

Every row assumes the `gfm`, `tables` and `frontmatter` extensions are enabled.
Without `tables`, a table is a paragraph to mdformat and every table row below is void; without `frontmatter`, front matter is rewritten as a thematic break and a heading.
The plugin declares both packages as dependencies.

## Two exceptions that cut across rules

Two of mdformat's behaviours are content-preserving by design and turn a handful of Guaranteed rows into Neutral ones wherever they apply.
They are stated once here rather than in every row they touch.

- **Inside a tight list item, blocks stay on adjacent lines.**
  A blank line between two blocks of a list item makes the whole list loose and changes the render, so mdformat never adds one.
  A heading, a fence or a table written directly under an item's text keeps no blank line around it, and MD022, MD031 and MD058 report it exactly as they did before formatting.
  The fix is the author's: a loose list, or the block moved out of the item.
- **An HTML block is written verbatim.**
  Everything from an opening tag or `<!--` to the end of the block, a multi-line comment included, is content: trailing spaces, tabs and runs of blank lines inside it survive formatting, and MD009, MD010 and MD012 report them as before.

## What the plugin derives from the markdownlint configuration

mdformat itself has three options that affect style: paragraph wrapping, ordered-list numbering and line endings.
Its other options, `validate`, `exclude`, `extensions` and `codeformatters`, select behaviour rather than style.
Compact tables is an option of mdformat-gfm's `tables` plugin.
The plugin sets two of these from the nearest `.markdownlint-cli2.jsonc` and leaves the rest to mdformat's own configuration.

| markdownlint setting | mdformat option | Derivation | Evidence |
| -- | -- | -- | -- |
| `MD029.style` | `number` | `one` gives `false`; `one_or_ordered`, `ordered` and the default give `true`, the numbering every style but `one` accepts. `MD029: false` leaves `number` to mdformat's own configuration | Prototype |
| `MD060.style` | `compact_tables` | `compact` gives `true`; `aligned` gives `false`; `any`, `tight` and the default leave mdformat's own setting in place | Prototype |
| `MD013` with `tables` true, the default | `compact_tables` | `true` unless `MD060.style` is `aligned`: a padded table lengthens every row to its widest cell, which is the one way mdformat's own style breaks a line-length limit | Pending |
| `ignores` | none; the file is left as it was on disk, except that a file with no trailing newline gains one | Matched against the nearest configuration only, with `*`, `?` and `**`. markdownlint-cli2 also expands a bare directory name, expands braces, applies a root configuration's `ignores` to every file beneath it, and has its own reading of a `!` entry; matching those is pending and each divergence is a corpus entry | Prototype, pending for the divergences |
| `MD013.line_length` | none | Wrapping is not derived: the rule also measures headings, code and tables, which no wrap setting reaches, and a wrapped paragraph is a choice the plugin has no business making | |
| `MD009.br_spaces` | none | mdformat writes every hard break as a backslash, which satisfies any value | Probe |

A derived value wins over the same option given on mdformat's command line or in `.mdformat.toml`, the reverse of mdformat's own precedence, because the markdownlint configuration is the one style declaration.
The plugin will report a `.mdformat.toml` value the configuration implies as redundant and stop on one that conflicts, since the two files would then disagree about what the repository's style is; neither check exists in the prototype yet.

## Headings

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD001 heading-increment | any | Neutral | Probe | Heading levels are content |
| MD003 heading-style | `consistent`, `atx` | Guaranteed | [Corpus for `atx`](../../tests/corpus/md003-atx/case.toml), probe for `consistent` | Every heading, setext or closed, in a list or a blockquote, is rewritten as open ATX |
| MD003 heading-style | `atx_closed`, `setext`, `setext_with_atx`, `setext_with_atx_closed` | Unsatisfiable | Probe | Closing hashes are dropped and setext headings converted |
| MD018 no-missing-space-atx | | Neutral | Probe | `#Heading` is a paragraph in CommonMark and is left as one |
| MD019 no-multiple-space-atx | | Guaranteed | Probe | A tab after the hashes is normalised too |
| MD020 no-missing-space-closed-atx | | Neutral | Probe | `#Heading#` is a paragraph and is left as one. The one form the rule reports that is a heading, `# Heading#`, is escaped to `# Heading\#`, which removes the finding |
| MD021 no-multiple-space-closed-atx | | Guaranteed | Probe | |
| MD022 blanks-around-headings | `lines_above` and `lines_below` at 1, 0 or −1 | Guaranteed | Probe | Blocks outside tight list items are separated by exactly one blank line, and the rule checks for at least the configured number |
| MD022 blanks-around-headings | `lines_above` or `lines_below` at 2 or more, in any form | Unsatisfiable | Probe | |
| MD022 blanks-around-headings | `include_front_matter` | Guaranteed | Probe | mdformat separates front matter from the first block with a blank line |
| MD023 heading-start-left | | Guaranteed | Probe | |
| MD024 no-duplicate-heading | any | Neutral | Probe | Content |
| MD025 single-title | any | Neutral | Probe | Content; a front-matter title counts as the first heading, as the rule documents |
| MD026 no-trailing-punctuation | any | Neutral | Probe | Content |
| MD041 first-line-heading | any | Neutral | Probe | Content |
| MD043 required-headings | any | Neutral | Probe | Content |

## Lists

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD004 ul-style | `consistent`, `dash` | Guaranteed | [Corpus for `dash`](../../tests/corpus/md004-dash/case.toml), probe for `consistent` | Every bullet is a dash, at every nesting level |
| MD004 ul-style | `consistent`, `dash`, on two lists written directly one after the other | Neutral | Probe | The source can only express adjacent lists with different markers, so it already violates the rule; mdformat keeps the second list's marker, and no formatter can satisfy the rule there without inserting a separator |
| MD004 ul-style | `asterisk`, `plus`, `sublist` | Unsatisfiable | Probe | |
| MD005 list-indent | | Guaranteed | Probe | Zero-padded markers included |
| MD007 ul-indent | `indent` 2 | Guaranteed | Probe | Nested content is indented by the parent marker's width, two for a dash |
| MD007 ul-indent | any other `indent` | Unsatisfiable | Probe | |
| MD007 ul-indent | `start_indented` true | Unsatisfiable | Probe | The first level is never indented |
| MD029 ol-prefix | `one` | Guaranteed | [Corpus](../../tests/corpus/md029-one/case.toml) | At mdformat's default, every item after the first is written as `1.`; the plugin also derives `number` as `false`, so a `number = true` in mdformat's own configuration cannot contradict the rule (prototype). A list whose first item is not `1.` or `0.` violates the rule before and after formatting |
| MD029 ol-prefix | `one_or_ordered`, `ordered` | Bridged | Prototype | `number` derived as `true`. Without the derivation a list starting at `0.` renders `0. 1. 1.`, which the rule reads as ordered and rejects. A list of ten or more items is zero-padded to `01.`, which the rule accepts. A list starting at 2 or above violates the rule before and after formatting |
| MD029 ol-prefix | `zero` | Unsatisfiable | Probe | Items after the first are never `0.` |
| MD030 list-marker-space | all four parameters at 1 | Guaranteed | Probe | One space follows every marker |
| MD030 list-marker-space | any parameter above 1 | Unsatisfiable | Probe | Each parameter tested on its own |
| MD032 blanks-around-lists | | Guaranteed | Probe | Including a list that follows a comment the plugin keeps adjacent |

## Whitespace and blank lines

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD009 no-trailing-spaces | any `br_spaces`, `strict` true, `list_item_empty_lines` | Guaranteed | Probe | Trailing whitespace is stripped and a hard break is written as a backslash; see the HTML-block exception |
| MD009 no-trailing-spaces | `code_blocks` true | Neutral | Probe | Code content is preserved |
| MD010 no-hard-tabs | `code_blocks` false | Guaranteed | Probe | Tabs in prose become spaces; see the HTML-block exception |
| MD010 no-hard-tabs | `code_blocks` true, the default | Neutral | Probe | Tabs inside code are content |
| MD012 no-multiple-blanks | any `maximum` | Guaranteed | Probe | At most one blank line separates blocks; blank lines inside code are exempt from the rule and preserved; see the HTML-block exception |
| MD013 line-length | default, with `tables` true and padded tables | Bridged | Pending | mdformat's padded tables lengthen every row to the widest cell, so a table at the limit fails on every row after formatting; the plugin derives compact tables whenever the rule measures tables and MD060 does not demand `aligned` |
| MD013 line-length | any, with compact tables or `tables` false | Neutral | Probe | mdformat never reflows a line at its default `wrap = keep`. Two of its rewrites can lengthen one: an escape such as `*` to `\*` adds a character, and a thematic break becomes seventy underscores, which is a finding only where `line_length` is below 70 with `strict` or `stern` |
| MD027 no-multiple-space-blockquote | any | Guaranteed | Probe | Lists, fences, nested quotes and tables inside a blockquote included |
| MD028 no-blanks-blockquote | | Neutral | Probe | Two blockquotes separated by a blank line are kept as written; joining them would change the render |
| MD047 single-trailing-newline | | Guaranteed | Probe | An empty file stays empty, which the rule accepts |

## Code

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD014 commands-show-output | | Neutral | Probe | Code content |
| MD031 blanks-around-fences | outside tight list items; `list_items` false | Guaranteed | Probe | See the tight-list exception |
| MD038 no-space-in-code | | Neutral | Probe | mdformat strips only the single symmetric space CommonMark itself strips, which the rule allows; every padding the rule reports is content and is kept |
| MD040 fenced-code-language | any, on fenced blocks | Neutral | Probe | Content |
| MD040 fenced-code-language | any, on an indented code block | Unsatisfiable | Probe | An indented block is outside the rule's scope; mdformat rewrites it as a fence with no language, which puts it inside, and only the author knows the language. The one place a document that lints clean at markdownlint's defaults stops doing so after formatting; ADR-002 names it |
| MD046 code-block-style | `consistent`, `fenced` | Guaranteed | [Corpus for `fenced`](../../tests/corpus/md046-fenced/case.toml), probe for `consistent` | Indented code is rewritten as a fence |
| MD046 code-block-style | `indented` | Unsatisfiable | Probe | |
| MD048 code-fence-style | `consistent`, `backtick` | Guaranteed | [Corpus for `backtick`](../../tests/corpus/md048-backtick/case.toml), probe for `consistent` | Tilde fences are rewritten with backticks, lengthened where the content holds a backtick run |
| MD048 code-fence-style | `tilde` | Unsatisfiable | Probe | |

## Emphasis and inline text

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD033 no-inline-html | any | Neutral | Probe | Content |
| MD034 no-bare-urls | | Neutral | Probe | A bare URL, `www.` literal or email address is left as written |
| MD036 no-emphasis-as-heading | any | Neutral | Probe | Content |
| MD037 no-space-in-emphasis | | Neutral | Probe | A `**`, `__` or `_` run that cannot open emphasis is escaped, which removes the rule's finding for it; a single `*` beside a space is left as literal text, and the rule's heuristic still reports it |
| MD039 no-space-in-links | | Neutral | Probe | Stripping the spaces would change the rendered link text |
| MD044 proper-names | any | Neutral | Probe | Content; a lowercased reference label is not text to the rule |
| MD049 emphasis-style | any | Neutral | Probe | The marker is kept as written |
| MD050 strong-style | any | Neutral | Probe | The marker is kept as written |

## Links and images

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD011 no-reversed-links | | Neutral | Probe | Reversed syntax is plain text to the parser |
| MD042 no-empty-links | | Neutral | Probe | An empty destination is rewritten as `<>`, which the rule reads the same way |
| MD045 no-alt-text | | Neutral | Probe | Content |
| MD051 link-fragments | any | Neutral | Probe | Content; a non-ASCII fragment is percent-encoded and still resolves |
| MD052 reference-links-images | any | Neutral | Probe | An undefined label is plain text and is left as such. markdownlint 0.41.1 reports this rule only when other rules are enabled alongside it, so the corpus never asserts it in isolation |
| MD053 link-image-reference-definitions | any | Guaranteed | Probe | Unused and duplicate definitions are removed and the rest gathered at the end of the document, sorted by label. A definition whose label the default `ignored_definitions` covers, the `[//]: #` comment idiom, is removed too; deleting it violates nothing, and keeping it is a content-preservation behaviour of the plugin, pending |
| MD054 link-image-style | `autolink`, `inline`, `url_inline` | Neutral | Probe | Each link keeps its style; removing redundant angle brackets around a destination and moving definitions to the end change nothing the rule classifies |
| MD054 link-image-style | `shortcut` false | Unsatisfiable | Probe | A full or collapsed reference whose text equals its label is rewritten as a shortcut reference |
| MD054 link-image-style | `collapsed` false, `full` false | Guaranteed | Probe | For the same reason: such references become shortcuts |
| MD059 descriptive-link-text | any | Neutral | Probe | Content |

## Tables

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD055 table-pipe-style | `consistent`, `leading_and_trailing` | Guaranteed | [Corpus for `leading_and_trailing`](../../tests/corpus/md055-pipes/case.toml), probe for `consistent` | Every row is written with a leading and a trailing pipe |
| MD055 table-pipe-style | `leading_only`, `trailing_only`, `no_leading_or_trailing` | Unsatisfiable | Probe | |
| MD056 table-column-count | | Guaranteed | Probe | A short row is padded with empty cells and a long row loses its extra cells, as GFM renders them |
| MD058 blanks-around-tables | | Guaranteed | Probe | See the tight-list exception |
| MD060 table-column-style | `any`, the default, with padded tables | Guaranteed | Probe | Padded tables are `aligned`, with wide, combining and escaped characters measured as the rule measures them |
| MD060 table-column-style | `any` with compact tables | Bridged | Prototype | An empty cell is rendered as a single space; mdformat alone writes two, which no style accepts |
| MD060 table-column-style | `aligned` | Guaranteed | [Corpus](../../tests/corpus/md060-aligned/case.toml) | At mdformat's default, every cell is padded to its column's widest; the plugin also derives `compact_tables` as `false`, so a compact setting in mdformat's own configuration cannot contradict the rule (prototype) |
| MD060 table-column-style | `compact` | Bridged | Prototype | `compact_tables` derived as `true`, and empty cells rendered as above. The delimiter row is `--`, or `:-:` and `-:` for aligned columns, which the style accepts |
| MD060 table-column-style | `tight` | Unsatisfiable | Probe | Every pipe is padded with a space |
| MD060 table-column-style | `aligned_delimiter` true with `aligned` | Guaranteed | Probe | |
| MD060 table-column-style | `aligned_delimiter` true with `compact` | Unsatisfiable | Probe | The compact delimiter row is `--` regardless of the header |

## Thematic breaks

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD035 hr-style | `consistent` | Guaranteed | Probe | Every thematic break is rewritten as seventy underscores |
| MD035 hr-style | the explicit style of seventy underscores | Guaranteed | [Corpus](../../tests/corpus/md035-underscores/case.toml) | |
| MD035 hr-style | any other explicit style | Unsatisfiable | Construction | |

## Front matter

mdformat-frontmatter parses the front matter as YAML and re-emits it, which normalises spacing inside it: `a:   "two"` becomes `a: "two"`, `[1,2]` becomes `[1, 2]`, and trailing whitespace goes.
Invalid YAML is passed through unchanged with a warning.
No markdownlint rule reads front matter except through the `front_matter_title` and `include_front_matter` options above.

## Inline configuration comments

markdownlint's directives are HTML comments, and mdformat treats a comment on its own line as a block and puts a blank line after it.

| Directive | Status | Evidence | Notes |
| -- | -- | -- | -- |
| `disable-next-line` | Bridged | Prototype | A comment block written flush against the next block stays flush, at top level, in a blockquote and in a list item; one the author separated with a blank line keeps it. A comment kept flush before a heading, list, fence or table triggers none of MD022, MD032, MD031 or MD058 |
| `disable-line` | Guaranteed | Probe | An inline comment on the governed line is inline HTML and is kept in place |
| `disable`, `enable`, `disable-file`, `capture`, `restore`, `configure-file` | Guaranteed | Probe | Their scope starts at the comment's own line, so a blank line after it changes nothing |

## mdformat behaviours an adopter meets that no rule describes

- **A paragraph line beginning with a link whose text is `x`, `X` or a single space is refused.**
  mdformat-gfm 1.0.0 escapes what looks like a task-list marker at the start of a line, which breaks such a link, and mdformat's validation then refuses to write the file; with validation off it writes `\[x\](…)` instead.
  The fix is upstream, and until it lands the link text or the line start is the author's to change.
- **An unused reference definition inside a list item or blockquote** leaves an empty container behind or, where the container would otherwise be empty, makes validation refuse the file.
- **Non-ASCII link destinations are percent-encoded**, `#héllo` to `#h%C3%A9llo`; they still resolve, and the diff is the only surprise.

## The refusal set

The settings the plugin will refuse to run under, collected from the rows above; the refusal itself is pending in the prototype:

- `MD003.style` at `atx_closed`, `setext`, `setext_with_atx` or `setext_with_atx_closed`
- `MD004.style` at `asterisk`, `plus` or `sublist`
- `MD007.indent` at any value but 2, or `MD007.start_indented` true
- `MD022.lines_above` or `MD022.lines_below` at 2 or more
- `MD029.style` at `zero`
- `MD030` with any parameter above 1
- `MD035.style` at any explicit value but seventy underscores
- `MD046.style` at `indented`
- `MD048.style` at `tilde`
- `MD054.shortcut` false
- `MD055.style` at `leading_only`, `trailing_only` or `no_leading_or_trailing`
- `MD060.style` at `tight`, or `MD060.aligned_delimiter` true together with `compact`

None of these is a markdownlint default, so a repository with no configuration is never refused.
The one construct-level exception at the defaults, an indented code block under MD040, is not a refusal: the plugin formats the file and the author supplies the language the rule then asks for.

## Bridge candidates

Behaviours that would move a row from neutral or unsatisfiable to bridged, none of them mdformat's fixed decision, taken on when an adopter needs one, with its corpus entries, and never before:

- `MD049` and `MD050`: normalise emphasis and strong markers to the configured style, or to the document's first marker under `consistent`.
  Render-neutral except inside a word, where `_` cannot open or close emphasis and `*` can, so a marker there stays as written.
- `MD060.aligned_delimiter` with `compact`: pad the delimiter row's cells to the header's widths.
- `MD034`: wrap a bare URL in angle brackets, using the extent GFM's autolink literal actually parsed, which excludes trailing punctuation and underscores; a `www.` literal cannot be wrapped, since angle brackets make it plain text.
