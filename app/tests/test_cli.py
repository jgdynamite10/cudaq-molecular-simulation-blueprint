"""CLI smoke tests using Typer's runner."""

from __future__ import annotations

from typer.testing import CliRunner

from app.cli.main import app

runner = CliRunner()


def test_help_lists_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "results" in result.stdout
    assert "bench" in result.stdout


def test_info_runs() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "python_version" in result.stdout


def test_run_help_documents_backend_option() -> None:
    result = runner.invoke(app, ["run", "h2", "--help"])
    assert result.exit_code == 0
    assert "--backend" in result.stdout


def test_results_list_with_no_runs() -> None:
    result = runner.invoke(app, ["results", "list"])
    assert result.exit_code == 0
    assert "No runs found" in result.stdout
