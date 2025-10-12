from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .core import CommandBus, QueryBus
from .ioc import Container
from .infrastructure import FsToolRepository
from .app import RunTool, ListTools, handle_run_tool, handle_list_tools


app = typer.Typer(add_completion=False, help="Mentat CLI — an agent-driven tool orchestrator")


def bootstrap(tools_dir: Optional[Path] = None) -> Container:
    cfg = load_config()
    if tools_dir is None:
        tools_dir = cfg.tools_dir
    # Normalize to absolute path
    tools_dir = Path(tools_dir).expanduser().resolve()

    container = Container()
    repo = FsToolRepository(tools_dir)
    cmd_bus = CommandBus()
    qry_bus = QueryBus()

    # register handlers
    cmd_bus.register(RunTool, handle_run_tool(repo))
    qry_bus.register(ListTools, handle_list_tools(repo))

    container.register_singleton("config", cfg)
    container.register_singleton("tools_repo", repo)
    container.register_singleton("command_bus", cmd_bus)
    container.register_singleton("query_bus", qry_bus)
    return container


@app.command()
def tools(tools_dir: Optional[Path] = typer.Option(None, help="Path to tools directory")) -> None:
    container = bootstrap(tools_dir)
    bus: QueryBus = container.resolve("query_bus")
    res = bus.ask(ListTools())
    if not res.ok:
        typer.echo(res.error or "Unknown error")
        raise typer.Exit(code=1)
    for name in sorted(res.value or []):
        typer.echo(name)


@app.command()
def run(
    name: str = typer.Argument(..., help="Tool name"),
    args: list[str] = typer.Argument([], help="Arguments passed to the tool"),
    tools_dir: Optional[Path] = typer.Option(None, help="Path to tools directory"),
) -> None:
    container = bootstrap(tools_dir)
    bus: CommandBus = container.resolve("command_bus")
    res = bus.dispatch(RunTool(name=name, args=list(args)))
    if not res.ok:
        typer.echo(res.error or "Unknown error")
        raise typer.Exit(code=1)
    raise typer.Exit(code=int(res.value or 0))


if __name__ == "__main__":
    app()
