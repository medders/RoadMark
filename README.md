# RoadMark

Generate attractive **Now / Next / Later** roadmaps from a single markdown file.

RoadMark takes a structured `.md` file and outputs a self-contained HTML page — no build pipeline, no backend, no login. Open it in a browser, attach it to an email, or drop it on a static host.

---

## Installation

Requires Python 3.11+. Clone the repo and install with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/medders/RoadMark.git
cd RoadMark
uv tool install .
```

Or run without installing:

```bash
uv run roadmark build my-roadmap.md
```

---

## Usage

### Create a template

```bash
roadmark init
```

Generates a `roadmap.md` file in the current directory with all supported fields pre-populated and ready to edit. Pass a filename to write elsewhere:

```bash
roadmark init my-roadmap.md
```

### Build

```bash
roadmark build my-roadmap.md
```

Outputs `my-roadmap.html` alongside the input file.

To specify an output path:

```bash
roadmark build my-roadmap.md --output /path/to/output.html
```

To use a different visual style:

```bash
roadmark build my-roadmap.md --style polished
```

RoadMark ships with 11 built-in themes. See [docs/themes.md](docs/themes.md) for a visual preview of each one.

To generate an HTML fragment for pasting into a Confluence HTML macro:

```bash
roadmark build my-roadmap.md --fragment
```

Outputs `my-roadmap.fragment.html`. Paste the file contents directly into the Confluence HTML macro.

### Lint

```bash
roadmark lint my-roadmap.md
```

Checks the file for quality issues: missing fields, invalid values, empty columns, and unrecognised keys. Exits non-zero if errors are found. Use `--strict` to also exit non-zero on warnings.

---

## Input format

RoadMark uses a single markdown file with YAML frontmatter for roadmap-level metadata and standard markdown headings to define columns and themes.

```markdown
---
title: Platform Roadmap
description: Roadmap for the platform team
owner: Jane Smith
team: Platform Team
team_link: https://example.com/platform
last_updated: 2026-03-21
summary: |
  This quarter we're focused on reliability and developer experience.
---

## Now

### API Gateway Upgrade
- summary: Replace the legacy gateway to meet SLA commitments.
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency below 50 ms
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholders: CTO, Head of Engineering
- components: API, Gateway
- link: https://jira.example.com/epic/101

## Next

### Observability Improvements
- status: planned
- confidence: likely
- target: Q3 2026

## Later

### Multi-region Support
- summary: Active-active deployment across EU and US.
- status: planned
- confidence: exploring
```

Items further out on the roadmap should be less specified. A `Later` item with just a `summary` and `confidence: exploring` is more honest than a fully-detailed card for work that hasn't been scoped yet.

For the complete format specification — all fields, valid values, multi-value syntax, and linting rules — see [docs/syntax.md](docs/syntax.md).

---

## Example

See [`examples/full_example.md`](examples/full_example.md) for a complete roadmap with all fields demonstrated.

```bash
roadmark build examples/full_example.md
```

---

## Development

### Setup

```bash
git clone https://github.com/medders/RoadMark.git
cd RoadMark
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### Running tests

```bash
uv run pytest
```

### Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

### Committing

This project uses [Conventional Commits](https://www.conventionalcommits.org/) enforced via [Commitizen](https://commitizen-tools.github.io/commitizen/):

```bash
cz commit
```
