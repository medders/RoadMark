# RoadMark

Generate **Now / Next / Later** roadmaps from a single markdown file.

RoadMark takes a structured `.md` file and outputs:

- A **self-contained HTML page** for local preview, email attachments, or static hosting.
- A **Confluence page** published directly via the REST API using native Storage Format — no macros, no attachments required.

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

### Build (HTML preview)

```bash
roadmark build my-roadmap.md
```

Outputs `my-roadmap.html` alongside the input file. To specify an output path:

```bash
roadmark build my-roadmap.md --output /path/to/output.html
```

### Publish to Confluence

```bash
roadmark publish my-roadmap.md \
    --url https://confluence.example.com \
    --space MYSPACE \
    --token $CONFLUENCE_TOKEN
```

Creates the page if it doesn't exist; updates it if it does. The page title defaults to the roadmap's `title` frontmatter field; override it with `--title`.

To nest the page under an existing parent:

```bash
roadmark publish my-roadmap.md --url ... --space ... --token ... --parent "Team Home"
```

To wrap the roadmap in a Confluence [excerpt macro](https://confluence.atlassian.com/doc/excerpt-macro-148062.html) so other pages can transclude it, and prepend a "do not edit" banner:

```bash
roadmark publish my-roadmap.md --url ... --space ... --token ... --as-excerpt
```

The `--token` flag reads from the `CONFLUENCE_TOKEN` environment variable if not passed directly.

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
owner: "@admin"
team: Platform Team
team_link: https://example.com/platform
last_updated: 2026-03-21
edit_link: https://github.com/your-org/your-repo/edit/main/roadmap.md
edit_link_text: Edit on GitHub
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
- stakeholders: CTO, @alice
- components: API, Gateway
- jira: PLAT-101
- link: https://example.com/wiki/api-gateway-upgrade

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

### Linting, formatting, and type checking

```bash
uv run pre-commit run --all-files
```

### Committing

This project uses [Conventional Commits](https://www.conventionalcommits.org/) enforced via [Commitizen](https://commitizen-tools.github.io/commitizen/):

```bash
cz commit
```
