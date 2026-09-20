# Architecture Decision Records

Decision-oriented records for `mdformat-markdownlint`.
ADRs are numbered sequentially and **never deleted or renumbered** — a superseded decision keeps its file with its Status updated to point at the newer ADR.

| # | Title | Status |
| -- | -- | -- |
| [001](001-make-markdownlint-accept-mdformat.md) | Bridge the two tools by making markdownlint accept mdformat, not by making mdformat obey markdownlint | Accepted |
| [002](002-the-compatibility-contract.md) | The compatibility contract: every rule variant is guaranteed, neutral, bridged or refused, and a corpus proves which | Accepted |
| [003](003-ship-the-preset-as-an-npm-package.md) | Ship the preset as an npm package beside the plugin, versioned independently | Accepted |
| [004](004-read-yaml-configuration-with-ruamel-under-the-core-schema.md) | Read YAML configuration with ruamel.yaml under a YAML 1.2 core-schema loader | Accepted |

## Adding a new ADR

1. Create `docs/decisions/<NNN>-<kebab-case-title>.md` using the template below.
1. Update this index with a one-row summary.
1. If the new decision supersedes an existing one, update the older ADR's status to `Superseded by ADR-NNN`.

### ADR template

```markdown
# ADR-NNN: Title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by ADR-MMM | Deprecated

## Context

The forces and problem motivating the decision — what made a choice necessary.

## Decision

What we will do, in active voice — the choice itself, not a discussion of options.

## Consequences

What becomes easier or harder as a result.
```
