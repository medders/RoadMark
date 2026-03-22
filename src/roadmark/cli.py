"""CLI entry point for RoadMark."""

from pathlib import Path

import click

from roadmark.linter import Severity, lint
from roadmark.parser import ParseError, parse_file
from roadmark.renderer import DEFAULT_STYLE, list_styles, render, render_fragment

_INIT_TEMPLATE = """\
---
title: My Product Roadmap
description: One-line description shown beneath the title
owner: Your Name
team: Platform Team
team_link: https://example.com/team
last_updated: {today}
summary: |
  A paragraph of free-form context for stakeholders — why this roadmap
  exists, what the current quarter focus is, or any important caveats.
---

## Now

### Theme Name
- summary: One sentence describing what this theme is about.
- objectives:
  - First measurable outcome
  - Second measurable outcome
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholder: Jane Doe
- component: API
- link: https://example.com/epic/123

## Next

### Another Theme
- objectives:
  - Outcome to achieve
- status: planned
- confidence: likely
- target: Q3 2026

## Later

### Future Theme
- objectives:
  - Long-horizon outcome
- status: planned
- confidence: exploring
"""


@click.group()
def cli() -> None:
    """RoadMark — generate Now/Next/Later roadmaps from markdown files."""


@cli.command()
@click.argument(
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output HTML file path. Defaults to <input>.html.",
)
@click.option(
    "--style",
    "-s",
    default=DEFAULT_STYLE,
    show_default=True,
    help=f"CSS style to apply. Available: {', '.join(list_styles())}.",
)
@click.option(
    "--fragment",
    is_flag=True,
    default=False,
    help="Output an HTML fragment for pasting into a Confluence HTML macro.",
)
def build(input_file: Path, output: Path | None, style: str, fragment: bool) -> None:
    """Build an HTML roadmap from INPUT_FILE."""
    if output is None:
        suffix = ".fragment.html" if fragment else ".html"
        output = input_file.with_suffix(suffix)

    try:
        roadmap = parse_file(input_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    for warning in roadmap.parse_warnings:
        click.echo(click.style(f"Warning: {warning}", fg="yellow"), err=True)

    try:
        html = (
            render_fragment(roadmap, style=style)
            if fragment
            else render(roadmap, style=style)
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    output.write_text(html, encoding="utf-8")
    if fragment:
        click.echo(f"Fragment written to {output}")
        click.echo("Paste the file contents into the Confluence HTML macro.")
    else:
        click.echo(f"Roadmap written to {output} (style: {style})")


@cli.command()
@click.argument(
    "output_file",
    type=click.Path(dir_okay=False, path_type=Path),
    default="roadmap.md",
)
def init(output_file: Path) -> None:
    """Create a template roadmap markdown file at OUTPUT_FILE.

    Defaults to roadmap.md in the current directory.
    """
    import datetime

    if output_file.exists():
        raise click.ClickException(f"{output_file} already exists. Remove it first.")

    today = datetime.date.today().isoformat()
    content = _INIT_TEMPLATE.format(today=today)
    output_file.write_text(content, encoding="utf-8")
    click.echo(f"Template roadmap written to {output_file}")
    click.echo(f"Run 'roadmark build {output_file}' to generate HTML.")


@cli.command()
@click.argument(
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with a non-zero code if any warnings are found.",
)
def lint_cmd(input_file: Path, strict: bool) -> None:
    """Check INPUT_FILE for roadmap quality issues."""
    try:
        roadmap = parse_file(input_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    result = lint(roadmap)

    if not result.issues:
        click.echo(click.style("No issues found.", fg="green"))
        return

    for issue in result.issues:
        if issue.severity == Severity.ERROR:
            click.echo(click.style(str(issue), fg="red"))
        else:
            click.echo(click.style(str(issue), fg="yellow"))

    n_errors = len(result.errors)
    n_warnings = len(result.warnings)
    summary = f"{n_errors} error(s), {n_warnings} warning(s)"

    if not result.ok:
        raise click.ClickException(summary)

    if strict and n_warnings:
        raise click.ClickException(summary)

    click.echo(summary)
