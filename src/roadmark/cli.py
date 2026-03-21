"""CLI entry point for RoadMark."""

from pathlib import Path

import click

from roadmark.parser import ParseError, parse_file
from roadmark.renderer import DEFAULT_STYLE, list_styles, render


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
def build(input_file: Path, output: Path | None, style: str) -> None:
    """Build an HTML roadmap from INPUT_FILE."""
    if output is None:
        output = input_file.with_suffix(".html")

    try:
        roadmap = parse_file(input_file)
    except ParseError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        html = render(roadmap, style=style)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    output.write_text(html, encoding="utf-8")
    click.echo(f"Roadmap written to {output}")
