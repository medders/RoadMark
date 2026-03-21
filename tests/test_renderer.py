"""Tests for the HTML renderer."""

from pathlib import Path

from roadmark.parser import parse_file
from roadmark.renderer import render

FIXTURES = Path(__file__).parent / "fixtures"


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
        assert "Jane Smith" in html
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
        assert "Head of Engineering" in html
        assert "API" in html
        assert "Gateway" in html

    def test_link_rendered(self) -> None:
        roadmap = parse_file(FIXTURES / "full_example.md")
        html = render(roadmap)
        assert "https://jira.example.com/epic/101" in html

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
