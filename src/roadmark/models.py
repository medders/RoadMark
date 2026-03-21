"""Data models for RoadMark roadmaps."""

from pydantic import BaseModel, HttpUrl


class FrontMatter(BaseModel):
    """Roadmap-level metadata parsed from YAML frontmatter."""

    title: str
    description: str | None = None
    owner: str | None = None
    team: str | None = None
    team_link: HttpUrl | None = None
    last_updated: str | None = None


class Theme(BaseModel):
    """A single roadmap item representing a theme."""

    name: str
    objectives: list[str] = []
    stakeholder: str | None = None
    component: str | None = None
    link: HttpUrl | None = None


class Column(BaseModel):
    """A kanban column (Now, Next, or Later) containing themes."""

    name: str
    themes: list[Theme] = []


class Roadmap(BaseModel):
    """The complete roadmap parsed from a markdown file."""

    front_matter: FrontMatter
    columns: list[Column] = []
