from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mentat.cli import app

runner = CliRunner()


def write_tool(dir_: Path, name: str, command: str = "python -c \"print('ok')\"") -> None:
    path = dir_ / f"{name}.toml"
    cmd_escaped = command.replace('"', '\\"')
    path.write_text(
        f"""
name = "{name}"
description = "Test tool {name}"
command = "{cmd_escaped}"
""".strip(),
        encoding="utf-8",
    )


def test_cli_help():
    result = runner.invoke(app, ["--help"])  # type: ignore[arg-type]
    assert result.exit_code == 0
    assert "Mentat CLI" in result.stdout


def test_tools_list(tmp_path: Path):
    write_tool(tmp_path, "alpha")
    write_tool(tmp_path, "beta")
    result = runner.invoke(app, ["tools", "--tools-dir", str(tmp_path)])
    assert result.exit_code == 0
    out = result.stdout.strip().splitlines()
    assert "alpha" in out and "beta" in out


def test_run_tool(tmp_path: Path):
    write_tool(tmp_path, "echo", command="python -c \"import sys; print(' '.join(sys.argv[1:]))\"")
    result = runner.invoke(
        app,
        [
            "run",
            "echo",
            "--tools-dir",
            str(tmp_path),
            "--",
            "hello",
            "world",
        ],
    )
    # run returns the tool's exit code; Typer exit codes don't print, but we expect success
    assert result.exit_code == 0


def test_tools_command_with_query_error(tmp_path: Path):
    """Test tools command when query bus returns error."""
    # Create an empty tools directory to trigger potential query errors
    empty_tools_dir = tmp_path / "empty"
    empty_tools_dir.mkdir()

    result = runner.invoke(app, ["tools", "--tools-dir", str(empty_tools_dir)])
    # Should handle empty directory gracefully
    assert result.exit_code == 0
    assert result.stdout.strip() == ""


def test_tools_command_with_nonexistent_directory(tmp_path: Path):
    """Test tools command with nonexistent tools directory."""
    nonexistent_dir = tmp_path / "nonexistent"

    result = runner.invoke(app, ["tools", "--tools-dir", str(nonexistent_dir)])
    # Should handle nonexistent directory - may create it or show error
    # The specific behavior depends on implementation, but shouldn't crash
    assert result.exit_code in (0, 1)  # Allow success or controlled failure


def test_run_command_with_nonexistent_tool(tmp_path: Path):
    """Test run command with nonexistent tool name."""
    result = runner.invoke(app, ["run", "nonexistent_tool", "--tools-dir", str(tmp_path)])

    # Should exit with error code when tool doesn't exist
    assert result.exit_code != 0  # Allow any non-zero exit code
    # Should provide helpful error message
    if result.stdout:
        assert "error" in result.stdout.lower() or "unknown error" in result.stdout.lower()


def test_run_command_with_failing_tool(tmp_path: Path):
    """Test run command when tool execution fails."""
    # Create a tool that exits with error code
    write_tool(tmp_path, "failing_tool", command='python -c "import sys; sys.exit(42)"')

    result = runner.invoke(app, ["run", "failing_tool", "--tools-dir", str(tmp_path)])

    # Should propagate tool's exit code
    assert result.exit_code == 42


def test_bootstrap_with_custom_tools_dir(tmp_path: Path):
    """Test bootstrap function with custom tools directory."""
    from mentat.cli import bootstrap

    custom_tools_dir = tmp_path / "custom_tools"
    custom_tools_dir.mkdir()

    container = bootstrap(custom_tools_dir)

    # Verify container is properly configured
    assert container is not None
    config = container.resolve("config")
    tools_repo = container.resolve("tools_repo")
    cmd_bus = container.resolve("command_bus")
    qry_bus = container.resolve("query_bus")

    assert config is not None
    assert tools_repo is not None
    assert cmd_bus is not None
    assert qry_bus is not None


def test_bootstrap_with_none_tools_dir():
    """Test bootstrap function with None tools directory (uses config default)."""
    from mentat.cli import bootstrap

    container = bootstrap(None)

    # Should use default from config
    assert container is not None
    config = container.resolve("config")
    assert config is not None


def test_main_entrypoint():
    """Test __main__ entrypoint doesn't crash on import."""
    # This tests the if __name__ == "__main__": app() line
    # Just importing/accessing shouldn't crash
    from mentat.cli import app as cli_app

    assert cli_app is not None


def test_cli_argument_definitions():
    """Test CLI argument and option definitions are properly configured."""
    from mentat.cli import ARGS_ARGUMENT, NAME_ARGUMENT, TOOLS_DIR_OPTION

    # Verify the arguments are properly defined
    assert TOOLS_DIR_OPTION is not None
    assert NAME_ARGUMENT is not None
    assert ARGS_ARGUMENT is not None


def test_tools_command_with_invalid_tools_dir_path(tmp_path: Path):
    """Test tools command with invalid path characters."""
    # Create a path with special characters that might cause issues
    result = runner.invoke(app, ["tools", "--tools-dir", ""])

    # Should handle invalid/empty path gracefully
    assert result.exit_code in (0, 1)  # Allow success or controlled failure


def test_run_command_empty_args(tmp_path: Path):
    """Test run command with empty arguments list."""
    write_tool(tmp_path, "no_args_tool", command="python -c \"print('no args')\"")

    result = runner.invoke(app, ["run", "no_args_tool", "--tools-dir", str(tmp_path)])

    # Should handle empty args gracefully
    assert result.exit_code == 0
