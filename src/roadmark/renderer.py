"""HTML renderer for RoadMark roadmaps."""

from importlib.resources import files

from jinja2 import BaseLoader, Environment

from roadmark.models import Roadmap


def render(roadmap: Roadmap) -> str:
    """Render a Roadmap model to a self-contained HTML string.

    Args:
        roadmap: The parsed roadmap to render.

    Returns:
        A fully rendered HTML string with all CSS inlined.
    """
    template_text = (
        files("roadmark.templates").joinpath("roadmap.html.jinja2").read_text()
    )
    env = Environment(loader=BaseLoader(), autoescape=True)
    template = env.from_string(template_text)
    return template.render(roadmap=roadmap)
