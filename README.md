# RoadMark

Generate attractive **Now / Next / Later** roadmaps from a single markdown file.

RoadMark takes a structured `.md` file and outputs a self-contained HTML page — no build pipeline, no backend, no login. Open it in a browser, attach it to an email, or drop it on a static host.

---

## Installation

Requires Python 3.11+. Install with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install roadmark
```

Or install into a project:

```bash
uv add roadmark
```

---

## Usage

```bash
roadmark build my-roadmap.md
```

Outputs `my-roadmap.html` alongside the input file.

To specify an output path:

```bash
roadmark build my-roadmap.md --output /path/to/output.html
```

---

## Input format

RoadMark uses a single markdown file with YAML frontmatter for roadmap-level metadata and standard markdown headings to define columns and themes.

### Roadmap metadata (frontmatter)

```yaml
---
title: Platform Roadmap
description: Our plan for the next 12 months
owner: Jane Smith
team: Platform Team
team_link: https://example.com/platform
last_updated: 2026-03-21
---
```

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Roadmap title, shown in the header |
| `description` | No | Short summary, shown below the title |
| `owner` | No | Roadmap owner |
| `team` | No | Team name |
| `team_link` | No | URL for the team (wraps `team` as a link) |
| `last_updated` | No | Date shown in the header and footer |

### Columns and themes

Columns are defined by `##` headings. The three valid column names are `Now`, `Next`, and `Later`. Each `###` heading beneath a column becomes a theme card.

```markdown
## Now

### API Gateway Upgrade
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency
- stakeholder: CTO
- component: API
- link: https://jira.example.com/epic/101

## Next

### Observability Improvements
- objectives:
  - Add distributed tracing
- component: Infra

## Later

### Multi-region Support
- link: https://jira.example.com/epic/250
```

### Theme fields

| Field | Required | Description |
|---|---|---|
| Theme name (`###` heading) | Yes | Displayed as the card title |
| `objectives` | No | List of objectives, rendered as bullet points |
| `stakeholder` | No | Key stakeholder, shown as a tag on the card |
| `component` | No | Component or area, shown as a tag on the card |
| `link` | No | URL to an external tracker (Jira, Linear, GitHub, etc.) |

The `link` field is product-agnostic — paste any URL. It is rendered as a "View details" link on the card and does not fetch any data from the external system.

---

## Full example

```markdown
---
title: Platform Roadmap
description: Roadmap for the platform team
owner: Jane Smith
team: Platform Team
team_link: https://example.com/platform
last_updated: 2026-03-21
---

## Now

### API Gateway Upgrade
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency
- stakeholder: CTO
- component: API
- link: https://jira.example.com/epic/101

### Auth Refactor
- stakeholder: Security Lead
- component: Auth

## Next

### Observability Improvements
- objectives:
  - Add distributed tracing
  - Centralise log aggregation
- component: Infra

## Later

### Multi-region Support
- objectives:
  - Active-active in EU and US
- link: https://jira.example.com/epic/250
```

---

## Development

### Setup

```bash
git clone <repo>
cd roadmap
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

---

## Roadmap for RoadMark

- [ ] Confluence wiki markup export
- [ ] Image (PNG/SVG) export
- [ ] Additional themes and colour schemes
