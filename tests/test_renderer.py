"""Tests for the HTML renderer."""

from pathlib import Path

from roadmark.parser import parse_file
from roadmark.renderer import render

FIXTURES = Path(__file__).parent.parent / "examples"


class TestRender:
    def test_returns_html_string(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        html = render(roadmap)
        assert isinstance(html, str)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_contains_title(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        html = render(roadmap)
        assert "Simple Roadmap" in html

    def test_contains_column_names(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        html = render(roadmap)
        assert "Now" in html
        assert "Next" in html
        assert "Later" in html

    def test_contains_theme_names(self) -> None:
        roadmap = parse_file(FIXTURES / "simple.md")
        html = render(roadmap)
        assert "First Theme" in html
        assert "Second Theme" in html
        assert "Third Theme" in html

    def test_full_front_matter_rendered(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        html = render(roadmap)
        assert "Platform Roadmap" in html
        assert "@admin" in html
        assert "Platform Team" in html
        assert "2026-03-21" in html

    def test_objectives_rendered(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        html = render(roadmap)
        assert "Improve throughput by 30%" in html
        assert "Reduce p99 latency" in html

    def test_stakeholders_and_components_rendered(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        html = render(roadmap)
        assert "CTO" in html
        assert "@admin" in html
        assert "API" in html
        assert "Gateway" in html

    def test_link_rendered(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        html = render(roadmap)
        assert "https://example.com/wiki/api-gateway-upgrade" in html

    def test_edit_link_rendered_in_footer(self) -> None:
        from roadmark.models import Column, FrontMatter, Roadmap

        roadmap = Roadmap(
            front_matter=FrontMatter(
                title="T",
                edit_link="https://github.com/org/repo/edit/main/roadmap.md",  # type: ignore[arg-type]
                edit_link_text="GitHub",
            ),
            columns=[Column(name="Now")],
        )
        html = render(roadmap)
        assert "Edit on GitHub" in html
        assert "https://github.com/org/repo/edit/main/roadmap.md" in html

    def test_edit_link_uses_default_text(self) -> None:
        from roadmark.models import Column, FrontMatter, Roadmap

        roadmap = Roadmap(
            front_matter=FrontMatter(
                title="T",
                edit_link="https://github.com/org/repo",  # type: ignore[arg-type]
            ),
            columns=[Column(name="Now")],
        )
        html = render(roadmap)
        assert "Edit on Git" in html

    def test_no_edit_link_renders_no_edit_element(self) -> None:
        roadmap_no_link = parse_file(FIXTURES / "simple.md")
        html = render(roadmap_no_link)
        assert "Edit on" not in html

    def test_html_is_escaped(self) -> None:
        """User content with special characters should be escaped."""
        from roadmark.models import Column, FrontMatter, Roadmap, Theme

        roadmap = Roadmap(
            front_matter=FrontMatter(title="<script>alert('xss')</script>"),
            columns=[
                Column(
                    name="Now",
                    themes=[Theme(name="<b>bold theme</b>")],
                )
            ],
        )
        html = render(roadmap)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
