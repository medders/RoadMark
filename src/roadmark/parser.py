"""Markdown parser for RoadMark roadmap files."""

from pathlib import Path
from typing import Any

import frontmatter
import mistune
from pydantic import ValidationError

from roadmark.models import Column, ConfidenceT, FrontMatter, Roadmap, StatusT, Theme

VALID_COLUMNS = {"Now", "Next", "Later"}
COLUMN_ORDER = ["Now", "Next", "Later"]
VALID_STATUSES: frozenset[StatusT] = frozenset(
    {"planned", "in-progress", "blocked", "in-review"}
)
VALID_CONFIDENCES: frozenset[ConfidenceT] = frozenset(
    {"committed", "likely", "exploring"}
)


class ParseError(Exception):
    """Raised when the roadmap markdown file has a structural problem."""


def parse_file(path: Path) -> Roadmap:
    """Parse a markdown roadmap file and return a Roadmap model.

    Args:
        path: Path to the markdown file.

    Returns:
        A fully populated Roadmap instance.

    Raises:
        ParseError: If the file is missing required structure.
        FileNotFoundError: If the file does not exist.
    """
    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)

    front_matter = _parse_front_matter(post.metadata)
    columns, warnings = _parse_body(post.content)

    if not columns:
        raise ParseError(
            "No valid columns found. "
            "The file must contain at least one ## Now, ## Next, or ## Later heading."
        )

    return Roadmap(front_matter=front_matter, columns=columns, parse_warnings=warnings)


def _parse_front_matter(metadata: dict[str, Any]) -> FrontMatter:
    """Build a FrontMatter model from the parsed YAML metadata dict."""
    if "title" not in metadata:
        raise ParseError("Missing required frontmatter field: 'title'")
    coerced = {
        k: str(v) if k == "last_updated" and v is not None else v
        for k, v in metadata.items()
    }
    try:
        return FrontMatter.model_validate(coerced)
    except ValidationError as exc:
        errors = "; ".join(
            f"{' -> '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        raise ParseError(f"Invalid frontmatter: {errors}") from exc


def _parse_body(content: str) -> tuple[list[Column], list[str]]:
    """Walk the Markdown AST and extract columns and themes.

    Returns a tuple of (columns, parse_warnings).
    """
    md = mistune.create_markdown(renderer=None)
    tokens: list[dict[str, Any]] = md(content)  # type: ignore[assignment]

    columns: list[Column] = []
    warnings: list[str] = []
    current_column: Column | None = None
    current_theme: Theme | None = None

    for token in tokens:
        token_type = token.get("type")

        if token_type == "heading":
            level = token.get("attrs", {}).get("level")
            text = _extract_text(token)

            if level == 2:
                if text in VALID_COLUMNS:
                    existing = next((c for c in columns if c.name == text), None)
                    if existing is not None:
                        warnings.append(
                            f"Duplicate column heading '## {text}' — "
                            "themes merged into the first occurrence."
                        )
                        current_column = existing
                    else:
                        current_column = Column(name=text)
                        columns.append(current_column)
                    current_theme = None
                else:
                    raise ParseError(
                        f"Unrecognised column heading: {text!r}. "
                        f"Valid columns are: {', '.join(sorted(VALID_COLUMNS))}."
                    )

            elif level == 3 and current_column is not None:
                current_theme = Theme(name=text)
                current_column.themes.append(current_theme)

        elif token_type == "list" and current_theme is not None:
            assert current_column is not None
            location = f"column '{current_column.name}' > theme '{current_theme.name}'"
            _parse_theme_list(token, current_theme, warnings, location)

    columns.sort(key=lambda c: COLUMN_ORDER.index(c.name))
    return columns, warnings


_KNOWN_KEYS = frozenset(
    {
        "objectives",
        "stakeholders",
        "stakeholder",
        "components",
        "component",
        "link",
        "status",
        "confidence",
        "target",
        "summary",
    }
)


def _parse_theme_list(
    token: dict[str, Any],
    theme: Theme,
    warnings: list[str],
    location: str,
) -> None:
    """Parse a bulleted list of key: value pairs into Theme fields."""
    children: list[dict[str, Any]] = token.get("children", [])

    for item in children:
        if item.get("type") != "list_item":
            continue

        item_children: list[dict[str, Any]] = item.get("children", [])
        if not item_children:
            continue

        # The first child of a list_item is typically a block_text or paragraph
        first_child = item_children[0]
        raw_text = _extract_text(first_child).strip()

        # Extract the key (text before the first colon)
        if ":" in raw_text:
            raw_key = raw_text[: raw_text.index(":")].strip().lower()
        else:
            raw_key = raw_text.lower()

        if raw_text.lower().startswith("objectives:"):
            # Objectives may be inline ("objectives: foo") or a nested list
            inline = raw_text[len("objectives:") :].strip()
            if inline:
                theme.objectives.append(inline)
            else:
                # Look for a nested list in remaining children
                for child in item_children[1:]:
                    if child.get("type") == "list":
                        for sub_item in child.get("children", []):
                            obj_text = _extract_text(sub_item).strip()
                            if obj_text:
                                theme.objectives.append(obj_text)

        elif raw_text.lower().startswith("stakeholders:"):
            inline = raw_text[len("stakeholders:") :].strip()
            if inline:
                # Comma-separated inline form: "stakeholders: Alice, Bob"
                for v in inline.split(","):
                    v = v.strip()
                    if v:
                        theme.stakeholders.append(v)
            else:
                # Nested list form
                for child in item_children[1:]:
                    if child.get("type") == "list":
                        for sub_item in child.get("children", []):
                            value = _extract_text(sub_item).strip()
                            if value:
                                theme.stakeholders.append(value)

        elif raw_text.lower().startswith("stakeholder:"):
            # Singular shorthand: inline single value
            value = raw_text[len("stakeholder:") :].strip()
            if value:
                theme.stakeholders.append(value)

        elif raw_text.lower().startswith("components:"):
            inline = raw_text[len("components:") :].strip()
            if inline:
                # Comma-separated inline form: "components: API, Auth"
                for v in inline.split(","):
                    v = v.strip()
                    if v:
                        theme.components.append(v)
            else:
                # Nested list form
                for child in item_children[1:]:
                    if child.get("type") == "list":
                        for sub_item in child.get("children", []):
                            value = _extract_text(sub_item).strip()
                            if value:
                                theme.components.append(value)

        elif raw_text.lower().startswith("component:"):
            # Singular shorthand: inline single value
            value = raw_text[len("component:") :].strip()
            if value:
                theme.components.append(value)

        elif raw_text.lower().startswith("link:"):
            value = raw_text[len("link:") :].strip()
            if value:
                theme.link = value  # type: ignore[assignment]

        elif raw_text.lower().startswith("status:"):
            value = raw_text[len("status:") :].strip().lower()
            if value in VALID_STATUSES:
                theme.status = value  # type: ignore[assignment]
            else:
                valid = ", ".join(sorted(VALID_STATUSES))
                warnings.append(
                    f"{location}: unrecognised status {value!r} — valid values: {valid}"
                )

        elif raw_text.lower().startswith("confidence:"):
            value = raw_text[len("confidence:") :].strip().lower()
            if value in VALID_CONFIDENCES:
                theme.confidence = value  # type: ignore[assignment]
            else:
                valid = ", ".join(sorted(VALID_CONFIDENCES))
                warnings.append(
                    f"{location}: unrecognised confidence {value!r}"
                    f" — valid values: {valid}"
                )

        elif raw_text.lower().startswith("target:"):
            value = raw_text[len("target:") :].strip()
            if value:
                theme.target = value

        elif raw_text.lower().startswith("summary:"):
            value = raw_text[len("summary:") :].strip()
            if value:
                theme.summary = value

        elif raw_key and raw_key not in _KNOWN_KEYS:
            warnings.append(f"{location}: unrecognised field {raw_key!r} — ignored")


def _extract_text(token: dict[str, Any]) -> str:
    """Recursively extract plain text from a token and its children."""
    if "raw" in token and not token.get("children"):
        return str(token["raw"])

    result = ""
    for child in token.get("children") or []:
        result += _extract_text(child)
    return result
