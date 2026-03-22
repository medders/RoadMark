# RoadMark Format Specification

A RoadMark file is a single `.md` file with YAML frontmatter for roadmap metadata and standard markdown headings to define columns and themes.

```
---
title: Platform Roadmap
---

## Now

### API Gateway Upgrade
- summary: Replace the legacy gateway to meet SLA commitments.
- status: in-progress
- confidence: committed
```

---

## Summary

A RoadMark file consists of two parts: a **frontmatter block** (YAML, between `---` delimiters) and a **body** (standard markdown). The body contains column headings and theme cards. All theme fields are optional bullet-list entries beneath the theme heading.

---

## Specification

The keywords **must**, **must not**, **should**, **may**, and **optional** are used as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

### Frontmatter

1. The file **must** open with a YAML frontmatter block delimited by `---`.
2. The frontmatter **must** include a `title` field. Files without a `title` are rejected with an error.
3. The following fields are recognised in the frontmatter:

| Field | Required | Type | Description |
|---|---|---|---|
| `title` | Yes | string | Roadmap title, shown in the header. |
| `description` | No | string | Short subtitle, shown below the title. |
| `owner` | No | string | Roadmap owner's name. |
| `team` | No | string | Team name. |
| `team_link` | No | URL | URL wrapping the team name as a hyperlink. |
| `last_updated` | No | string | Date shown in the header and footer (e.g. `2026-03-21`). |
| `summary` | No | string | Freeform context paragraph shown above the board. Supports multi-line YAML block scalar (`summary: \|`). |

### Columns

4. Columns are defined by `##` headings. The three valid column names are `Now`, `Next`, and `Later` — **exact capitalisation required**.
5. At least one column **must** be present. A file with no valid columns is rejected with an error.
6. An unrecognised `##` heading (e.g. `## Notes`) **must not** appear in the file. It will be rejected with an error.
7. The output column order is always **Now → Next → Later**, regardless of the order they appear in the source file.

### Themes

8. A theme is defined by a `###` heading beneath a column. The heading text becomes the theme's title.
9. All theme fields are **optional**. A theme with only a `###` heading is valid.
10. Theme fields are expressed as a bullet list (`- key: value`) immediately beneath the `###` heading.
11. Field keys are **case-insensitive**. `- Status: in-progress` and `- status: in-progress` are equivalent.
12. An unrecognised field key (e.g. `- due_date: Q2`) produces a **warning** and is ignored. It does not cause an error.

### Theme fields

| Field | Value | Description |
|---|---|---|
| `summary` | string | One-sentence description of the theme, shown below the title. |
| `objectives` | string or list | Measurable outcomes. See [multi-value fields](#multi-value-fields). |
| `status` | see below | Current state of the theme. |
| `confidence` | see below | Delivery confidence level. |
| `target` | string | Free-form target date or quarter (e.g. `Q2 2026`, `H1`, `June`). |
| `stakeholders` | string or list | People with a stake in this theme. See [multi-value fields](#multi-value-fields). |
| `components` | string or list | Technical areas or system components involved. See [multi-value fields](#multi-value-fields). |
| `link` | URL | Link to an external tracker (Jira, Linear, GitHub, etc.), rendered as "View details". |

#### `status` values

13. The `status` field **must** be one of the following values (case-insensitive):

| Value | Meaning |
|---|---|
| `planned` | Work is identified and scoped but not yet started. |
| `in-progress` | Actively being worked on. |
| `blocked` | Work cannot proceed until an impediment is resolved. |
| `in-review` | Delivered and being evaluated. The natural end state before removing the item from the roadmap. |

The natural lifecycle is: `planned` → `in-progress` → `in-review` → *(removed from roadmap)*. `blocked` may occur at any active stage.

An invalid `status` value produces a **warning** and the field is left unset. It does not cause an error.

#### `confidence` values

14. The `confidence` field **must** be one of the following values (case-insensitive):

| Value | Meaning |
|---|---|
| `committed` | The team is confident this will be delivered as described. |
| `likely` | The current plan is for this to be delivered, but details may shift. |
| `exploring` | The need is understood but the approach and timing are uncertain. |

An invalid `confidence` value produces a **warning** and the field is left unset. It does not cause an error.

#### Multi-value fields

15. `objectives`, `stakeholders`, and `components` accept either a single inline value or multiple values.

**Inline (single value):**
```markdown
- stakeholder: CTO
- component: API
```

**Inline comma-separated (multiple values):**
```markdown
- stakeholders: CTO, Head of Engineering
- components: API, Gateway
```

**Nested list (multiple values):**
```markdown
- stakeholders:
  - CTO
  - Head of Engineering
```

The singular shorthands `stakeholder:` and `component:` always take a single inline value. Use the plural form for comma-separated or nested list syntax.

---

## Examples

### Minimal valid file

```markdown
---
title: My Roadmap
---

## Now

### Improve login performance

## Next

### Self-service account management

## Later

### Multi-region support
```

### Fully specified theme

```markdown
### API Gateway Upgrade
- summary: Replace the legacy gateway with a high-throughput layer to meet SLA commitments.
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency below 50 ms
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholders: CTO, Head of Engineering
- components: API, Gateway
- link: https://jira.example.com/epic/101
```

### Intentionally sparse Later item

```markdown
### Multi-region Support
- summary: Active-active deployment across EU and US to meet data-residency requirements.
- status: planned
- confidence: exploring
```

Later items **should** be less specified than Now items. A `confidence: exploring` theme with only a summary is more honest than a fully-detailed card for work that hasn't been scoped.

### Complete file

See [`examples/full_example.md`](../examples/full_example.md).

---

## Linting

`roadmark lint` checks a file for quality issues beyond basic validity. Warnings do not prevent the roadmap from building.

| Check | Severity |
|---|---|
| Missing `Now`, `Next`, or `Later` column | Error |
| A column has no themes | Warning |
| A theme has no `summary` and no `objectives` | Warning |
| A theme in `Now` or `Next` has no `confidence` | Warning |
| A theme has no `status` | Warning |
| A `blocked` theme has no `summary` or `objectives` | Warning |
| Invalid `status` or `confidence` value | Warning |
| Unrecognised field key | Warning |

Run with `--strict` to treat warnings as errors:

```bash
roadmark lint --strict my-roadmap.md
```

---

## FAQ

**Can I add my own fields?**
No. Unrecognised field keys are preserved as warnings in the output of `roadmark lint` and `roadmark build`, but their values are ignored. The field set is intentionally fixed to keep roadmaps consistent and comparable.

**Can I have more than three columns?**
No. `Now`, `Next`, and `Later` are the only valid columns. The three-column structure is a core constraint of the format.

**Does field order within a theme matter?**
No. `status:` can appear before or after `objectives:`. The parser reads all fields in any order.

**Can a column appear more than once?**
No. If `## Now` appears twice, the themes from the second occurrence are merged into the first, and a warning is emitted. Split your themes across the two sections if you like, but the output will combine them.

**What happens if I misspell a field value?**
`roadmark build` and `roadmark lint` will both emit a warning identifying the unrecognised value and listing the valid options. The field will be left unset for that theme.
