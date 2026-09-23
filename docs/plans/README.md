# Plans

One-time procedures tracked to completion, then **retired** — the file is deleted in a second pull request once its work is done and the retirement is confirmed.
The permanent record of what a plan produced lives in ADRs, reference docs and the code, not here.
Contrast [`../reference/`](../reference/) (information-oriented lookup docs, not procedures).

A plan has a status line at the top, a goal, and numbered checkbox steps (`- [ ]` / `- [x]`); the pull request that completes a step is the one that ticks it.

| Plan | Status |
| -- | -- |
| [`build-out.md`](build-out.md) | In progress — skeleton, founding decisions, the compatibility matrix, the Markdown CI, the package skeleton with the corpus harness, the config package with its cases, the corpus, the plugin's configuration reader, the options it derives and the first refusals landed; next the other behaviours that act on the configuration |
