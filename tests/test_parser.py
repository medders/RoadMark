"""Tests for the markdown parser."""

from pathlib import Path

import pytest

from roadmark.parser import ParseError, parse_file

FIXTURES = Path(__file__).parent.parent / "examples"


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

    def test_unrecognised_column_heading_raises(self, tmp_path: Path) -> None:
        md = tmp_path / "bad_heading.md"
        md.write_text(
            "---\ntitle: T\n---\n\n## Now\n\n### Theme\n\n## Notes\n\n### Hidden\n"
        )
        with pytest.raises(ParseError, match="Unrecognised column heading"):
            parse_file(md)


class TestThemes:
    def test_simple_theme_names(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        assert roadmap.columns[0].themes[0].name == "First Theme"
        assert roadmap.columns[1].themes[0].name == "Second Theme"
        assert roadmap.columns[2].themes[0].name == "Third Theme"

    def test_full_theme_fields(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        gateway = roadmap.columns[0].themes[0]
        assert gateway.name == "API Gateway Upgrade"
        assert gateway.objectives == [
            "Improve throughput by 30%",
            "Reduce p99 latency below 50 ms",
        ]
        assert gateway.stakeholders == ["CTO", "Head of Engineering"]
        assert gateway.components == ["API", "Gateway"]
        assert str(gateway.link) == "https://jira.example.com/epic/101"
        assert gateway.status == "in-progress"
        assert gateway.confidence == "committed"
        assert gateway.target == "Q2 2026"

    def test_singular_shorthand(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        auth = roadmap.columns[0].themes[1]
        assert auth.name == "Auth Refactor"
        assert auth.stakeholders == ["Security Lead"]
        assert auth.components == ["Auth"]

    def test_optional_fields_default_to_empty(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        theme = roadmap.columns[0].themes[0]
        assert theme.objectives == []
        assert theme.stakeholders == []
        assert theme.components == []
        assert theme.link is None

    def test_theme_without_link(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        auth = roadmap.columns[0].themes[1]
        assert auth.link is None

    def test_multiple_themes_per_column(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        assert len(roadmap.columns[0].themes) == 2

    def test_multiple_stakeholders_via_list(self, tmp_path: Path) -> None:
        md = tmp_path / "multi.md"
        md.write_text(
            "---\ntitle: T\n---\n\n## Now\n\n### Theme\n"
            "- stakeholders:\n  - Alice\n  - Bob\n"
        )
        roadmap = parse_file(md)
        assert roadmap.columns[0].themes[0].stakeholders == ["Alice", "Bob"]

    def test_multiple_components_via_list(self, tmp_path: Path) -> None:
        md = tmp_path / "multi.md"
        md.write_text(
            "---\ntitle: T\n---\n\n## Now\n\n### Theme\n"
            "- components:\n  - API\n  - Auth\n"
        )
        roadmap = parse_file(md)
        assert roadmap.columns[0].themes[0].components == ["API", "Auth"]


class TestNewThemeFields:
    def _make(self, tmp_path: Path, fields: str) -> "Theme":  # noqa: F821
        md = tmp_path / "t.md"
        md.write_text(f"---\ntitle: T\n---\n\n## Now\n\n### Theme\n{fields}")
        return parse_file(md).columns[0].themes[0]

    def test_status_parsed(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- status: in-progress\n")
        assert theme.status == "in-progress"

    def test_status_blocked(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- status: blocked\n")
        assert theme.status == "blocked"

    def test_status_invalid_ignored(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- status: banana\n")
        assert theme.status is None

    def test_confidence_parsed(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- confidence: committed\n")
        assert theme.confidence == "committed"

    def test_confidence_invalid_ignored(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- confidence: definitely\n")
        assert theme.confidence is None

    def test_target_parsed(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- target: 2026 Q3\n")
        assert theme.target == "2026 Q3"

    def test_theme_summary_parsed(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "- summary: Upgrading the gateway.\n")
        assert theme.summary == "Upgrading the gateway."

    def test_new_fields_default_to_none(self, tmp_path: Path) -> None:
        theme = self._make(tmp_path, "")
        assert theme.status is None
        assert theme.confidence is None
        assert theme.target is None
        assert theme.summary is None


class TestFrontMatterSummary:
    def test_summary_parsed(self, tmp_path: Path) -> None:
        md = tmp_path / "s.md"
        md.write_text(
            "---\ntitle: T\nsummary: This quarter we focus on stability.\n---\n\n"
            "## Now\n\n### Theme\n"
        )
        roadmap = parse_file(md)
        assert roadmap.front_matter.summary == "This quarter we focus on stability."

    def test_summary_optional(self) -> None:
        from roadmark.models import FrontMatter

        fm = FrontMatter(title="T")
        assert fm.summary is None
