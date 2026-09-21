# ADR-005: Run the corpus in one pass over one tree, not a subprocess per document

- **Date:** 2026-09-21
- **Status:** Accepted

## Context

The corpus asserts its statuses by running both tools as an adopter runs them, as subprocesses rather than in-process calls ([ADR-002](002-the-compatibility-contract.md)).
The first harness took that per document: a copy of the case, a lint, a format, a lint, twice over, without the plugin and with it.

That is six subprocesses a document, and the corpus grew to 234 of them across 113 cases — 1404 launches a run.
Almost none of it is work.
markdownlint-cli2 costs about 0.26s of startup and 1.6ms of linting per file; mdformat costs about 0.17s and less.
So a run spent around 320s launching processes, which was the whole of the pytest job: checkout, both setups and either install came to about 15s of a 5:45 job, and the matrix is four such jobs.
It also ran on one core while the runner's other three sat idle.

Parallelism is the obvious answer and the wrong one.
It divides the launches rather than removing them, buys a factor of three where the waste is a factor of fifty, and scales the wrong way: every case added costs six more launches for as long as the harness is built this way.

The corpus is a tree of directories, which is the shape both tools already take as input.
markdownlint-cli2 resolves configuration by walking up from each file, so a directory's own `.markdownlint-cli2.jsonc` governs its documents and no others — this is how an adopter's repository works, and a case directory is that arrangement in miniature.
mdformat formats each file independently of the rest.
Neither tool has a reason to be launched per document.

## Decision

Build the whole corpus into one tree — one directory per case, its documents and its configuration beside it — and run each tool over the tree whole.

Lint the unformatted tree once for the findings every document reports before formatting, which are the same for both runs because both start from the same bytes.
Then per run, build a tree, format it in one invocation, and lint it in one more.
Five subprocesses for the corpus, against 1404.

Two things make this a change of arrangement rather than of meaning, and both were measured rather than assumed before the harness was rewritten:

- A tree-wide lint applies each case directory's own configuration, exactly as a run from inside that directory does.
  The tree's root carries no configuration for anything to inherit.
- Across all 234 documents and both runs — 468 document-runs — the batched pipeline produces byte-identical formatter output and identical findings to the per-document one.

Name every document to both tools rather than letting either walk the tree.
A case's copy carries a link to the corpus's `node_modules`, so that a case extending the config package by name resolves it as an adopter's checkout does; anything that walks the tree therefore reaches the README of every installed package.
Linting the tree by glob found 12131 files that are not corpus documents and took 174s, which is worse than the harness it replaces.
The paths are known before either tool runs, so passing them is both the correct input and the cheaper one.

Keep the per-document pipeline as `run_document`, for a case built outside the corpus, which has no tree to join, and for attributing a batched format failure.
A tree-wide format reports one exit code, so a non-zero one re-runs the formatter a document at a time on a fresh tree to name the documents it belongs to; that cost is paid on the way to a failure report and nowhere else.

Separate the assertions from the pipeline that feeds them, so a document's status is checked by the same code whichever pipeline produced the runs.

Do not parallelise the suite.
The remaining work is seconds, and a worker per core rebuilds the tree per worker, which costs more than it saves.

## Consequences

### Positive

- The suite runs in about 6s rather than 324s, and the pytest job in well under a minute rather than 5:45.
  The four-job matrix costs a fraction of the runner minutes it did.
- The cost of a new case is now its documents' own linting and formatting — under two milliseconds — rather than six process launches, so the corpus can grow with the matrix without the suite's duration tracking it.
- A local run is fast enough to sit inside the edit loop, which is what the corpus reference asks of it: every count is taken from a run, never reasoned.
- Both tools still run as an adopter runs them, and a tree-wide markdownlint-cli2 run over a repository of directories is closer to an adopter's invocation than a run per file was.

### Negative — trade-offs

- A document is no longer formatted in isolation.
  The equivalence was verified across the whole corpus, but it rests on mdformat treating files independently and on markdownlint-cli2's configuration lookup being per file; a future release of either that broke one of those would be caught as a corpus failure rather than as an obviously wrong harness.
- The tree holds what a case directory holds, the link to the corpus's `node_modules` included, so the document list is what keeps either tool inside the corpus.
  A future harness that reaches for a glob over the tree meets the same trap.
- A format that does not exit zero needs the attribution pass before it can name the document, so that one failure mode reports more slowly than it did.
- Selecting a single case with `-k` no longer costs less than the whole suite, since the pass covers every case whatever is selected.
  At six seconds this is cheaper than the per-document harness's single case was.
- The tree is built three times a run, holding three copies of the corpus at once.
  It is a few hundred small files and is gone with the temporary directory.
