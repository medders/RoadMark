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

To use a different visual style:

```bash
roadmark build my-roadmap.md --style polished
```

RoadMark ships with 8 built-in themes. See [themes.md](themes.md) for a visual preview of each one.

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
summary: |
  A paragraph of free-form context for stakeholders — why this roadmap
  exists, what the current focus is, or any important caveats.
---
```

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Roadmap title, shown in the header |
| `description` | No | Short subtitle, shown below the title |
| `owner` | No | Roadmap owner |
| `team` | No | Team name |
| `team_link` | No | URL for the team (wraps `team` as a link) |
| `last_updated` | No | Date shown in the header and footer |
| `summary` | No | Freeform context paragraph shown above the board |

### Columns and themes

Columns are defined by `##` headings. The three valid column names are `Now`, `Next`, and `Later`. Each `###` heading beneath a column becomes a theme card.

```markdown
## Now

### API Gateway Upgrade
- summary: Replace the legacy gateway to meet SLA commitments.
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency below 50 ms
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholder: CTO
- component: API
- link: https://jira.example.com/epic/101

## Next

### Observability Improvements
- objectives:
  - Add distributed tracing
  - Centralise log aggregation
- status: planned
- confidence: likely
- target: Q3 2026

## Later

### Multi-region Support
- summary: Active-active deployment across EU and US.
- status: planned
- confidence: exploring
```

### Theme fields

| Field | Required | Description |
|---|---|---|
| Theme name (`###` heading) | Yes | Displayed as the card title |
| `summary` | No | One-sentence description of the theme, shown below the title |
| `objectives` | No | List of measurable outcomes, rendered as bullet points |
| `status` | No | `planned`, `in-progress`, `blocked`, or `in-review` |
| `confidence` | No | `committed`, `likely`, or `exploring` |
| `target` | No | Target date or quarter (free-form, e.g. `Q2 2026`) |
| `stakeholder` | No | Single stakeholder (shorthand for `stakeholders`) |
| `stakeholders` | No | List of stakeholders, shown as tags on the card |
| `component` | No | Single component or area (shorthand for `components`) |
| `components` | No | List of components, shown as tags on the card |
| `link` | No | URL to an external tracker (Jira, Linear, GitHub, etc.) |

All fields except the theme name are optional. The `link` field is product-agnostic — it renders as a "View details" link and does not fetch data from the external system.

Not all themes need every field. Items further out on the roadmap should be less specified — a `Later` item with just a `summary` and `confidence: exploring` is more honest than a fully-detailed card for work that hasn't been scoped yet.

---

## Full example

See the [`examples/`](examples/) directory for ready-to-use roadmap files.

```bash
roadmark build examples/full_example.md
```

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
  The gateway upgrade and auth refactor are our top priorities;
  observability work unblocks both of them.
---

## Now

### API Gateway Upgrade
- summary: Replace the legacy gateway with a high-throughput layer to meet SLA commitments.
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency below 50 ms
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholders:
  - CTO
  - Head of Engineering
- components:
  - API
  - Gateway
- link: https://jira.example.com/epic/101

### Auth Refactor
- summary: Migrate session tokens to a compliant storage mechanism.
- objectives:
  - Remove legacy session store
  - Implement short-lived JWT rotation
- status: blocked
- confidence: likely
- target: Q2 2026
- stakeholder: Security Lead
- component: Auth

## Next

### Observability Improvements
- objectives:
  - Add distributed tracing across all services
  - Centralise log aggregation
- status: planned
- confidence: likely
- target: Q3 2026

### Developer Portal
- summary: Self-service tooling so teams can ship without a platform ticket.
- status: planned
- confidence: exploring

## Later

### Multi-region Support
- summary: Active-active deployment across EU and US to meet data-residency requirements.
- status: planned
- confidence: exploring

### Event Streaming Platform
- summary: Replace polling patterns with an event-driven architecture.
- status: planned
- confidence: exploring
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
