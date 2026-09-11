# Plans

One-time procedures tracked to completion, then **retired** — the file is deleted in a second pull request once its work is done and the retirement is confirmed.
The permanent record of what a plan produced lives in ADRs, reference docs and the code, not here.

A plan has a status line at the top, a goal, and numbered checkbox steps (`- [ ]` / `- [x]`); the pull request that completes a step is the one that ticks it.

| Plan | Status |
| --- | --- |
| [`build-out.md`](build-out.md) | In progress — skeleton, founding decisions and the Markdown CI callers landed; next the compatibility matrix, then the `markdown` flag in `terraform-github`, then the package |
