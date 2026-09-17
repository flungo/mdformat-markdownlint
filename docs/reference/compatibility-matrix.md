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
  The MD022 and MD031 cases each carry the construct inside a tight list item as a neutral document, so the corpus asserts the exception where it applies.
- **An HTML block is written verbatim.**
  Everything from an opening tag or `<!--` to the end of the block, a multi-line comment included, is content: trailing spaces, tabs and runs of blank lines inside it survive formatting, and MD009, MD010 and MD012 report them as before.
  Each of those rules' cases carries the construct inside an HTML block as a neutral document, so the corpus asserts the exception where it applies.

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
| MD001 heading-increment | any | Neutral | [Corpus at the default](../../tests/corpus/md001/case.toml), [for `front_matter_title` empty](../../tests/corpus/md001-front-matter-title-empty/case.toml) | Heading levels are content |
| MD003 heading-style | `consistent`, `atx` | Guaranteed | [Corpus for `atx`](../../tests/corpus/md003-atx/case.toml), [for `consistent`](../../tests/corpus/md003-consistent/case.toml) | Every heading, setext or closed, in a list or a blockquote, is rewritten as open ATX |
| MD003 heading-style | `atx_closed`, `setext`, `setext_with_atx`, `setext_with_atx_closed` | Unsatisfiable | Probe | Closing hashes are dropped and setext headings converted |
| MD018 no-missing-space-atx | | Neutral | [Corpus](../../tests/corpus/md018/case.toml) | `#Heading` is a paragraph in CommonMark and is left as one |
| MD019 no-multiple-space-atx | | Guaranteed | [Corpus](../../tests/corpus/md019/case.toml) | |
| MD020 no-missing-space-closed-atx | | Neutral | [Corpus](../../tests/corpus/md020/case.toml) | `#Heading#` is a paragraph and is left as one. The one form the rule reports that is a heading, `# Heading#`, is escaped to `# Heading\#`, which removes the finding |
| MD021 no-multiple-space-closed-atx | | Guaranteed | [Corpus](../../tests/corpus/md021/case.toml) | |
| MD022 blanks-around-headings | `lines_above` and `lines_below` at 1, 0 or −1 | Guaranteed | [Corpus for 1](../../tests/corpus/md022/case.toml), [for 0 and −1 in the per-level array form](../../tests/corpus/md022-lines-1-0-minus-1/case.toml) | Blocks outside tight list items are separated by exactly one blank line, and the rule checks for at least the configured number |
| MD022 blanks-around-headings | `lines_above` or `lines_below` at 2 or more, in any form | Unsatisfiable | Probe | |
| MD022 blanks-around-headings | `include_front_matter` | Guaranteed | [Corpus](../../tests/corpus/md022-include-front-matter/case.toml) | mdformat separates front matter from the first block with a blank line |
| MD023 heading-start-left | | Guaranteed | [Corpus](../../tests/corpus/md023/case.toml) | |
| MD024 no-duplicate-heading | any | Neutral | [Corpus at the default](../../tests/corpus/md024/case.toml), [for `siblings_only`](../../tests/corpus/md024-siblings-only/case.toml) | Content |
| MD025 single-title | any | Neutral | [Corpus at the default](../../tests/corpus/md025/case.toml), [for `level`](../../tests/corpus/md025-level-2/case.toml), [for `front_matter_title` empty](../../tests/corpus/md025-front-matter-title-empty/case.toml) | Content; a front-matter title counts as the first heading, as the rule documents |
| MD026 no-trailing-punctuation | any | Neutral | [Corpus at the default](../../tests/corpus/md026/case.toml), [for `punctuation`](../../tests/corpus/md026-punctuation-question-mark/case.toml) | Content |
| MD041 first-line-heading | any | Neutral | [Corpus at the default](../../tests/corpus/md041/case.toml), [for `level`](../../tests/corpus/md041-level-2/case.toml), [for `allow_preamble`](../../tests/corpus/md041-allow-preamble/case.toml), [for `front_matter_title` empty](../../tests/corpus/md041-front-matter-title-empty/case.toml) | Content |
| MD043 required-headings | any | Neutral | [Corpus for `headings`](../../tests/corpus/md043-headings/case.toml), [for `match_case`](../../tests/corpus/md043-headings-match-case/case.toml) | Content |

## Lists

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD004 ul-style | `consistent`, `dash` | Guaranteed | [Corpus for `dash`](../../tests/corpus/md004-dash/case.toml), [for `consistent`](../../tests/corpus/md004-consistent/case.toml) | Every bullet is a dash, at every nesting level |
| MD004 ul-style | `consistent`, `dash`, on two lists written directly one after the other | Neutral | [Corpus](../../tests/corpus/md004-dash/case.toml) | The source can only express adjacent lists with different markers, so it already violates the rule; mdformat separates the lists with a blank line and keeps the second list's marker, since a dash would merge them, and no formatter can satisfy the rule there without inserting a separator. A third adjacent list is written with a dash again, so its finding goes |
| MD004 ul-style | `asterisk`, `plus`, `sublist` | Unsatisfiable | Probe | |
| MD005 list-indent | | Guaranteed | [Corpus](../../tests/corpus/md005/case.toml) | Zero-padded markers included |
| MD007 ul-indent | `indent` 2 | Guaranteed | [Corpus](../../tests/corpus/md007/case.toml) | Nested content is indented by the parent marker's width, two for a dash |
| MD007 ul-indent | any other `indent` | Unsatisfiable | Probe | |
| MD007 ul-indent | `start_indented` true | Unsatisfiable | Probe | The first level is never indented |
| MD029 ol-prefix | `one` | Guaranteed | [Corpus](../../tests/corpus/md029-one/case.toml) | At mdformat's default, every item after the first is written as `1.`; the plugin also derives `number` as `false`, so a `number = true` in mdformat's own configuration cannot contradict the rule (prototype). A list whose first item is not `1.` or `0.` violates the rule before and after formatting |
| MD029 ol-prefix | `one_or_ordered`, `ordered` | Bridged | Prototype | `number` derived as `true`. Without the derivation a list starting at `0.` renders `0. 1. 1.`, which the rule reads as ordered and rejects. A list of ten or more items is zero-padded to `01.`, which the rule accepts. A list starting at 2 or above violates the rule before and after formatting |
| MD029 ol-prefix | `zero` | Unsatisfiable | Probe | Items after the first are never `0.` |
| MD030 list-marker-space | all four parameters at 1 | Guaranteed | [Corpus](../../tests/corpus/md030/case.toml) | One space follows every marker |
| MD030 list-marker-space | any parameter above 1 | Unsatisfiable | Probe | Each parameter tested on its own |
| MD032 blanks-around-lists | | Guaranteed | [Corpus](../../tests/corpus/md032/case.toml) | A list that follows a comment the plugin keeps adjacent is the comment-adjacency row's own entry, pending |

## Whitespace and blank lines

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD009 no-trailing-spaces | any `br_spaces`, `strict` true, `list_item_empty_lines` | Guaranteed | [Corpus at the default](../../tests/corpus/md009/case.toml), [for `br_spaces` 0](../../tests/corpus/md009-br-spaces-0/case.toml), [for `strict`](../../tests/corpus/md009-strict/case.toml), [for `list_item_empty_lines`](../../tests/corpus/md009-list-item-empty-lines/case.toml) | Trailing whitespace is stripped and a hard break is written as a backslash; see the HTML-block exception |
| MD009 no-trailing-spaces | `code_blocks` true | Neutral | [Corpus](../../tests/corpus/md009-code-blocks/case.toml) | Code content is preserved |
| MD010 no-hard-tabs | `code_blocks` false | Guaranteed | [Corpus](../../tests/corpus/md010-code-blocks-false/case.toml) | Tabs in prose become spaces; see the HTML-block exception |
| MD010 no-hard-tabs | `code_blocks` true, the default, with any `ignore_code_languages` | Neutral | [Corpus at the default](../../tests/corpus/md010/case.toml), [for `ignore_code_languages`](../../tests/corpus/md010-ignore-code-languages-text/case.toml) | Tabs inside code are content |
| MD012 no-multiple-blanks | any `maximum` | Guaranteed | [Corpus for 1](../../tests/corpus/md012/case.toml), [for 2](../../tests/corpus/md012-maximum-2/case.toml) | At most one blank line separates blocks; blank lines inside code are exempt from the rule and preserved; see the HTML-block exception |
| MD013 line-length | default, with `tables` true and padded tables | Bridged | Pending | mdformat's padded tables lengthen every row to the widest cell, so a table at the limit fails on every row after formatting; the plugin derives compact tables whenever the rule measures tables and MD060 does not demand `aligned` |
| MD013 line-length | any, on lines outside tables, with compact tables or with `tables` false | Neutral | [Corpus at the defaults outside tables](../../tests/corpus/md013/case.toml), [for `line_length`](../../tests/corpus/md013-line-length-100/case.toml), [for `heading_line_length`](../../tests/corpus/md013-heading-line-length-100/case.toml), [for `code_block_line_length`](../../tests/corpus/md013-code-block-line-length-100/case.toml), [for `code_blocks` false](../../tests/corpus/md013-code-blocks-false/case.toml), [for `headings` false](../../tests/corpus/md013-headings-false/case.toml), [for `strict`](../../tests/corpus/md013-strict/case.toml), [for `stern`](../../tests/corpus/md013-stern/case.toml), [for `tables` false](../../tests/corpus/md013-tables-false/case.toml); probe for compact tables | mdformat never reflows a line at its default `wrap = keep`. Two of its rewrites can lengthen one: an escape such as `*` to `\*` adds a character, and a thematic break becomes seventy underscores, which is a finding only where `line_length` is below 70 with `strict` or `stern` |
| MD027 no-multiple-space-blockquote | any | Guaranteed | [Corpus at the default](../../tests/corpus/md027/case.toml), [for `list_items` false](../../tests/corpus/md027-list-items-false/case.toml) | Lists, fences, nested quotes and tables inside a blockquote included |
| MD028 no-blanks-blockquote | | Neutral | [Corpus](../../tests/corpus/md028/case.toml) | Two blockquotes separated by a blank line are kept as written; joining them would change the render |
| MD047 single-trailing-newline | | Guaranteed | [Corpus](../../tests/corpus/md047/case.toml) | An empty file stays empty, which the rule accepts |

## Code

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD014 commands-show-output | | Neutral | [Corpus](../../tests/corpus/md014/case.toml) | Code content |
| MD031 blanks-around-fences | outside tight list items; `list_items` false | Guaranteed | [Corpus at the default](../../tests/corpus/md031/case.toml), [for `list_items` false](../../tests/corpus/md031-list-items-false/case.toml) | See the tight-list exception |
| MD038 no-space-in-code | | Neutral | [Corpus](../../tests/corpus/md038/case.toml) | mdformat strips only the single symmetric space CommonMark itself strips, which the rule allows; every padding the rule reports is content and is kept |
| MD040 fenced-code-language | any, on fenced blocks | Neutral | [Corpus at the default](../../tests/corpus/md040/case.toml), [for `allowed_languages`](../../tests/corpus/md040-allowed-languages-text/case.toml), [for `language_only`](../../tests/corpus/md040-language-only/case.toml) | Content |
| MD040 fenced-code-language | any, on an indented code block | Unsatisfiable | Probe | An indented block is outside the rule's scope; mdformat rewrites it as a fence with no language, which puts it inside, and only the author knows the language. The one place a document that lints clean at markdownlint's defaults stops doing so after formatting; ADR-002 names it |
| MD046 code-block-style | `consistent`, `fenced` | Guaranteed | [Corpus for `fenced`](../../tests/corpus/md046-fenced/case.toml), [for `consistent`](../../tests/corpus/md046-consistent/case.toml) | Indented code is rewritten as a fence |
| MD046 code-block-style | `indented` | Unsatisfiable | Probe | |
| MD048 code-fence-style | `consistent`, `backtick` | Guaranteed | [Corpus for `backtick`](../../tests/corpus/md048-backtick/case.toml), [for `consistent`](../../tests/corpus/md048-consistent/case.toml) | Tilde fences are rewritten with backticks, lengthened where the content holds a backtick run |
| MD048 code-fence-style | `tilde` | Unsatisfiable | Probe | |

## Emphasis and inline text

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD033 no-inline-html | any | Neutral | [Corpus at the default](../../tests/corpus/md033/case.toml), [for `allowed_elements`](../../tests/corpus/md033-allowed-elements-br/case.toml), [for `table_allowed_elements`](../../tests/corpus/md033-table-allowed-elements-br/case.toml) | Content |
| MD034 no-bare-urls | | Neutral | [Corpus](../../tests/corpus/md034/case.toml) | A bare URL, `www.` literal or email address is left as written |
| MD036 no-emphasis-as-heading | any | Neutral | [Corpus at the default](../../tests/corpus/md036/case.toml), [for `punctuation` empty](../../tests/corpus/md036-punctuation-empty/case.toml) | Content |
| MD037 no-space-in-emphasis | | Neutral | [Corpus](../../tests/corpus/md037/case.toml) | A `**` or `__` run that cannot open strong emphasis is escaped, which removes the rule's finding for it; a single `*` or `_` beside a space is left as literal text, and the rule's heuristic still reports it |
| MD039 no-space-in-links | | Neutral | [Corpus](../../tests/corpus/md039/case.toml) | Stripping the spaces would change the rendered link text |
| MD044 proper-names | any | Neutral | [Corpus for `names`](../../tests/corpus/md044-names-javascript/case.toml), [for `code_blocks` false](../../tests/corpus/md044-names-javascript-code-blocks-false/case.toml), [for `html_elements` false](../../tests/corpus/md044-names-javascript-html-elements-false/case.toml) | Content; a lowercased reference label is not text to the rule |
| MD049 emphasis-style | any | Neutral | [Corpus for `consistent`](../../tests/corpus/md049/case.toml), [for `asterisk`](../../tests/corpus/md049-asterisk/case.toml), [for `underscore`](../../tests/corpus/md049-underscore/case.toml) | The marker is kept as written |
| MD050 strong-style | any | Neutral | [Corpus for `consistent`](../../tests/corpus/md050/case.toml), [for `asterisk`](../../tests/corpus/md050-asterisk/case.toml), [for `underscore`](../../tests/corpus/md050-underscore/case.toml) | The marker is kept as written |

## Links and images

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD011 no-reversed-links | | Neutral | [Corpus](../../tests/corpus/md011/case.toml) | Reversed syntax is plain text to the parser |
| MD042 no-empty-links | | Neutral | [Corpus](../../tests/corpus/md042/case.toml) | An empty destination is rewritten as `<>`, which the rule reads the same way |
| MD045 no-alt-text | | Neutral | [Corpus](../../tests/corpus/md045/case.toml) | Content |
| MD051 link-fragments | any | Neutral | [Corpus at the default](../../tests/corpus/md051/case.toml), [for `ignore_case`](../../tests/corpus/md051-ignore-case/case.toml), [for `ignored_pattern`](../../tests/corpus/md051-ignored-pattern-missing/case.toml) | Content; a non-ASCII fragment is percent-encoded and still resolves |
| MD052 reference-links-images | any | Neutral | [Corpus at the default](../../tests/corpus/md052/case.toml), [for `shortcut_syntax`](../../tests/corpus/md052-shortcut-syntax/case.toml), [for `ignored_labels` empty](../../tests/corpus/md052-shortcut-syntax-ignored-labels-empty/case.toml) | An undefined label is plain text and is left as such. markdownlint 0.41.1 reports this rule only when other rules are enabled alongside it, so the corpus never asserts it in isolation |
| MD053 link-image-reference-definitions | any | Guaranteed | [Corpus at the default](../../tests/corpus/md053/case.toml), [for `ignored_definitions` empty](../../tests/corpus/md053-ignored-definitions-empty/case.toml) | Unused and duplicate definitions are removed and the rest gathered at the end of the document, sorted by label. A definition whose label the default `ignored_definitions` covers, the `[//]: #` comment idiom, is removed too; deleting it violates nothing, and keeping it is a content-preservation behaviour of the plugin, pending |
| MD054 link-image-style | `autolink`, `inline`, `url_inline` | Neutral | [Corpus for `autolink` false](../../tests/corpus/md054-autolink-false/case.toml), [for `inline` false](../../tests/corpus/md054-inline-false/case.toml), [for `url_inline` false](../../tests/corpus/md054-url-inline-false/case.toml) | Each link keeps its style; removing redundant angle brackets around a destination and moving definitions to the end change nothing the rule classifies |
| MD054 link-image-style | `shortcut` false | Unsatisfiable | Probe | A full or collapsed reference whose text equals its label is rewritten as a shortcut reference |
| MD054 link-image-style | `collapsed` false | Guaranteed | [Corpus](../../tests/corpus/md054-collapsed-false/case.toml) | For the same reason: a collapsed reference becomes a shortcut |
| MD054 link-image-style | `full` false | Neutral | [Corpus](../../tests/corpus/md054-full-false/case.toml) | A full reference whose text equals its label becomes a shortcut, which removes the finding; one whose text differs is kept, since no other reference form carries that text |
| MD059 descriptive-link-text | any | Neutral | [Corpus at the default](../../tests/corpus/md059/case.toml), [for `prohibited_texts`](../../tests/corpus/md059-prohibited-texts-there/case.toml) | Content |

## Tables

| Rule | Setting | Status | Evidence | Notes |
| -- | -- | -- | -- | -- |
| MD055 table-pipe-style | `consistent`, `leading_and_trailing` | Guaranteed | [Corpus for `leading_and_trailing`](../../tests/corpus/md055-leading-and-trailing/case.toml), probe for `consistent` | Every row is written with a leading and a trailing pipe |
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
