"""Tests for the Confluence Storage Format renderer."""

from pathlib import Path

from roadmark.confluence_markup import _card, _status_macro, render_confluence
from roadmark.models import Column, FrontMatter, Roadmap, Theme

FIXTURES = Path(__file__).parent.parent / "examples"


def _simple_roadmap() -> Roadmap:
    return Roadmap(
        front_matter=FrontMatter(title="Test Roadmap"),
        columns=[
            Column(
                name="Now",
                themes=[
                    Theme(
                        name="Platform Reliability",
                        summary="Improve uptime across core services.",
                        status="in-progress",
                        confidence="committed",
                        target="Q2 2026",
                        stakeholders=["Jane", "Bob"],
                        components=["API", "DB"],
                        objectives=["Reduce p99 latency", "Add circuit breakers"],
                        link="https://example.com/epic/1",  # type: ignore[arg-type]
                    )
                ],
            ),
            Column(name="Next", themes=[Theme(name="Developer Tooling")]),
            Column(name="Later", themes=[]),
        ],
    )


class TestStatusMacro:
    def test_renders_macro_element(self) -> None:
        out = _status_macro("in-progress", "Blue")
        assert 'ac:name="status"' in out
        assert '<ac:parameter ac:name="colour">Blue</ac:parameter>' in out
        assert '<ac:parameter ac:name="title">in-progress</ac:parameter>' in out

    def test_escapes_special_chars(self) -> None:
        out = _status_macro("<foo>", "Grey")
        assert "<foo>" not in out
        assert "&lt;foo&gt;" in out


class TestCard:
    def test_renders_panel_macro(self) -> None:
        theme = Theme(name="Auth Overhaul", status="planned")
        out = _card(theme, "Now")
        assert 'ac:name="panel"' in out
        assert "Auth Overhaul" in out

    def test_status_badge_present(self) -> None:
        theme = Theme(name="X", status="blocked")
        out = _card(theme, "Now")
        assert 'ac:name="status"' in out
        assert ">Red<" in out
        assert "Status: blocked" in out

    def test_confidence_badge_present(self) -> None:
        theme = Theme(name="X", confidence="committed")
        out = _card(theme, "Next")
        assert ">Green<" in out
        assert "Confidence: committed" in out

    def test_uses_column_border_colour(self) -> None:
        theme = Theme(name="X")
        now = _card(theme, "Now")
        next_ = _card(theme, "Next")
        later = _card(theme, "Later")
        assert "#059669" in now
        assert "#2563eb" in next_
        assert "#d97706" in later

    def test_objectives_rendered_as_list(self) -> None:
        theme = Theme(name="X", objectives=["Goal A", "Goal B"])
        out = _card(theme, "Now")
        assert "<ul>" in out
        assert "<li>Goal A</li>" in out
        assert "<li>Goal B</li>" in out

    def test_link_plain_url(self) -> None:
        theme = Theme(name="X", link="https://example.com/123")  # type: ignore[arg-type]
        out = _card(theme, "Now")
        assert 'href="https://example.com/123"' in out
        assert 'ac:name="jira"' not in out

    def test_jira_field_renders_macro(self) -> None:
        theme = Theme(name="X", jira="PROJ-42")
        out = _card(theme, "Now")
        assert 'ac:name="jira"' in out
        assert ">PROJ-42<" in out

    def test_jira_and_link_both_render(self) -> None:
        theme = Theme(name="X", jira="PROJ-1", link="https://example.com/wiki")  # type: ignore[arg-type]
        out = _card(theme, "Now")
        assert 'ac:name="jira"' in out
        assert 'href="https://example.com/wiki"' in out

    def test_no_optional_fields(self) -> None:
        theme = Theme(name="Minimal")
        out = _card(theme, "Later")
        assert "Minimal" in out
        assert "<ul>" not in out


class TestRenderConfluence:
    def test_returns_string(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert isinstance(out, str)

    def test_title_present(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert "<h1>Test Roadmap</h1>" in out

    def test_column_headers_present(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert "NOW" in out
        assert "NEXT" in out
        assert "LATER" in out

    def test_theme_card_present(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert "Platform Reliability" in out

    def test_item_count_in_header(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert "1 item</span>" in out  # Now column
        assert "0 items</span>" in out  # Later column

    def test_metadata_bar(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(
                title="T",
                owner="Alice",
                team="Platform",
                last_updated="2026-03-25",
            ),
            columns=[],
        )
        out = render_confluence(roadmap)
        assert "Alice" in out
        assert "Platform" in out
        assert "2026-03-25" in out

    def test_summary_rendered(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(title="T", summary="Context paragraph."),
            columns=[],
        )
        out = render_confluence(roadmap)
        assert "Context paragraph." in out

    def test_edit_link_rendered(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(
                title="T",
                edit_link="https://github.com/org/repo",  # type: ignore[arg-type]
                edit_link_text="GitHub",
            ),
            columns=[],
        )
        out = render_confluence(roadmap)
        assert 'href="https://github.com/org/repo"' in out
        assert ">GitHub<" in out

    def test_empty_columns(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(title="T"),
            columns=[Column(name="Now"), Column(name="Next"), Column(name="Later")],
        )
        out = render_confluence(roadmap)
        assert "<table>" in out

    def test_full_example(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        # Smoke test: valid-ish XML (no unclosed tags for key elements)
        assert out.count("<table>") == out.count("</table>")
        assert out.count("<ul>") == out.count("</ul>")

    def test_xhtml_escaping(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(title="A & B <roadmap>"),
            columns=[],
        )
        out = render_confluence(roadmap)
        assert "A &amp; B &lt;roadmap&gt;" in out
        assert "<roadmap>" not in out

    def test_from_fixture(self) -> None:
        from roadmark.parser import parse_file

        roadmap = parse_file(FIXTURES / "full_example.md")
        out = render_confluence(roadmap)
        assert isinstance(out, str)
        assert len(out) > 100
