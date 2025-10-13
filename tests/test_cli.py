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
