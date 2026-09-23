# mdformat-markdownlint

An [mdformat](https://github.com/hukkin/mdformat) plugin and a [markdownlint](https://github.com/DavidAnson/markdownlint) configuration that keep the two tools in agreement: one style configuration, markdownlint's, and formatter output that lints clean against it.

> **Status: nothing is published yet.**
> The [compatibility matrix](docs/reference/compatibility-matrix.md) is written, the package skeleton, the corpus and the config package with its cases exist, and the plugin reads the markdownlint configuration as markdownlint-cli2 does and derives mdformat's `number` and `compact_tables` from it; the other behaviours that act on it follow.
> Progress is tracked in [`docs/plans/build-out.md`](docs/plans/build-out.md).

## What it will do

mdformat has three style options and makes every other formatting decision for you.
markdownlint has fifty-three rules, most with options.
Run both on a repository and they disagree in a handful of places, and every release of either can add another.

This project takes the shape of [eslint-config-prettier](https://github.com/prettier/eslint-config-prettier), in three parts:

- **A markdownlint configuration**, the npm package [`markdownlint-config-mdformat`](markdownlint-config-mdformat/README.md), carries every rule setting that mdformat's fixed choices satisfy: eight settings whose markdownlint default differs from, or is looser than, what mdformat writes at its own defaults, each with the reason beside it.
  Your `.markdownlint-cli2.jsonc` extends it by name and adds your own content rules on top.
  It is not what makes a formatted file pass, since markdownlint's defaults already accept mdformat's output; it makes drift before formatting report in the style the formatter will produce, and it makes your configuration the one place the style is declared.
  Until it is published, it installs only from a checkout of this repository, whose own configuration is the first adopter.
- **The mdformat plugin** reads that same markdownlint configuration the way markdownlint-cli2 does, `extends` included ([how](docs/reference/configuration.md)), and will derive from it the options mdformat does have, honour its `ignores`, and fix the few places where the two tools genuinely conflict: a `<!-- markdownlint-disable-next-line -->` comment stays attached to the line it governs, an empty compact table cell is rendered the way markdownlint expects, and the `[//]: #` comment definitions markdownlint tolerates are not deleted as unused.
  A setting mdformat cannot satisfy will make the plugin refuse to run, naming the setting, rather than write a file your own linter rejects.
  It targets mdformat with the mdformat-gfm and mdformat-frontmatter plugins, which it declares as dependencies.
- **A corpus** will assert, for every rule and every option value, which of four things is true: the rule cannot fire on formatted output, the formatter never makes it worse, this plugin bridges it, or it is unsatisfiable and refused.
  It will run against pinned and latest versions of both tools, so a version bump fails here first.

The rule-by-rule promise is the [compatibility matrix](docs/reference/compatibility-matrix.md), whose Evidence column says which rows a prototype already meets and which are pending; the reasoning is in the [decision records](docs/decisions/README.md).

## Documentation

- [`docs/decisions/`](docs/decisions/README.md) — architecture decision records.
- [`docs/plans/`](docs/plans/README.md) — one-time procedures in progress.
- [`docs/reference/`](docs/reference/README.md) — lookup documents, including the compatibility matrix.
