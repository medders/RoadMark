"""Tests for the Confluence Storage Format renderer."""

from pathlib import Path

from roadmark.confluence_markup import _card, _prose, _status_macro, render_confluence
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


class TestProse:
    def test_plain_text_escaped(self) -> None:
        assert _prose("hello <world>") == "hello &lt;world&gt;"

    def test_mention_expands_to_user_macro(self) -> None:
        out = _prose("contact @admin for access")
        assert '<ri:user ri:username="admin"/>' in out
        assert "@admin" not in out

    def test_mention_at_start_of_string(self) -> None:
        out = _prose("@alice owns this")
        assert '<ri:user ri:username="alice"/>' in out

    def test_no_match_inside_email(self) -> None:
        out = _prose("email user@example.com here")
        assert "ri:user" not in out
        assert "user@example.com" in out

    def test_multiple_mentions(self) -> None:
        out = _prose("@alice and @bob are reviewing")
        assert 'ri:username="alice"' in out
        assert 'ri:username="bob"' in out

    def test_mention_with_dots_and_hyphens(self) -> None:
        out = _prose("ask @jane.doe-smith")
        assert 'ri:username="jane.doe-smith"' in out


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

    def test_column_names_in_header(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert "NOW" in out
        assert "NEXT" in out
        assert "LATER" in out

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


class TestExcerptMode:
    def test_excerpt_wraps_body_in_macro(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap, excerpt=True)
        assert 'ac:name="excerpt"' in out
        assert "Test Roadmap" in out

    def test_excerpt_prepends_do_not_edit_banner(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap, excerpt=True)
        assert 'ac:name="info"' in out
        assert "Do not edit this page directly" in out

    def test_banner_includes_edit_link_when_present(self) -> None:
        roadmap = Roadmap(
            front_matter=FrontMatter(
                title="T",
                edit_link="https://github.com/org/repo/edit/main/roadmap.md",  # type: ignore[arg-type]
                edit_link_text="GitHub",
            ),
            columns=[],
        )
        out = render_confluence(roadmap, excerpt=True)
        assert "https://github.com/org/repo/edit/main/roadmap.md" in out
        assert ">GitHub<" in out

    def test_banner_no_edit_link_shows_fallback(self) -> None:
        roadmap = Roadmap(front_matter=FrontMatter(title="T"), columns=[])
        out = render_confluence(roadmap, excerpt=True)
        assert "roadmark publish" in out

    def test_banner_before_excerpt_macro(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap, excerpt=True)
        banner_pos = out.index('ac:name="info"')
        excerpt_pos = out.index('ac:name="excerpt"')
        assert banner_pos < excerpt_pos

    def test_no_excerpt_flag_returns_plain_body(self) -> None:
        roadmap = _simple_roadmap()
        out = render_confluence(roadmap)
        assert 'ac:name="excerpt"' not in out
        assert 'ac:name="info"' not in out
