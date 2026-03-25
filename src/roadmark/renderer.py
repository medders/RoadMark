"""HTML renderer for RoadMark roadmaps."""

from importlib.resources import files

from jinja2 import Environment, PackageLoader

from roadmark.models import Roadmap


def render(roadmap: Roadmap) -> str:
    """Render a Roadmap model to a self-contained HTML string."""
    css = files("roadmark.styles").joinpath("default.css").read_text()
    env = Environment(loader=PackageLoader("roadmark", "templates"), autoescape=True)
    template = env.get_template("roadmap.html.jinja2")
    return template.render(roadmap=roadmap, styles=css)
