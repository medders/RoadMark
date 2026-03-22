"""Tests for the roadmap linter."""

from pathlib import Path

from click.testing import CliRunner

from roadmark.cli import cli
from roadmark.linter import Severity, lint
from roadmark.models import Column, FrontMatter, Roadmap, Theme

FIXTURES = Path(__file__).parent / "fixtures"


def _make_roadmap(
    columns: list[Column] | None = None,
    summary: str | None = None,
) -> Roadmap:
    if columns is None:
        columns = [
            Column(name="Now"),
            Column(name="Next"),
            Column(name="Later"),
        ]
    return Roadmap(
        front_matter=FrontMatter(title="Test", summary=summary),
        columns=columns,
    )


class TestColumnChecks:
    def test_missing_now_column_is_error(self) -> None:
        roadmap = _make_roadmap(columns=[Column(name="Next"), Column(name="Later")])
        result = lint(roadmap)
        assert any(
            i.severity == Severity.ERROR and "now" in i.message for i in result.issues
        )

    def test_missing_all_columns_gives_three_errors(self) -> None:
        roadmap = _make_roadmap(columns=[])
        result = lint(roadmap)
        errors = [i for i in result.issues if i.severity == Severity.ERROR]
        assert len(errors) == 3

    def test_empty_column_is_warning(self) -> None:
        roadmap = _make_roadmap()  # all three columns, all empty
        result = lint(roadmap)
        warnings = [i for i in result.warnings if "empty" in i.message.lower()]
        assert len(warnings) == 3

    def test_ok_result_when_all_columns_present_with_themes(self) -> None:
        theme = Theme(
            name="T",
            objectives=["obj"],
            status="planned",
            confidence="committed",
        )
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next", themes=[theme]),
                Column(name="Later", themes=[theme]),
            ]
        )
        result = lint(roadmap)
        assert result.ok


class TestThemeChecks:
    def test_theme_without_objectives_or_summary_warns(self) -> None:
        theme = Theme(name="T")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert any("objectives or summary" in i.message for i in result.warnings)

    def test_theme_with_summary_no_objectives_does_not_warn_about_content(self) -> None:
        theme = Theme(name="T", summary="A summary.")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert not any("objectives or summary" in i.message for i in result.issues)

    def test_missing_status_warns(self) -> None:
        theme = Theme(name="T", objectives=["obj"])
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert any("status" in i.message for i in result.warnings)

    def test_now_theme_missing_confidence_warns(self) -> None:
        theme = Theme(name="T", objectives=["obj"], status="in-progress")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert any("confidence" in i.message for i in result.warnings)

    def test_next_theme_missing_confidence_warns(self) -> None:
        theme = Theme(name="T", objectives=["obj"], status="planned")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now"),
                Column(name="Next", themes=[theme]),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert any("confidence" in i.message for i in result.warnings)

    def test_blocked_theme_with_no_explanation_warns(self) -> None:
        theme = Theme(name="T", status="blocked")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert any("explanation" in i.message for i in result.warnings)

    def test_blocked_theme_with_summary_does_not_warn_about_explanation(self) -> None:
        theme = Theme(name="T", status="blocked", summary="Waiting on legal sign-off.")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now", themes=[theme]),
                Column(name="Next"),
                Column(name="Later"),
            ]
        )
        result = lint(roadmap)
        assert not any("explanation" in i.message for i in result.issues)

    def test_later_theme_missing_confidence_does_not_warn(self) -> None:
        theme = Theme(name="T", objectives=["obj"], status="planned")
        roadmap = _make_roadmap(
            columns=[
                Column(name="Now"),
                Column(name="Next"),
                Column(name="Later", themes=[theme]),
            ]
        )
        result = lint(roadmap)
        assert not any("confidence" in i.message for i in result.issues)


class TestParseWarnings:
    def test_parse_warnings_surfaced_as_lint_warnings(self) -> None:
        roadmap = _make_roadmap()
        roadmap.parse_warnings.append(
            "column 'Now' > theme 'T': unrecognised field 'foo' — ignored"
        )
        result = lint(roadmap)
        assert any("foo" in i.message for i in result.warnings)

    def test_parse_warnings_location_and_message_split_correctly(self) -> None:
        roadmap = _make_roadmap()
        roadmap.parse_warnings.append(
            "column 'Now' > theme 'T': unrecognised status 'banana' — valid values: ..."
        )
        result = lint(roadmap)
        issue = next(i for i in result.warnings if "banana" in i.message)
        assert issue.location == "column 'Now' > theme 'T'"
        assert "banana" in issue.message

    def test_no_parse_warnings_produces_no_extra_issues(self) -> None:
        roadmap = _make_roadmap()
        assert roadmap.parse_warnings == []
        result = lint(roadmap)
        # Only the expected structural issues (empty columns etc), no parse issues
        assert not any("unrecognised" in i.message for i in result.issues)


class TestLintCliCommand:
    def test_lint_command_exits_zero_on_clean_file(self, tmp_path: Path) -> None:
        runner = CliRunner()
        md = tmp_path / "r.md"
        runner.invoke(cli, ["init", str(md)])
        result = runner.invoke(cli, ["lint", str(md)])
        assert result.exit_code == 0
        assert "No issues found" in result.output

    def test_lint_strict_exits_nonzero_on_warnings(self, tmp_path: Path) -> None:
        runner = CliRunner()
        md = tmp_path / "r.md"
        # A file with themes that lack status → generates warnings
        md.write_text(
            "---\ntitle: T\n---\n\n"
            "## Now\n\n### Theme\n- objectives:\n  - obj\n\n"
            "## Next\n\n## Later\n"
        )
        result = runner.invoke(cli, ["lint", "--strict", str(md)])
        assert result.exit_code != 0

    def test_lint_missing_column_exits_nonzero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        md = tmp_path / "bad.md"
        md.write_text(
            "---\ntitle: T\n---\n\n## Now\n\n### Theme\n- objectives:\n  - obj\n"
        )
        result = runner.invoke(cli, ["lint", str(md)])
        assert result.exit_code != 0
