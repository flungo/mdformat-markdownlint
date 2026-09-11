# ADR-002: The compatibility contract: every rule variant is guaranteed, neutral, bridged or refused, and a corpus proves which

- **Date:** 2026-09-11
- **Status:** Accepted

## Context

[ADR-001](001-make-markdownlint-accept-mdformat.md) makes the markdownlint configuration the single style declaration and leaves the plugin to bridge what a static preset cannot.
That settles the direction but not the promise: what exactly an adopter may rely on, for which rules, under which options, and how they find out when a version bump breaks it.

A promise phrased as "the formatter's output lints clean" is unfalsifiable as it stands.
markdownlint's rules split into ones a formatter can satisfy structurally, ones that judge content no formatter can decide, and ones whose options can be set to something mdformat's fixed style contradicts.
Each rule needs its own statement, per option value, and each statement needs a test that fails when it stops being true.

## Decision

**Every markdownlint rule, and every value of each of its options, carries exactly one of four statuses, and the corpus asserts it.**

| Status | Meaning | What the adopter relies on |
| --- | --- | --- |
| Guaranteed | mdformat's output cannot violate the rule under this setting | The rule never fires on a formatted file |
| Neutral | mdformat never introduces a violation, and never removes one | markdownlint remains the gate; the formatter cannot make it worse |
| Bridged | mdformat alone would violate it, and this plugin's rendering or derived options make it hold | The rule never fires on a file formatted with the plugin enabled |
| Unsatisfiable | mdformat's fixed style violates it and nothing here changes that | The plugin refuses to run under the setting and names it |

Four rules govern how the statuses are assigned:

- **The markdownlint baseline contains no unsatisfiable setting.**
  A document that lints clean with no markdownlint configuration at all must still lint clean after formatting with this plugin.
  A baseline conflict is a bug in this plugin or a fix to take upstream, never an entry in the unsatisfiable set.
  The one class this cannot reach is a construct mdformat rewrites into a rule's scope where the rule then asks for something only the author knows; the matrix names each such case, and today there is one, an indented code block under MD040.
- **mdformat's decisions stand where they satisfy the rule.**
  A behaviour that is cosmetic and lint-clean is not changed to match anyone's existing corpus, this project's author's included.
  Bridging is for a genuine conflict, not a preference.
- **A gap an existing third-party plugin closes is closed by recommending that plugin**, provided the corpus shows it actually closes the gap; the recommendation is itself a corpus entry.
- **Unsatisfiable is a refusal, not a warning.**
  Formatting under a configuration that cannot be satisfied would produce a file the repository's own gate rejects, so the plugin stops before writing and names the setting, the value, and the mdformat behaviour it conflicts with.
  A setting may move out of this status later, by a plugin feature or an upstream change, and the corpus entry that recorded the refusal becomes the test of the fix.

The corpus is one input document per rule and per option value, formatted with the plugin enabled and then linted, asserting the status above.
It runs against pinned versions of markdownlint and mdformat, and against the newest release of each so that a new rule or a changed style fails here before it reaches an adopter.
A rule ID the corpus does not know is a failure, not a skip.

## Consequences

- The reference matrix in `docs/reference/` is the human-readable form of the corpus, and the two must agree; a status that changes in one changes in the other in the same pull request.
- An adopter reads their configuration against the matrix and knows, before formatting anything, which of their settings would be refused.
- Version bumps become this project's work.
  The corpus is the drift detector the two independently evolving tools otherwise lack, and it fails in this repository's CI rather than in a consumer's pull request.
- The corpus will be the largest artefact in the repository and the one that grows with every markdownlint release; that maintenance is the price of the promise being falsifiable.
- Refusing is stricter than what an adopter might prefer in the moment.
  It is chosen because a formatter that silently emits lint-failing output teaches people to disable the linter, which is the outcome the whole project exists to avoid.
