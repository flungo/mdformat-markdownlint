# The corpus

The test suite that proves the compatibility contract ([ADR-002](../decisions/002-the-compatibility-contract.md)): one input per markdownlint rule and option value, formatted with the plugin and then linted, asserting the status the [compatibility matrix](compatibility-matrix.md) gives that row.
The matrix is the human-readable form of the corpus and the two must agree; a status that changes in one changes in the other in the same pull request.

## Layout

| Path | Purpose |
| -- | -- |
| `tests/corpus/<case>/` | One directory per case, named for the configuration its documents share. `baseline` is markdownlint's defaults and `preset` the config package alone; every other case is the preset with one thing the subject, and is named for it: a rule at the preset's own settings (`md018`), a rule's `style` at a value (`md003-atx`), any other option at a value (`md025-level-2`), a boolean at true (`md041-allow-preamble`), a string emptied (`md001-front-matter-title-empty`), or markdownlint's comment directives (`inline-configuration`). A construct that is the exception to a row under the same configuration is a document of that case with its own status, never a case of its own |
| `tests/corpus/<case>/case.toml` | The case's status, the rule it exercises where it does, and one entry per document |
| `tests/corpus/<case>/*.md` | The documents the case formats and lints. A rule case carries at least one that violates the rule and one already in mdformat's style that formatting must leave byte for byte; a baseline case carries one in mdformat's style and one consistent in the styles mdformat does not write, which markdownlint's defaults accept before and after formatting and the preset reports only before |
| `tests/documents/*.md` | The pool: a document more than one case runs, written once and named from each case's `case.toml` by `from`, so a document that behaves in a known way under several configurations is the same bytes in every case that runs it; a pooled document no case names fails the suite |
| `tests/corpus/<case>/.markdownlint-cli2.jsonc` | The markdownlint configuration the case runs under; absent, markdownlint runs on its defaults. A case about a preset setting extends the config package by name, `markdownlint-config-mdformat`, as an adopter does |
| `markdownlint-config-mdformat/` | The config package the cases extend; `tests/package.json` installs it from the tree, so `npm ci --prefix tests` links it beside the markdownlint-cli2 the harness runs, and Node's resolution finds it from a case's temporary copy |
| `tests/conftest.py` | The harness: runs both tools and asserts the status |
| `tests/test_corpus.py` | One test per document, on both runs |
| `tests/test_plugin.py` | The plugin is registered under its entry point and loads with the contract's extensions |
| `lychee.toml` | The link check's configuration: the corpus documents it does not read, each one whose construct is a link the check would reject, listed by path; nothing else |
| `tests/test_link_check.py` | Every path `lychee.toml` excludes is a corpus document that exists |
| `tests/test_rules.py` | A rule ID the corpus does not know is a failure, not a skip: the installed markdownlint ships exactly the rules the corpus knows, each with its rows in the matrix and a case in the corpus; and a document reports exactly the rules its entry says it does |
| `tests/constraints.txt` | The mdformat releases the pinned leg installs |
| `tests/package.json` and its lockfile | The markdownlint-cli2 release the pinned leg installs |

## A case

`case.toml` names the status and the rule, then lists every document the case runs, its own and the pooled ones:

| Key | Values | Meaning |
| -- | -- | -- |
| `status` | `guaranteed`, `neutral`, `bridged` | The matrix status the case asserts; `unsatisfiable` joins them when the plugin's refusal lands |
| `rule` | a rule the corpus knows, or absent | The rule the case is about, required for a bridged case; absent, every finding counts, which is what a baseline case asserts. The rules the corpus knows are the ones markdownlint ships, and a case naming any other does not load |
| `inputs.<file>.from` | a filename, or absent | The pooled document under `tests/documents/` the harness copies into the case under this entry's name; absent, the document is the case's own file of that name. The case's own `.md` files are exactly the entries without `from` |
| `inputs.<file>.status` | `guaranteed`, `neutral`, `bridged`, or absent | The status this document asserts; absent, the case's. Set on a document whose construct is the exception to the rule's row under the same configuration, such as two adjacent lists under MD004, so the case stays one per configuration and the exception is an entry in it rather than a case of its own; a case naming no rule counts every finding and cannot carry one |
| `inputs.<file>.findings` | a count | How many findings the document reports before formatting, for the rule or for any rule when the case names none; every `.md` in the directory is listed, and a case naming a rule needs one document above zero, or it proves nothing |
| `inputs.<file>.incidental` | a list of rules the corpus knows, or absent | The rules beside the case's that the document reports, on some run: a rule outside the list fails the document, and so does a listed rule no run reports, so the list is exact. Each is on the construct itself, never on filler; a case naming no rule counts every finding and cannot carry one |
| `inputs.<file>.unchanged` | `true` or `false` | Whether mdformat must write the document back byte for byte, on both runs; set on a document written in mdformat's own style |
| `inputs.<file>.rewritten` | `true` or `false` | Whether mdformat must change the document, on both runs; set on a baseline document that is consistent in styles mdformat does not write, so the case cannot quietly stop exercising the formatter |

A case about a rule carries two kinds of document.
One violates the rule, in one construct per document where the rule has several, with a compliant construct beside it that formatting must not touch; its finding count asserts that exactly the constructs the case is about are what markdownlint reports.
The other is already what mdformat writes, and is `unchanged`: it proves the setting really is the formatter's output, since a preset value that differed from it would be rewritten, and it proves formatting is stable on compliant input rather than churning it.
Two documents rather than one is deliberate: the violating document alone shows the rule is satisfied after formatting, and the compliant document shows the fixed point is where the preset says it is.

For each document the harness copies the case directory twice, pooled documents included, lints the document, formats it in place, one copy with mdformat and the `gfm`, `tables` and `frontmatter` extensions alone and one with the `markdownlint` extension added, and lints both again.
Both tools run as the subprocesses an adopter runs, from the case's own directory, so the configuration markdownlint-cli2 discovers is the case's and nothing outside the case reaches either tool.
The findings before formatting must match the count the case declares, each format must exit zero, an `unchanged` document must come back byte for byte and a `rewritten` one must not; then the document's status, the case's unless its entry says otherwise, decides what the two runs must show:

| Status | Without the plugin | With the plugin |
| -- | -- | -- |
| `guaranteed` | No finding for the rule; with no rule named, no finding at all | No finding for the rule: the plugin does not break what mdformat alone holds |
| `bridged` | For a violating document, at least one finding for the rule: mdformat alone does not hold it | No finding for the rule: the plugin is what holds it |
| `neutral` | The findings for the rule are the same, by rule and count, as before formatting | The same |

A finding for a rule the corpus does not know fails the document it is on, whatever rule the case names, rather than being filtered out with the findings the case is not about.
That, with the load-time check on `rule` and the test that the installed markdownlint ships exactly the rules the corpus knows, is what makes a rule ID the corpus does not know a failure and never a skip.
A finding for a rule the corpus does know, beside the case's, fails the document too unless its entry lists that rule as `incidental`, and a listed rule no run reports fails it as a stale entry: a document reports exactly the rules its entry says it does, on every lint of every run, and the filter to the case's rule hides nothing.

Two runs rather than one keep a status honest.
A guaranteed case the plugin turns out to hold is misdeclared and belongs in bridged; a bridged case mdformat alone already satisfies is misdeclared and belongs in guaranteed; both fail, so a status claims no more than the run that earns it.

### Writing a document

The harness detects a change of meaning only through what it asserts: the findings per rule before and after formatting, on both runs, and whether the bytes changed.
A document is therefore built so that every way formatting could alter what it means moves one of those, and the rules below are the ones the corpus has needed so far.

- **Every construct the document is about is load-bearing.**
  Remove it, or the directive that governs it, and the count must change; where it does not, the assertion cannot tell the construct from its absence.
  The directive documents prove this by removal: each of `disable-line`, `disable`, `enable`, `disable-file`, `capture`, `restore` and `configure-file` is placed so that losing it adds or removes a finding, which took a capture document that disables the rule before capturing and enables it after, since a bare `restore` restores the file's initial state and changes nothing.
- **Counts are per rule, not per line or per construct.**
  A rewrite that trades one finding for another of the same rule is invisible, so a document never holds constructs whose findings could swap: the `configure-file` document has two headings its configuration allows against one it reports, so losing the configuration turns one finding into two rather than exchanging them.
- **A neutral document is rewritten wherever it can be, by a form of its own construct.**
  Neutrality asserted on a document mdformat leaves byte for byte proves nothing about formatting, so a construct mdformat rewrites sits beside the construct under test, and it is one of the same kind, so the rewrite the assertion runs across is one the rule's own constructs meet: a link's destination in angle brackets or its title in single quotes, a reference definition in mixed case, a blockquote marker with no space after it, a `1)` list marker, a fence of four backticks, a one-dash delimiter row, and beside a heading rule's construct a setext heading.
  Each of those but the last is written back without a finding for any rule.
  `unchanged` or `rewritten` is declared on every document, so the fixed point or the rewrite is asserted rather than assumed.
- **A case names a document that violates its rule**, which the loader enforces.
  A value no document can violate on its own, MD022 at `lines_above` 0, is proven in a form that can, the per-level array beside a value that is violated.
- **Constructs that behave differently are separate documents.**
  mdformat escapes a `**` run beside a space and leaves a lone `*` alone, so one document of both would be neither guaranteed nor neutral; each behaviour has its own document, with its own status where they differ.
- **A construct is checked to be what it looks like.**
  A paragraph directly below a list is a lazy continuation of the last item, a paragraph directly below a table is another row, and a blank line ends a tag-opened HTML block: each looked like the construct under test and was not, and each was found by running both tools on the draft, not by reading it.
- **Every count is taken from a run, never reasoned.**
  A document's count under each configuration it is pooled into, and each claim that losing a construct changes the count, is established by running markdownlint on the document and on the document with the construct removed.
- **A document reports no rule but its subject, and its entry lists the exceptions.**
  A finding for another rule is filtered from the count but not from the test: the entry's `incidental` list names every other rule the document reports on any run, a rule outside it fails the document, and so does a listed rule no run reports.
  Before a rule is listed the document is edited so that it stops firing, wherever the construct allows: an aligned table for a rule about pipes or cell counts, a paragraph above a table and a blockquote below it or below a list, an ordered list before the title, a title above the heading MD022 tests at a lower level.
  What is listed is on the construct itself, the setext heading whose level MD001 counts or the HTML block MD009 leaves alone, or is what mdformat makes of it, the fence with no language it writes for an indented block.
  A pooled document that reports a rule under one case lists it in that case's entry, and is split into two documents only when they are two documents, never to shorten a list.

> **🤖 Agent** — Before declaring a document's count in its manifest, remove each construct or directive the document is about and run markdownlint on the result; the count must change, or the document cannot detect losing it.

<!-- -->

> **🤖 Agent** — Before listing a rule under `incidental`, edit the document so the rule stops firing; list it only when the construct itself is what reports it.

## What a document may contain

Documents are test data, written to violate the rule their case names, so the repository's own Markdown checks skip `tests/corpus/` and `tests/documents/`: `.markdownlint-cli2.jsonc` ignores both directories and the semantic-line-break check inherits that.
The link check reads them too, so a document carries no external URL and no relative link or fragment that does not resolve, with one exception: a document whose construct is such a link, an unresolvable fragment under MD051, an empty destination under MD042 or a bare URL under MD034, is listed by path in `lychee.toml` and the check does not read it.
Its manifest says so, the list holds nothing else, and a test fails on an entry that names no corpus document.

## The two legs

The test suite runs twice per Python version in CI ([`pytest.yml`](../../.github/workflows/pytest.yml)):

| Leg | Installs | Purpose |
| -- | -- | -- |
| `pinned` | `tests/constraints.txt` and `tests/package-lock.json`, the releases the matrix's rows were established against and the ones its version table names | The contract as stated holds |
| `latest` | The newest release of mdformat, mdformat-gfm, mdformat-frontmatter and markdownlint-cli2, ignoring the plugin's own dependency bounds | A new rule or a changed style fails here before it reaches an adopter: a rule the release adds or drops fails the rule-set test whether or not a document trips it |

A red `latest` leg is a bump waiting to be made, not a broken pull request: [bump the pin](../runbooks/running-the-corpus.md#bumping-a-pin), fix or re-establish the rows the bump changes, and change the matrix with them.
Every run prints the versions it ran against in pytest's header, which is the record of what a given run proved.
