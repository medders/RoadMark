"""HTML renderer for RoadMark roadmaps."""

from importlib.resources import files

import minify_html
from jinja2 import BaseLoader, Environment

from roadmark.models import Roadmap

DEFAULT_STYLE = "default"


def list_styles() -> list[str]:
    """Return the names of all available styles, sorted alphabetically."""
    return sorted(
        p.name.removesuffix(".css")
        for p in files("roadmark.styles").iterdir()
        if p.name.endswith(".css")
    )


def load_style(name: str) -> str:
    """Load a style's CSS by name.

    Args:
        name: The style name (e.g. "default", "minimal").

    Returns:
        The CSS string for the given style.

    Raises:
        ValueError: If the style name is not recognised.
    """
    try:
        return files("roadmark.styles").joinpath(f"{name}.css").read_text()
    except FileNotFoundError:
        available = ", ".join(list_styles())
        raise ValueError(
            f"Unknown style '{name}'. Available styles: {available}"
        ) from None


def render(roadmap: Roadmap, style: str = DEFAULT_STYLE) -> str:
    """Render a Roadmap model to a self-contained HTML string.

    Args:
        roadmap: The parsed roadmap to render.
        style: The name of the CSS style to apply. Defaults to "default".

    Returns:
        A fully rendered HTML string with all CSS inlined.

    Raises:
        ValueError: If the style name is not recognised.
    """
    css = load_style(style)
    template_text = (
        files("roadmark.templates").joinpath("roadmap.html.jinja2").read_text()
    )
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(template_text)
    return template.render(roadmap=roadmap, styles=css)


def render_fragment(roadmap: Roadmap, style: str = DEFAULT_STYLE) -> str:
    """Render a Roadmap model as an HTML fragment for Confluence HTML macro embedding.

    The fragment starts with a <style> block followed by the page content —
    no <!DOCTYPE>, <html>, <head>, or <body> wrapper. Paste the output directly
    into the Confluence HTML macro.

    Args:
        roadmap: The parsed roadmap to render.
        style: The name of the CSS style to apply. Defaults to "default".

    Returns:
        An HTML fragment string starting with <style>...</style>.

    Raises:
        ValueError: If the style name is not recognised.
    """
    css = load_style(style)
    template_text = (
        files("roadmark.templates").joinpath("roadmap.fragment.html.jinja2").read_text()
    )
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(template_text)
    html = template.render(roadmap=roadmap, styles=css)
    return minify_html.minify(html, minify_css=True)
