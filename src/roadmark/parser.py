"""Markdown parser for RoadMark roadmap files."""

from pathlib import Path
from typing import Any

import frontmatter
import mistune
from pydantic import ValidationError

from roadmark.models import Column, FrontMatter, Roadmap, Theme

VALID_COLUMNS = {"Now", "Next", "Later"}


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
    columns = _parse_body(post.content)

    if not columns:
        raise ParseError(
            "No valid columns found. "
            "The file must contain at least one ## Now, ## Next, or ## Later heading."
        )

    return Roadmap(front_matter=front_matter, columns=columns)


def _parse_front_matter(metadata: dict[str, Any]) -> FrontMatter:
    """Build a FrontMatter model from the parsed YAML metadata dict."""
    if "title" not in metadata:
        raise ParseError("Missing required frontmatter field: 'title'")
    coerced = {
        k: str(v) if k == "last_updated" and v is not None else v
        for k, v in metadata.items()
    }
    try:
        return FrontMatter(**coerced)
    except ValidationError as exc:
        errors = "; ".join(
            f"{' -> '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        raise ParseError(f"Invalid frontmatter: {errors}") from exc


def _parse_body(content: str) -> list[Column]:
    """Walk the Markdown AST and extract columns and themes."""
    md = mistune.create_markdown(renderer=None)
    tokens: list[dict[str, Any]] = md(content)  # type: ignore[assignment]

    columns: list[Column] = []
    current_column: Column | None = None
    current_theme: Theme | None = None

    for token in tokens:
        token_type = token.get("type")

        if token_type == "heading":
            level = token.get("attrs", {}).get("level")
            text = _extract_text(token)

            if level == 2:
                if text in VALID_COLUMNS:
                    current_column = Column(name=text)
                    columns.append(current_column)
                    current_theme = None
                else:
                    current_column = None
                    current_theme = None

            elif level == 3 and current_column is not None:
                current_theme = Theme(name=text)
                current_column.themes.append(current_theme)

        elif token_type == "list" and current_theme is not None:
            _parse_theme_list(token, current_theme)

    return columns


def _parse_theme_list(token: dict[str, Any], theme: Theme) -> None:
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

        elif raw_text.lower().startswith("stakeholder:"):
            value = raw_text[len("stakeholder:") :].strip()
            if value:
                theme.stakeholder = value

        elif raw_text.lower().startswith("component:"):
            value = raw_text[len("component:") :].strip()
            if value:
                theme.component = value

        elif raw_text.lower().startswith("link:"):
            value = raw_text[len("link:") :].strip()
            if value:
                theme.link = value  # type: ignore[assignment]


def _extract_text(token: dict[str, Any]) -> str:
    """Recursively extract plain text from a token and its children."""
    if "raw" in token and not token.get("children"):
        return token["raw"]

    result = ""
    for child in token.get("children") or []:
        result += _extract_text(child)
    return result
