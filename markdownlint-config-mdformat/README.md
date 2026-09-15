# markdownlint-config-mdformat

A shareable [markdownlint](https://github.com/DavidAnson/markdownlint) configuration that declares the style [mdformat](https://github.com/hukkin/mdformat) writes.
Extend it and your markdownlint configuration states the same style as your formatter: a formatted file lints clean, and drift is reported before formatting in the style the formatter will produce.

## Use

```sh
npm install --save-dev markdownlint-config-mdformat
```

Then extend it from `.markdownlint-cli2.jsonc`, adding your own rules beside it:

```jsonc
{
  "config": {
    "extends": "markdownlint-config-mdformat"
  }
}
```

A `.markdownlint.jsonc` extends it the same way, with `"extends"` at the top level.
markdownlint-cli2, markdownlint-cli and the editor extensions all resolve the name through markdownlint itself.

## What it carries

Eight settings, each one where markdownlint's default differs from, or is looser than, what mdformat writes at its own defaults:

| Rule | Setting | What mdformat writes |
| -- | -- | -- |
| MD003 heading-style | `atx` | Every heading as open ATX |
| MD004 ul-style | `dash` | Every bullet as a dash |
| MD029 ol-prefix | `one` | Every ordered-list item after the first as `1.` |
| MD035 hr-style | seventy underscores | Every thematic break |
| MD046 code-block-style | `fenced` | Indented code as a fence |
| MD048 code-fence-style | `backtick` | Every fence with backticks |
| MD055 table-pipe-style | `leading_and_trailing` | Every table row with a pipe at both ends |
| MD060 table-column-style | `aligned` | Every table cell padded to its column's widest |

Where markdownlint's default already agrees with mdformat the configuration says nothing.
MD029 and MD060 pin what mdformat writes at its defaults for the two options it does have.
If you run mdformat with `--number` or `--compact-tables`, override the rule in your own configuration to match, `ordered` or `compact`; with the mdformat plugin installed, that override is the one place the choice is made, since the plugin derives mdformat's option from it.

## What it does not do

markdownlint's default for each rule above is `consistent`, which mdformat's output already satisfies, so this configuration is not what makes a formatted file pass; it makes the linter report drift the way the formatter will fix it, and it makes your configuration the one place the style is declared.
The places where mdformat alone writes what markdownlint rejects, a `<!-- markdownlint-disable-next-line -->` comment detached from its line, an empty compact table cell, a list numbered against `MD029`, a deleted `[//]: #` definition, are the job of the mdformat plugin [`mdformat-markdownlint`](https://github.com/flungo/mdformat-markdownlint), which reads your markdownlint configuration and closes them.
The rule-by-rule contract, with and without the plugin, is the [compatibility matrix](https://github.com/flungo/mdformat-markdownlint/blob/main/docs/reference/compatibility-matrix.md).
