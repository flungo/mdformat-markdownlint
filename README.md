# mdformat-markdownlint

An [mdformat](https://github.com/hukkin/mdformat) plugin and a [markdownlint](https://github.com/DavidAnson/markdownlint) preset that keep the two tools in agreement: one style configuration, markdownlint's, and formatter output that lints clean against it.

> **Status: nothing is published yet.**
> The [compatibility matrix](docs/reference/compatibility-matrix.md) is written, and the package skeleton and the corpus harness exist; the plugin's behaviours, the preset and the corpus cases follow.
> Progress is tracked in [`docs/plans/build-out.md`](docs/plans/build-out.md).

## What it will do

mdformat has three style options and makes every other formatting decision for you.
markdownlint has fifty-three rules, most with options.
Run both on a repository and they disagree in a handful of places, and every release of either can add another.

This project takes the shape of [eslint-config-prettier](https://github.com/prettier/eslint-config-prettier), in three parts:

- **A markdownlint preset** will carry every rule setting that mdformat's fixed choices satisfy.
  Your `.markdownlint-cli2.jsonc` extends it and adds your own content rules on top.
- **The mdformat plugin** will read that same markdownlint configuration and derive the options mdformat does have, honour its `ignores`, and fix the few places where the two tools genuinely conflict: a `<!-- markdownlint-disable-next-line -->` comment stays attached to the line it governs, an empty compact table cell is rendered the way markdownlint expects, and the `[//]: #` comment definitions markdownlint tolerates are not deleted as unused.
  A setting mdformat cannot satisfy will make the plugin refuse to run, naming the setting, rather than write a file your own linter rejects.
  It targets mdformat with the mdformat-gfm and mdformat-frontmatter plugins, which it declares as dependencies.
- **A corpus** will assert, for every rule and every option value, which of four things is true: the rule cannot fire on formatted output, the formatter never makes it worse, this plugin bridges it, or it is unsatisfiable and refused.
  It will run against pinned and latest versions of both tools, so a version bump fails here first.

The rule-by-rule promise is the [compatibility matrix](docs/reference/compatibility-matrix.md), whose Evidence column says which rows a prototype already meets and which are pending; the reasoning is in the [decision records](docs/decisions/README.md).

## Documentation

- [`docs/decisions/`](docs/decisions/README.md) — architecture decision records.
- [`docs/plans/`](docs/plans/README.md) — one-time procedures in progress.
- [`docs/reference/`](docs/reference/README.md) — lookup documents, including the compatibility matrix.
