# Runbook: Run the corpus locally

Run the test suite the way CI runs it, on either leg, before pushing a change to the plugin, a case or a pin.
What the corpus is and how a case is written is [the corpus reference](../reference/corpus.md); this is only the procedure.

## Prerequisites

- Python 3.10 or newer, and Node.js 22 with npm, on the path.
- A checkout of this repository, as the current directory.

## The pinned leg

1. **Create a virtual environment and install the plugin with its test dependencies at the pinned releases:**

   ```sh
   python -m venv .venv
   . .venv/bin/activate
   python -m pip install -e '.[test]' -c tests/constraints.txt
   ```

1. **Install the pinned markdownlint-cli2** into `tests/node_modules/`, which is gitignored, together with a link to the config package in this tree, which the cases extend by name:

   ```sh
   npm ci --prefix tests
   ```

1. **Run it:**

   ```sh
   python -m pytest
   ```

   The header names the versions the run is against; a failing case names its directory and the findings that broke its status.
   The suite runs the cases across every core, since each one is independent of the rest and the time goes on launching the two tools rather than running them.

## Probing a draft document

The harness is the probe: a draft goes into its case before its counts are known, and the failing test reports them.

1. **Write the draft into the case directory**, or into `tests/documents/` with a `from` entry, and give its manifest entry a status, a guessed `findings` and one of `unchanged` or `rewritten`, as [the corpus reference](../reference/corpus.md) describes.
1. **Run that case alone:**

   ```sh
   python -m pytest -n0 -k <case-directory-name>
   ```

   `-n0` turns off the parallelism the whole suite wants: one case is a handful of tests, and the workers cost more than they save.
   The assertion that fails names what markdownlint reported, before formatting and after each run, with each finding's line and detail, and whether the bytes changed; correct the entry from that, never from reading the document.

1. **Prove each construct load-bearing** by removing it, or the directive that governs it, and running the case again: the count must change, or the document cannot detect losing it.
   Then restore it.
1. **Run the whole suite once the entry is right**, since a pooled document is asserted under every case that names it.

## The latest leg

The same three steps, with the installs replaced by the newest release of each tool, ignoring the plugin's own bounds on purpose:

```sh
python -m pip install --no-deps -e .
python -m pip install --upgrade pytest pytest-xdist mdformat mdformat-gfm mdformat-frontmatter ruamel.yaml 'tomli; python_version < "3.11"'
npm install --prefix tests --no-save --no-package-lock markdownlint-cli2@latest
```

The pinned leg's installs undo it; `npm ci` restores the lockfile's tree.

## Bumping a pin

1. **Change the release** in `tests/constraints.txt` or `tests/package.json`.
   For the latter, regenerate the lockfile with `npm install --prefix tests --package-lock-only`, never by hand.
1. **Run the pinned leg.**
   A case that fails is a row the bump changes: fix the plugin or re-establish the row, and change the matrix in the same pull request.
1. **Move the bound** in `pyproject.toml` and the version in the matrix's table to match.
