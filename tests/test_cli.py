"""Tests for the CLI."""

from pathlib import Path

from click.testing import CliRunner

from roadmark.cli import cli

FIXTURES = Path(__file__).parent.parent / "examples"


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

    def test_build_prints_parse_warnings(self, tmp_path: Path) -> None:
        runner = CliRunner()
        md = tmp_path / "warn.md"
        md.write_text(
            "---\ntitle: T\n---\n\n## Now\n\n### Theme\n"
            "- status: typo\n- unknown_field: value\n\n## Next\n\n## Later\n"
        )
        result = runner.invoke(
            cli, ["build", str(md), "--output", str(tmp_path / "out.html")]
        )
        assert result.exit_code == 0
        assert "typo" in result.output
        assert "unknown_field" in result.output

    def test_default_output_path(self, tmp_path: Path) -> None:
        """Output defaults to <input>.html when --output is not given."""
        runner = CliRunner()
        import shutil

        input_file = tmp_path / "my_roadmap.md"
        shutil.copy(FIXTURES / "simple.md", input_file)
        result = runner.invoke(cli, ["build", str(input_file)])
        assert result.exit_code == 0
        assert (tmp_path / "my_roadmap.html").exists()


class TestInitCommand:
    def test_init_creates_file(self, tmp_path: Path) -> None:
        runner = CliRunner()
        output = tmp_path / "roadmap.md"
        result = runner.invoke(cli, ["init", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert "Template roadmap written to" in result.output

    def test_init_file_is_parseable(self, tmp_path: Path) -> None:
        """The generated template should parse without error."""
        from roadmark.parser import parse_file

        runner = CliRunner()
        output = tmp_path / "roadmap.md"
        runner.invoke(cli, ["init", str(output)])
        roadmap = parse_file(output)
        assert roadmap.front_matter.title == "My Product Roadmap"
        assert len(roadmap.columns) == 3

    def test_init_contains_all_columns(self, tmp_path: Path) -> None:
        runner = CliRunner()
        output = tmp_path / "roadmap.md"
        runner.invoke(cli, ["init", str(output)])
        content = output.read_text()
        assert "## Now" in content
        assert "## Next" in content
        assert "## Later" in content

    def test_init_refuses_to_overwrite(self, tmp_path: Path) -> None:
        runner = CliRunner()
        output = tmp_path / "roadmap.md"
        output.write_text("existing content")
        result = runner.invoke(cli, ["init", str(output)])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_init_default_filename(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert Path("roadmap.md").exists()
