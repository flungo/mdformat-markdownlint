# ADR-005: Derive mdformat's options only from explicit markdownlint settings

- **Date:** 2026-09-21
- **Status:** Accepted

## Context

[ADR-001](001-make-markdownlint-accept-mdformat.md) has the plugin derive mdformat's two style options, `number` and mdformat-gfm's `compact_tables`, from the markdownlint configuration, so that the choice is made once, in the one style declaration.
The compatibility matrix first stated the derivation as a function of the style each rule runs with, the default included: MD029's default accepts 1/2/3 numbering as `ordered` does, so it gave `number` true, and MD013 at its default measures tables and a padded table can cross its limit, so it gave `compact_tables` true wherever MD060 did not demand `aligned`.

Implementing that showed what it means at markdownlint's defaults.
MD029 and MD013 are enabled with no configuration file at all, and MD060 is at `any`, so a plugin-only adopter with no configuration would have every ordered list renumbered and every table compacted.
That is not what a formatter plugin is expected to do at the defaults: ADR-002 states that mdformat's cosmetic decisions stand, the corpus's baseline case asserts that a document in mdformat's own style comes back byte for byte, and an adopter who installs the plugin to keep the two tools in agreement has not asked for a different style.
The rows the derivation at the defaults bought are two constructs: an ordered list starting at zero, which mdformat alone renumbers `0. 1. 1.` and MD029's default reads as ordered and rejects, and a table whose padded form crosses MD013's limit.
Both are rare, and both have a narrower fix than changing every list and every table: number consecutively only a list that starts at zero, and compact only a table that would cross the limit, each a rendering decision of its own.

## Decision

**The plugin derives an option only from a markdownlint setting that names what mdformat is to write: `number` from MD029's `one` and `ordered`, `compact_tables` from MD060's `compact` and `aligned`, and nothing from a rule that is disabled or at its default; a value mdformat cannot write, or one the plugin does not know, is refused.**

At markdownlint's defaults the plugin therefore changes nothing, and mdformat's own options, from its command line or `.mdformat.toml`, stand wherever the configuration says nothing.
The two constructs the defaults leave unbridged are bridged by rendering, never by an option that reaches every list or table: a list starting at zero is numbered consecutively on its own, and a table whose padded form would cross MD013's limit is written compact on its own where MD060 allows it, each landing as a behaviour of its own with its corpus entries.

## Consequences

- Installing the plugin with no markdownlint configuration formats exactly as mdformat alone does; the baseline case keeps asserting it.
- An adopter who wants 1/2/3 numbering or compact tables says so in the markdownlint configuration, as MD029 `ordered` or MD060 `compact`, and the plugin derives the option; the preset's `one` and `aligned` derive mdformat's own defaults, so a preset adopter sees no change either.
- MD029 at `one_or_ordered` or its default is guaranteed, with the list starting at zero bridged by rendering, and MD013 at its default is bridged by rendering for a table whose padded form crosses the limit, except under MD060 `aligned`, where padding is what the configuration asks for and such a table is unsatisfiable; the matrix carries both rows as pending until the rendering lands.
- A setting that accepts what mdformat writes either way, MD060 `any` or MD029's default, leaves mdformat's own option in force rather than picking one, so an adopter's `--number` or `--compact-tables` is honoured there.
- MD029 `zero`, MD060 `tight` and `aligned_delimiter` with `compact` stop the format with a message, the first of the matrix's refusal set to be refused, and so does a `style` value of either rule the plugin does not know, since markdownlint accepts anything under one and the plugin cannot tell what mdformat should write; a value a later markdownlint adds is therefore refused until the plugin learns it.
