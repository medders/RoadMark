"""Tests for the CLI."""

from pathlib import Path

from click.testing import CliRunner

from roadmark.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"


class TestBuildCommand:
    def test_build_default_output(self, tmp_path: Path) -> None:
        runner = CliRunner()
        input_file = FIXTURES / "simple.md"
        result = runner.invoke(
            cli, ["build", str(input_file), "--output", str(tmp_path / "out.html")]
        )
        assert result.exit_code == 0
        assert "Roadmap written to" in result.output

    def test_build_creates_html_file(self, tmp_path: Path) -> None:
        runner = CliRunner()
        output = tmp_path / "roadmap.html"
        result = runner.invoke(
            cli, ["build", str(FIXTURES / "simple.md"), "-o", str(output)]
        )
        assert result.exit_code == 0
        assert output.exists()
        assert output.read_text().strip().startswith("<!DOCTYPE html>")

    def test_build_full_example(self, tmp_path: Path) -> None:
        runner = CliRunner()
        output = tmp_path / "roadmap.html"
        result = runner.invoke(
            cli, ["build", str(FIXTURES / "full_example.md"), "-o", str(output)]
        )
        assert result.exit_code == 0
        content = output.read_text()
        assert "Platform Roadmap" in content
        assert "API Gateway Upgrade" in content

    def test_build_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["build", "nonexistent.md"])
        assert result.exit_code != 0

    def test_build_invalid_markdown(self, tmp_path: Path) -> None:
        runner = CliRunner()
        bad_file = tmp_path / "bad.md"
        bad_file.write_text("---\nowner: Bob\n---\n\nNo columns here.\n")
        result = runner.invoke(cli, ["build", str(bad_file)])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_default_output_path(self, tmp_path: Path) -> None:
        """Output defaults to <input>.html when --output is not given."""
        runner = CliRunner()
        import shutil

        input_file = tmp_path / "my_roadmap.md"
        shutil.copy(FIXTURES / "simple.md", input_file)
        result = runner.invoke(cli, ["build", str(input_file)])
        assert result.exit_code == 0
        assert (tmp_path / "my_roadmap.html").exists()
