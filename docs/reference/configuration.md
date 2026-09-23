# How the plugin reads the markdownlint configuration

The plugin formats a file under the configuration markdownlint-cli2 would lint it with, read the way that tool reads it, so that what the linter accepts and what the formatter writes are decided by the same files.
This page states what is read, how the files combine and what the plugin refuses; the code follows markdownlint-cli2's own, at the release the corpus pins in `tests/package.json`, and the corpus runs every case's configuration through both tools.

## The files

markdownlint-cli2 reads two kinds of file in a directory, and so does the plugin:

| Kind | Names, in the order looked for | Holds |
| -- | -- | -- |
| Options | `.markdownlint-cli2.jsonc`, `.markdownlint-cli2.yaml`, `.markdownlint-cli2.cjs`, `.markdownlint-cli2.mjs` | The markdownlint-cli2 options object: `config`, `ignores`, `noInlineConfig` and the rest |
| Configuration | `.markdownlint.jsonc`, `.markdownlint.json`, `.markdownlint.yaml`, `.markdownlint.yml`, `.markdownlint.cjs`, `.markdownlint.mjs` | The markdownlint configuration object alone: rules and `extends` |

In a directory, the first present name of each kind is the one read, and both kinds may be present.
A JavaScript form is refused wherever it is the one that would be read, since reading it means running it ([ADR-001](../decisions/001-make-markdownlint-accept-mdformat.md)): the plugin stops and names the file, and the configuration is written in the JSONC or YAML form instead.

## The directories

For a file under the working directory, the directories read are the file's own and each parent up to and including the working directory, and nothing above it.
A file outside the working directory reads its own directory and each parent up to the nearest one it shares with the working directory, and then the working directory itself, whose configuration applies as if it sat at that shared parent.
Standard input, and text formatted through mdformat's API with no file name, get the working directory's configuration.

The working directory is the one mdformat is run from, as it is the one markdownlint-cli2 is run from; the two agree when they are run from the same place, which a repository's root is.

## How the files combine

Nearer directories win.
Walking from the file's directory up:

- **Options files merge.**
  A key in the nearer file replaces the same key in the farther one, except `config`, which merges rule by rule: a rule set in the nearer file replaces that rule's whole value, options and all, and a rule set only in the farther file stays.
  An empty options object changes nothing.
- **A configuration file replaces.**
  The nearest `.markdownlint.*` file is the configuration, whole; nothing from a farther directory's file of either kind reaches it.
  An empty one is the empty configuration, markdownlint's defaults.
- **A directory holding no file of either kind does not count**: its files belong to the nearest directory above it that holds one, as if they sat there.
- **Beside an options file, a configuration file wins for its own directory's files** and for the files of the empty directories below it.
  Below a directory that holds an options file, even one that sets no `config`, the farther configuration file is inherited only while no options file from the file's directory up to and including the configuration file's own sets `config`; where one does, the merged `config` applies instead, so a directory holding both files gives its configuration file to the files beside it and its options file's `config` to a subdirectory that holds an options file.

What markdownlint then lints with is the nearest configuration file where there is one, and the merged options' `config` otherwise; where neither exists, markdownlint's defaults.

## `extends`

A `config` object, in either kind of file, may `extends` another: the named file's rules come in under the file's own, which win, and the named file's own `extends` is followed the same way.
The name is resolved from the directory of the file that names it, exactly as markdownlint does:

1. **A path**, relative to that directory, or absolute, or starting with `~/` for the home directory, when a file or directory exists there.
1. **A module**, by Node's rules: `node_modules/<name>` in that directory and in each of its parents, then each directory `NODE_PATH` lists, then `~/.node_modules` and `~/.node_libraries`.
   A name resolves to a file as written or with `.js`, `.json` or `.node` added, or to a directory through its `package.json` `main`, or to its `index.js`, `index.json` or `index.node`.
   This is how [`markdownlint-config-mdformat`](../../markdownlint-config-mdformat/README.md) is found once installed.

Whatever its name, the file `extends` names is parsed as a configuration object, never run: a preset whose `main` is `index.js` is read as JSON.

## The formats

- **JSONC**, as jsonc-parser reads it for markdownlint-cli2: JSON with `//` and `/* */` comments and a trailing comma before `}` or `]`.
  Everything else jsonc-parser reports is an error here too: `NaN`, single quotes, a leading comma, an unterminated comment, text after the value.
- **YAML**, as js-yaml reads it: one document in the YAML 1.2 core schema, which is not what every YAML reader assumes, so the plugin reads it with a loader of its own ([ADR-004](../decisions/004-read-yaml-configuration-with-ruamel-under-the-core-schema.md)).
  `yes`, `no`, `on` and `off` are strings; only `true` and `false`, in lower, title or upper case, are booleans.
  `012` is twelve, `0o17` is octal, `0x1F` is hexadecimal, and `1_000`, `0b101` and `-0o7` are strings.
  There is no merge key, so `<<` is a key like any other; there is no timestamp, binary or set type; a duplicated key is an error, and so is an empty document.
- **TOML**, which only reaches a `.markdownlint.*` file and a file `extends` names: those are parsed by the first of JSONC, TOML and YAML that accepts them, whatever their name, as markdownlint's own reader does.
  So an empty `.markdownlint.yaml` is the empty configuration, since empty text is valid TOML, while an empty `.markdownlint-cli2.yaml`, read by name as YAML alone, is an error.
  A document that parses to something other than an object, a bare string or `null`, is the empty configuration.

## What the plugin refuses

The plugin stops, with a message naming the file, rather than format under a configuration it has not read:

- a JavaScript configuration file, `.cjs` or `.mjs`, of either kind, where it is the one markdownlint-cli2 would read;
- an options file that cannot be parsed, or that holds something other than an object;
- a configuration file that none of the three parsers accepts;
- an `extends` that resolves to no file, or that leads back to a file already being read;
- a setting mdformat's output can never satisfy, MD029 `zero`, MD060 `tight` or `aligned_delimiter` with `compact`, or a `style` value of either rule the plugin does not know ([the refusal set](compatibility-matrix.md#the-refusal-set)).

## What is not read

Each of these is a way markdownlint-cli2's reading and the plugin's differ, stated so that an adopter is not surprised:

- **`overrides`** in an options file are carried in the options but not applied: applying one is matching the file against its `filter` globs, which lands with the plugin's `ignores` behaviour and the glob matching it needs.
- **`--config` and `--configPointer`**, markdownlint-cli2's command-line arguments, are not arguments the plugin has; a configuration given that way is not a file in the tree.
- **A package's `exports` map** is not consulted: a module resolves through `main` or an index file.
  A preset that restricts its subpaths through `exports` resolves here where Node would refuse it.
- **Modules resolvable only from markdownlint-cli2's own installation**, which Node also searches from the linter's location, are not found; the plugin looks from the configuration file's directory, which is where a repository installs its presets.
- **`gitignore`, `globs` and the other options** that decide which files markdownlint-cli2 lints are carried in the options and not acted on, since mdformat is told its files.

## A rule's setting

A behaviour that acts on a rule's setting, such as the options derived from MD029 and MD060 ([what the plugin derives](compatibility-matrix.md#what-the-plugin-derives-from-the-markdownlint-configuration)), reads it as markdownlint's `getEffectiveConfig` resolves it, so the setting is the one the rule runs with:

- **A key names a rule by any of its names or tags**, regardless of case: `MD029`, `ol-prefix` and `ol` all reach MD029, and a tag reaches every rule that carries it.
- **A later key replaces what an earlier one set** for the same rule, whole: `{ "ol": false, "MD029": { "style": "ordered" } }` enables MD029 at `ordered`, and the same two keys in the other order disable it.
- **`default`**, wherever it sits, decides whether a rule no key names is enabled.
- **An object value enables the rule** unless it carries `enabled` false, and its members other than `enabled` and `severity` are the rule's options.
  Any other value enables the rule when it is truthy, `true`, `"warning"` or a number other than zero, and disables it otherwise, `false`, `null`, `0` or `""`, with no options either way.

## For the plugin's own behaviours

Each behaviour reads the result from the parser mdformat builds for the file, under `mdit.options["mdformat_markdownlint"]`: a `Configuration` with `config`, the markdownlint configuration object markdownlint would lint the file with and `extends` already resolved; `options`, the merged markdownlint-cli2 options object; and `files`, the configuration file of each directory read, nearest first.
The reading is cached per directory for the length of the process, so formatting a tree reads each configuration file once.
