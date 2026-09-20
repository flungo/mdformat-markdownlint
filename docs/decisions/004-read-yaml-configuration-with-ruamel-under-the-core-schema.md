# ADR-004: Read YAML configuration with ruamel.yaml under a YAML 1.2 core-schema loader

- **Date:** 2026-09-20
- **Status:** Accepted

## Context

[ADR-001](001-make-markdownlint-accept-mdformat.md) has the plugin read the markdownlint configuration the way markdownlint-cli2 does, the YAML forms included.
markdownlint-cli2 parses YAML with js-yaml, whose default schema is the YAML 1.2 core schema: `yes`, `no`, `on` and `off` are strings, `012` is twelve, `0o17` is octal, `1_000`, `0b101` and `-0o7` are strings, a date is a string, `<<` is an ordinary key, the `binary`, `set` and `timestamp` tags are errors, a duplicated key is an error, and so is an empty document.
A reader that takes a different schema formats a file under a different configuration from the one the linter checks it against, which is the disagreement the plugin exists to remove.

Python has two YAML libraries in wide use, and neither reads that schema as it stands.
PyYAML reads YAML 1.1, where `yes` is a boolean and `012` is ten.
ruamel.yaml reads YAML 1.2 by default, and diverges from js-yaml in seven places: the underscore, binary and signed-octal integer forms, dates, merge keys, the three extra tags, and key identity, where `1` and `true` collide as one key because Python's `True` equals `1`.
Both libraries expose the same kind of hook for closing the gap, a loader class whose implicit resolvers and tag constructors are class-level tables a subclass replaces, and a loader built on either that resolves only the core schema's tags, constructs only those, keeps `<<` as a key, refuses a duplicated key, stringifies keys and treats an empty stream as an error matches js-yaml on every case the corpus pinned by running js-yaml itself.
Built on both, the two loaders are the same shape and the same size.

What differs is the dependency.
mdformat-frontmatter, which the plugin declares as a dependency because the compatibility contract is stated with the `frontmatter` extension enabled, requires ruamel.yaml, so ruamel.yaml is in every adopter's tree already; PyYAML would be a second YAML library installed for the reader alone.
Against that, ruamel.yaml's application interface changed at 0.18, when its old module-level functions were removed, while PyYAML's loader classes have not changed in a decade; the hooks the loader uses exist in ruamel.yaml's current interface, and mdformat-frontmatter bounds ruamel.yaml only from below.

## Decision

**Parse the YAML forms of the markdownlint configuration with a loader built on ruamel.yaml that resolves and constructs the YAML 1.2 core schema and nothing else, as js-yaml does, rather than with PyYAML or with ruamel.yaml's own defaults.**

The plugin declares ruamel.yaml as a dependency of its own, bounded from below at the release whose interface the loader is built on, and never relies on it arriving through mdformat-frontmatter.
The loader's behaviour is pinned by tests that restate what js-yaml returned for the same text, so a ruamel.yaml release that moves a hook the loader uses fails the test suite's latest leg before an adopter meets it.

## Consequences

- An adopter installs no YAML library for this plugin beyond the one mdformat-frontmatter already brings.
- The YAML a configuration file holds means the same thing to the plugin and to the linter, edge cases included, and the reference page states the schema rather than a list of divergences.
- The loader hooks class-level tables of ruamel.yaml's safe constructor and versioned resolver, and runs on ruamel.yaml's pure-Python path, since the compiled path takes no custom resolver.
  Configuration files are small and read once per directory, so the path costs nothing an adopter notices.
- The choice rests on ruamel.yaml keeping those hooks.
  Should a release move them, the same loader built on PyYAML is the fallback, at the cost of the second dependency this decision avoids, and this record is superseded.
