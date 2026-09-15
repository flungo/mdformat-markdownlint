# ADR-003: Ship the preset as an npm package beside the plugin, versioned independently

- **Date:** 2026-09-14
- **Status:** Accepted

## Context

[ADR-001](001-make-markdownlint-accept-mdformat.md) makes the preset one of the three artefacts and the corpus proves it, but an adopter has to obtain it.
markdownlint resolves a configuration's `extends` as a path relative to the configuration file or, failing that, as a module name through Node's own resolution from that file's directory upward; markdownlint-cli2, markdownlint-cli and the editor extensions all go through the same library call.
A path into a checkout of this repository serves only this repository.
A copy in each adopter drifts the moment the preset changes, which defeats the single style declaration.
A file the plugin writes on demand drifts the same way and puts a Node artefact behind a Python install.

The two artefacts also have different consumers.
markdownlint's default for every rule the preset touches is `consistent`, which mdformat's output satisfies, so a formatted file lints clean without the preset; what the preset adds is pre-format drift reported in the style the formatter will produce, and one declared style.
The plugin is what makes the bridged rows hold: derived options, directive adjacency, empty compact cells, preserved comment definitions, `ignores`.
A repository with its own markdownlint configuration needs only the plugin; a repository that formats in editors and lints in CI wants the preset whether or not it needs a bridge; a toolchain with no Node of its own can install only the plugin; a repository that wants a formatter-shaped style without running the formatter can take only the preset.
Neither artefact depends on the other, and the corpus is what tests the pair.

Shareable markdownlint configurations on npm follow two conventions: owner-scoped `@owner/markdownlint-config`, and purpose-named, unscoped `markdownlint-config-<purpose>`.
This preset is named for what it agrees with, not for who owns it, and no formatter-compatibility configuration for markdownlint exists yet.

## Decision

**The preset ships as the npm package `markdownlint-config-mdformat`, from the directory of that name in this repository, with the preset file as its main entry; the plugin ships as `mdformat-markdownlint` on PyPI from the repository root; the two are versioned independently.**

An adopter installs the package and writes `"extends": "markdownlint-config-mdformat"`.
A change to the preset is a release of the npm package alone and a plugin behaviour a release of the Python package alone; the compatibility matrix names the tool versions each was verified against, and the corpus, which installs the config package from the tree and extends it by name in every case, is the test of the pair.
The repository keeps the plugin's name, the artefact with behaviour.

## Consequences

- Two release procedures, one per ecosystem, each driven by its own tag prefix and trusted publishing, recorded as a runbook when the first release is cut.
- Every corpus case also proves the packaging, since it resolves the preset the way an adopter does.
- This repository's own configuration extends the preset by path, the one adopter that does, because the repository root has no `node_modules` to resolve the name from.
- A preset-only adopter gets no bridged row, and the package's README says which rows those are; a plugin-only adopter gets every bridged row and declares the style themselves.
- A `packages/` layout with both artefacts as siblings was rejected: it would put a subdirectory fragment on every `pip install` from a git URL for a symmetry nothing needs; it remains available if a third package appears.
