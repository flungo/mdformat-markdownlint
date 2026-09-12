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

2. **Install the pinned markdownlint-cli2** into `tests/node_modules/`, which is gitignored:

   ```sh
   npm ci --prefix tests
   ```

3. **Run it:**

   ```sh
   python -m pytest
   ```

   The header names the versions the run is against; a failing case names its directory and the findings that broke its status.

## The latest leg

The same three steps, with the installs replaced by the newest release of each tool, ignoring the plugin's own bounds on purpose:

```sh
python -m pip install --no-deps -e .
python -m pip install --upgrade pytest mdformat mdformat-gfm mdformat-frontmatter 'tomli; python_version < "3.11"'
npm install --prefix tests --no-save --no-package-lock markdownlint-cli2@latest
```

The pinned leg's installs undo it; `npm ci` restores the lockfile's tree.

## Bumping a pin

1. **Change the release** in `tests/constraints.txt` or `tests/package.json`.
   For the latter, regenerate the lockfile with `npm install --prefix tests --package-lock-only`, never by hand.
2. **Run the pinned leg.**
   A case that fails is a row the bump changes: fix the plugin or re-establish the row, and change the matrix in the same pull request.
3. **Move the bound** in `pyproject.toml` and the version in the matrix's table to match.
