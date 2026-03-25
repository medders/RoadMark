"""CLI entry point for RoadMark."""

from pathlib import Path

import click

from roadmark.confluence import ConfluenceClient, ConfluenceError
from roadmark.confluence_markup import render_confluence
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
# edit_link: https://github.com/your-org/your-repo/edit/main/roadmap.md
# edit_link_text: GitHub
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
- jira: PROJ-123
- link: https://example.com/wiki/theme-details

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
    help=(
        "Output file path. Extension determines format: "
        ".html (default), .fragment.html (Confluence HTML macro), "
        ".confluence (Confluence storage format)."
    ),
)
@click.option(
    "--style",
    "-s",
    default=DEFAULT_STYLE,
    show_default=True,
    help=(
        f"CSS style to apply (HTML output only). Available: {', '.join(list_styles())}."
    ),
)
@click.option(
    "--fragment",
    is_flag=True,
    default=False,
    help="Output an HTML fragment for pasting into a Confluence HTML macro.",
)
def build(input_file: Path, output: Path | None, style: str, fragment: bool) -> None:
    """Build a roadmap from INPUT_FILE.

    Output format is determined by the --output file extension:

    \b
      .html              Full standalone HTML page (default)
      .fragment.html     HTML fragment for the Confluence HTML macro
      .confluence        Confluence Storage Format for direct API upload
    """
    if output is None:
        suffix = ".fragment.html" if fragment else ".html"
        output = input_file.with_suffix(suffix)

    try:
        roadmap = parse_file(input_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    for warning in roadmap.parse_warnings:
        click.echo(click.style(f"Warning: {warning}", fg="yellow"), err=True)

    if output.suffix == ".confluence":
        markup = render_confluence(roadmap)
        output.write_text(markup, encoding="utf-8")
        click.echo(f"Confluence markup written to {output}")
        return

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
    "input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--url",
    required=True,
    help="Confluence base URL, e.g. https://confluence.example.com",
)
@click.option("--space", required=True, help="Space key, e.g. MYSPACE")
@click.option(
    "--token",
    required=True,
    envvar="CONFLUENCE_TOKEN",
    help="Personal access token (or set CONFLUENCE_TOKEN).",
)
@click.option(
    "--title", default=None, help="Page title. Defaults to frontmatter title."
)
@click.option(
    "--parent",
    default=None,
    help="Title of an existing page to nest this page under.",
)
def publish(
    input_file: Path,
    url: str,
    space: str,
    token: str,
    title: str | None,
    parent: str | None,
) -> None:
    """Publish INPUT_FILE to Confluence as a native storage-format page.

    Creates the page if it doesn't exist; updates it if it does.

    Example:

        roadmark publish my-roadmap.md \\
            --url https://confluence.example.com \\
            --space MYSPACE --token $CONFLUENCE_TOKEN
    """
    try:
        roadmap = parse_file(input_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    for warning in roadmap.parse_warnings:
        click.echo(click.style(f"Warning: {warning}", fg="yellow"), err=True)

    page_title = title or roadmap.front_matter.title
    if not page_title:
        raise click.ClickException(
            "No title found. Set one in frontmatter or pass --title."
        )

    markup = render_confluence(roadmap)
    client = ConfluenceClient(base_url=url, token=token)

    try:
        page_url = client.publish(
            space_key=space,
            title=page_title,
            body=markup,
            parent_title=parent,
        )
    except ConfluenceError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Published: {page_url}")


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
