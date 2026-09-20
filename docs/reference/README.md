# Reference

Information-oriented lookup docs — descriptive, not procedural.
If it has no steps and exists to be looked up, it goes here.
Contrast [`../plans/`](../plans/) (one-time procedures) and [`../decisions/`](../decisions/) (ADRs).

A reference doc is written in the instructional-writing style: it states the current truth, never its own history.

| Document | Purpose |
| -- | -- |
| [`compatibility-matrix.md`](compatibility-matrix.md) | Every markdownlint rule and option value with its status under this plugin — guaranteed, neutral, bridged or unsatisfiable — the two mdformat behaviours that cut across rules, the options the plugin derives from the markdownlint configuration, the mdformat behaviours no rule describes, the refusal set, and the bridge candidates |
| [`configuration.md`](configuration.md) | How the plugin reads the markdownlint configuration for a file, as markdownlint-cli2 does: the files and directories read, how they combine, `extends`, the formats, what is refused and what is not read |
| [`corpus.md`](corpus.md) | The test suite that proves the matrix: its layout, the case format, the assertion each status makes, what an input may contain, and the pinned and latest legs |
