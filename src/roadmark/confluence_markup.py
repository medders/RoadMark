"""Confluence Storage Format renderer for RoadMark roadmaps."""

from __future__ import annotations

import html
import re

from roadmark.models import ConfidenceT, Roadmap, StatusT, Theme

# Matches @username in prose; negative lookbehind avoids matching inside emails.
_MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9._-]+)")

# ── Column colour scheme ──────────────────────────────────────────────────────
_COL_HDR_BG = {"Now": "#d1fae5", "Next": "#dbeafe", "Later": "#fef3c7"}
_COL_HDR_FG = {"Now": "#065f46", "Next": "#1e3a8a", "Later": "#78350f"}
_PANEL_BORDER = {"Now": "#059669", "Next": "#2563eb", "Later": "#d97706"}
_PANEL_TITLE_BG = {"Now": "#ecfdf5", "Next": "#eff6ff", "Later": "#fffbeb"}

# Confluence status macro only supports these colour names (case-sensitive)
_STATUS_COLOUR: dict[StatusT, str] = {
    "planned": "Grey",
    "in-progress": "Blue",
    "blocked": "Red",
    "in-review": "Yellow",
}
_CONF_COLOUR: dict[ConfidenceT, str] = {
    "committed": "Green",
    "likely": "Blue",
    "exploring": "Grey",
}


def _e(text: str) -> str:
    return html.escape(str(text))


def _prose(text: str) -> str:
    """Escape *text* and expand @username mentions into Confluence user-link macros."""
    escaped = html.escape(str(text))
    return _MENTION_RE.sub(
        lambda m: (
            f'<ac:link><ri:user ri:username="{html.escape(m.group(1))}"/></ac:link>'
        ),
        escaped,
    )


def _status_macro(label: str, colour: str) -> str:
    return (
        f'<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{_e(label)}</ac:parameter>'
        f"</ac:structured-macro>"
    )


def _card(theme: Theme, col_name: str) -> str:
    border_color = _PANEL_BORDER.get(col_name, "#6b7280")
    title_bg = _PANEL_TITLE_BG.get(col_name, "#f9fafb")

    body_parts: list[str] = []

    # Status and confidence — label embedded in the badge title
    if theme.status:
        colour = _STATUS_COLOUR.get(theme.status, "Grey")
        body_parts.append(f"<p>{_status_macro(f'Status: {theme.status}', colour)}</p>")
    if theme.confidence:
        colour = _CONF_COLOUR.get(theme.confidence, "Grey")
        body_parts.append(
            f"<p>{_status_macro(f'Confidence: {theme.confidence}', colour)}</p>"
        )

    if theme.summary:
        body_parts.append(f"<p>{_prose(theme.summary)}</p>")

    if theme.objectives:
        items = "".join(f"<li>{_prose(o)}</li>" for o in theme.objectives)
        body_parts.append(f"<ul>{items}</ul>")

    if theme.target:
        body_parts.append(f"<p><strong>Target:</strong> {_e(theme.target)}</p>")
    if theme.stakeholders:
        stakeholders = ", ".join(_prose(s) for s in theme.stakeholders)
        body_parts.append(f"<p><strong>Stakeholders:</strong> {stakeholders}</p>")
    if theme.components:
        body_parts.append(
            f"<p><strong>Components:</strong> {_e(', '.join(theme.components))}</p>"
        )
    if theme.jira:
        body_parts.append(
            f'<p><ac:structured-macro ac:name="jira" ac:schema-version="1">'
            f'<ac:parameter ac:name="key">{_e(theme.jira)}</ac:parameter>'
            f"</ac:structured-macro></p>"
        )
    if theme.link:
        body_parts.append(
            f'<p><a href="{_e(str(theme.link))}">View details \u2197</a></p>'
        )

    body = "".join(body_parts) or "<p></p>"

    return (
        f'<ac:structured-macro ac:name="panel" ac:schema-version="1">'
        f'<ac:parameter ac:name="title">{_e(theme.name)}</ac:parameter>'
        f'<ac:parameter ac:name="borderStyle">solid</ac:parameter>'
        f'<ac:parameter ac:name="borderColor">{border_color}</ac:parameter>'
        f'<ac:parameter ac:name="titleBGColor">{title_bg}</ac:parameter>'
        f'<ac:parameter ac:name="bgColor">#ffffff</ac:parameter>'
        f"<ac:rich-text-body>{body}</ac:rich-text-body>"
        f"</ac:structured-macro>"
    )


def render_confluence(roadmap: Roadmap) -> str:
    """Render a Roadmap as a Confluence Storage Format XML string."""
    fm = roadmap.front_matter
    parts: list[str] = []

    # Title and description
    parts.append(f"<h1>{_e(fm.title)}</h1>")
    if fm.description:
        parts.append(f"<p><em>{_e(fm.description)}</em></p>")

    # Metadata bar
    meta: list[str] = []
    if fm.owner:
        meta.append(f"<strong>Owner:</strong> {_e(fm.owner)}")
    if fm.team:
        if fm.team_link:
            meta.append(
                f'<strong>Team:</strong> <a href="{_e(str(fm.team_link))}">'
                f"{_e(fm.team)}</a>"
            )
        else:
            meta.append(f"<strong>Team:</strong> {_e(fm.team)}")
    if fm.last_updated:
        meta.append(
            f'<strong>Last updated:</strong> <time datetime="{_e(fm.last_updated)}" />'
        )
    if meta:
        parts.append(f"<p>{' &nbsp;|&nbsp; '.join(meta)}</p>")

    if fm.summary:
        # Preserve newlines as <br/> so multi-line YAML block scalars render nicely
        safe = _prose(fm.summary.strip()).replace("\n", "<br/>")
        parts.append(f"<p>{safe}</p>")

    if fm.edit_link:
        label = fm.edit_link_text or "Edit"
        parts.append(f'<p><a href="{_e(str(fm.edit_link))}">{_e(label)}</a></p>')

    parts.append("<hr/>")

    # ── 3-column kanban table ─────────────────────────────────────────────────
    n = len(roadmap.columns)
    col_pct = f"{100 // n}%" if n else "33%"
    colgroup = "".join(f'<col style="width:{col_pct};"/>' for _ in roadmap.columns)

    header_cells = ""
    for col in roadmap.columns:
        bg = _COL_HDR_BG.get(col.name, "#f3f4f6")
        fg = _COL_HDR_FG.get(col.name, "#374151")
        count = len(col.themes)
        plural = "s" if count != 1 else ""
        header_cells += (
            f'<th style="text-align:center;background-color:{bg};color:{fg};'
            f'padding:10px;font-size:14px;">'
            f"<strong>{_e(col.name.upper())}</strong>"
            f'<br/><span style="font-size:11px;font-weight:normal;">'
            f"{count} item{plural}</span>"
            f"</th>"
        )

    card_cells = ""
    for col in roadmap.columns:
        cards = "".join(_card(theme, col.name) for theme in col.themes)
        card_cells += f'<td style="vertical-align:top;padding:8px;">{cards}</td>'

    parts.append(
        f"<table><colgroup>{colgroup}</colgroup>"
        f"<tbody>"
        f"<tr>{header_cells}</tr>"
        f"<tr>{card_cells}</tr>"
        f"</tbody></table>"
    )

    return "\n".join(parts)
