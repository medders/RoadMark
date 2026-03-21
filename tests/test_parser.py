"""Tests for the markdown parser."""

from pathlib import Path

import pytest

from roadmark.parser import ParseError, parse_file

FIXTURES = Path(__file__).parent / "fixtures"


class TestFrontMatter:
    def test_simple_title(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        assert roadmap.front_matter.title == "Simple Roadmap"

    def test_full_front_matter(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        fm = roadmap.front_matter
        assert fm.title == "Platform Roadmap"
        assert fm.description == "Roadmap for the platform team"
        assert fm.owner == "Jane Smith"
        assert fm.team == "Platform Team"
        assert str(fm.team_link) == "https://example.com/platform"
        assert fm.last_updated == "2026-03-21"

    def test_missing_title_raises(self, tmp_path: Path) -> None:
        md = tmp_path / "no_title.md"
        md.write_text("---\nowner: Bob\n---\n\n## Now\n\n### Theme\n")
        with pytest.raises(ParseError, match="title"):
            parse_file(md)


class TestColumns:
    def test_simple_has_three_columns(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        names = [col.name for col in roadmap.columns]
        assert names == ["Now", "Next", "Later"]

    def test_no_columns_raises(self, tmp_path: Path) -> None:
        md = tmp_path / "no_columns.md"
        md.write_text("---\ntitle: Bad\n---\n\nJust some text.\n")
        with pytest.raises(ParseError, match="No valid columns"):
            parse_file(md)

    def test_partial_columns_allowed(self, tmp_path: Path) -> None:
        md = tmp_path / "partial.md"
        md.write_text("---\ntitle: Partial\n---\n\n## Now\n\n### Theme\n")
        roadmap = parse_file(md)
        assert len(roadmap.columns) == 1
        assert roadmap.columns[0].name == "Now"


class TestThemes:
    def test_simple_theme_names(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        assert roadmap.columns[0].themes[0].name == "First Theme"
        assert roadmap.columns[1].themes[0].name == "Second Theme"
        assert roadmap.columns[2].themes[0].name == "Third Theme"

    def test_full_theme_fields(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        now_themes = roadmap.columns[0].themes
        gateway = now_themes[0]
        assert gateway.name == "API Gateway Upgrade"
        assert gateway.objectives == ["Improve throughput by 30%", "Reduce p99 latency"]
        assert gateway.stakeholder == "CTO"
        assert gateway.component == "API"
        assert str(gateway.link) == "https://jira.example.com/epic/101"

    def test_optional_fields_default_to_none(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        theme = roadmap.columns[0].themes[0]
        assert theme.objectives == []
        assert theme.stakeholder is None
        assert theme.component is None
        assert theme.link is None

    def test_theme_without_link(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        auth = roadmap.columns[0].themes[1]
        assert auth.name == "Auth Refactor"
        assert auth.stakeholder == "Security Lead"
        assert auth.link is None

    def test_multiple_themes_per_column(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        assert len(roadmap.columns[0].themes) == 2
