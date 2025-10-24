from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer

from mentat.providers.anthropic_provider import AnthropicProvider

from .app import ListTools, RunTool, handle_list_tools, handle_run_tool
from .config import load_config
from .core import CommandBus, QueryBus
from .infrastructure import FsToolRepository
from .ioc import Container

app = typer.Typer(add_completion=False, help="Mentat CLI — an agent-driven tool orchestrator")


@app.callback(invoke_without_command=True)
def _maybe_repl(ctx: typer.Context) -> None:
    """If no subcommand is provided, start an interactive REPL session.

    This lets users run free-text prompts that are routed to the default
    provider (anthropic) or run local tools with `run <tool> [args...]`.
    """
    # If Typer has invoked a subcommand, do nothing here
    if ctx.invoked_subcommand is not None:
        return

    # Auto-load .env if python-dotenv is available to pick up local secrets
    try:  # pragma: no cover - optional developer convenience
        import importlib

        _mod = importlib.import_module("dotenv")
        _fn = getattr(_mod, "load_dotenv", None)
        if callable(_fn):
            _fn()
    except Exception:
        pass

    # Start REPL
    container = bootstrap()
    typer.echo("Mentat interactive — type a prompt to send to the default provider (Anthropic).")

    import asyncio
    import shlex

    from mentat.providers.interfaces import Message, MessageRole

    def _resolve_provider() -> Optional[Any]:
        for key in ("provider", "provider.anthropic"):
            try:
                return container.resolve(key)
            except Exception:
                continue
        return None

    prov_preview = _resolve_provider()
    if prov_preview is None:
        typer.echo("No provider configured (resolve 'provider' or 'provider.anthropic')")
    else:
        model_name = getattr(prov_preview, "model", "<unknown>")
        typer.echo(f"Active provider: {prov_preview.__class__.__name__} (model: {model_name})")

    while True:
        try:
            line = input("mentat> ")
        except (EOFError, KeyboardInterrupt):
            typer.echo("")
            break
        if not line:
            continue
        cmd = line.strip()
        if cmd.lower() in ("exit", "quit", ":q"):
            break
        if cmd.lower() in ("help", "h", "?"):
            typer.echo("Typing any other text will send it as a prompt to the default provider.")
            continue

        # run <tool> ...
        if cmd.startswith("run "):
            parts = shlex.split(cmd)
            if len(parts) >= 2:
                name = parts[1]
                args = parts[2:]
                bus = container.resolve("command_bus")
                from mentat.app.commands import RunTool as RunToolDTO

                res = bus.dispatch(RunToolDTO(name=name, args=args))
                if res.ok and res.value is not None:
                    result = res.value
                    if result.stdout:
                        typer.echo(result.stdout.rstrip("\n"))
                    if result.stderr:
                        typer.echo(result.stderr.rstrip("\n"), err=True)
                    typer.echo(f"[exit {result.exit_code}]")
                else:
                    typer.echo(res.error or "Unknown error")
            else:
                typer.echo("Usage: run <tool> [args...]")
            continue

        if cmd == "/model":
            prov = _resolve_provider()
            if prov is None:
                typer.echo("No provider configured (resolve 'provider' or 'provider.anthropic')")
                continue
            typer.echo(getattr(prov, "model", "<unknown>"))
            continue

        if cmd == "/list":
            prov = _resolve_provider()
            if prov is None:
                typer.echo("No provider configured (resolve 'provider' or 'provider.anthropic')")
                continue
            if not hasattr(prov, "list_models"):
                typer.echo("Provider does not support listing models")
                continue
            models = prov.list_models()
            if not models:
                typer.echo("No models discovered")
            else:
                for mid in models:
                    typer.echo(mid)
            continue

        # Default: send to provider
        prov = _resolve_provider()
        if prov is None:
            typer.echo("No provider configured (resolve 'provider' or 'provider.anthropic')")
            continue

        try:
            resp = asyncio.run(prov.complete([Message(role=MessageRole.USER, content=cmd)]))
            typer.echo(resp.content)
        except Exception as exc:  # pragma: no cover - runtime/provider errors
            typer.echo(f"Provider error: {exc}")
            continue


# Define Typer defaults at module scope to avoid calling in function defaults (ruff B008)
TOOLS_DIR_OPTION = typer.Option(None, help="Path to tools directory")
NAME_ARGUMENT = typer.Argument(..., help="Tool name")
ARGS_ARGUMENT = typer.Argument([], help="Arguments passed to the tool")


def bootstrap(tools_dir: Optional[Path] = None) -> Container:
    # Auto-load .env if python-dotenv is available so non-interactive commands
    # (like `mentat ask`) also pick up local environment variables from a .env file.
    try:  # pragma: no cover - optional developer convenience
        import importlib

        _mod = importlib.import_module("dotenv")
        _fn = getattr(_mod, "load_dotenv", None)
        if callable(_fn):
            _fn()
    except Exception:
        pass
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
    # Register provider factories. Consumers can resolve "provider.anthropic" to get
    # an AnthropicProvider instance. The provider reads API key from env when config
    # does not provide it.
    # Wire anthropic provider with config if present
    anth_cfg = None
    try:
        anth_cfg = cfg.providers.anthropic
    except Exception:
        anth_cfg = None

    def _make_anthropic() -> AnthropicProvider:
        cfg_dict = {}
        if anth_cfg is not None:
            cfg_dict = {k: v for k, v in anth_cfg.dict().items() if v is not None}
        return AnthropicProvider(config=cfg_dict)

    container.register_factory("provider.anthropic", _make_anthropic)
    return container


@app.command()
def tools(tools_dir: Optional[Path] = TOOLS_DIR_OPTION) -> None:
    # Typer passes OptionInfo when called as library function; normalize to None
    if not (tools_dir is None or isinstance(tools_dir, (str, Path))):
        tools_dir = None
    container = bootstrap(tools_dir)
    bus: QueryBus = container.resolve("query_bus")
    res = bus.ask(ListTools())
    if not res.ok:
        typer.echo(res.error or "Unknown error")
        raise typer.Exit(code=1)
    tool_infos = res.value or []
    for info in sorted(tool_infos, key=lambda t: t.name.lower()):
        typer.echo(info.name)


@app.command()
def run(
    name: str = NAME_ARGUMENT,
    args: list[str] = ARGS_ARGUMENT,
    tools_dir: Optional[Path] = TOOLS_DIR_OPTION,
) -> None:
    container = bootstrap(tools_dir)
    bus: CommandBus = container.resolve("command_bus")
    res = bus.dispatch(RunTool(name=name, args=list(args)))
    if not res.ok or res.value is None:
        typer.echo(res.error or "Unknown error")
        raise typer.Exit(code=1)

    result = res.value
    if result.stdout:
        typer.echo(result.stdout.rstrip("\n"))
    if result.stderr:
        typer.echo(result.stderr.rstrip("\n"), err=True)

    raise typer.Exit(code=int(result.exit_code))


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Prompt text to send to the AI provider"),
    provider: str = typer.Option("anthropic", help="Provider to use (e.g. 'anthropic')"),
    tools_dir: Optional[Path] = TOOLS_DIR_OPTION,
) -> None:
    """Send a single prompt to the selected provider and print the response."""
    container = bootstrap(tools_dir)
    # Derive provider name (handle OptionInfo when called programmatically)
    provider_name = provider if isinstance(provider, str) else "anthropic"
    key = f"provider.{provider_name}"
    try:
        prov = container.resolve(key)
    except KeyError:
        typer.echo(f"Provider not found: {provider}")
        raise typer.Exit(code=2) from None

    # Import interfaces locally to avoid top-level asyncio interactions
    import asyncio

    from mentat.providers.interfaces import Message, MessageRole

    try:
        resp = asyncio.run(prov.complete([Message(role=MessageRole.USER, content=prompt)]))
        typer.echo(resp.content)
    except Exception as exc:  # pragma: no cover - runtime/provider errors
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc


@app.command(name="debug-provider")
def debug_provider(
    provider: str = typer.Option("anthropic", help="Provider to debug (e.g. 'anthropic')"),
    tools_dir: Optional[Path] = TOOLS_DIR_OPTION,
) -> None:
    """Show diagnostics for a configured provider without printing secrets.

    Prints whether an API key was found (masked), whether a client object
    exists, the client type, available top-level attributes, signatures for
    likely methods (completions/responses/messages), and an attempt to list
    available models if the SDK supports it.
    """
    import inspect
    import os

    # Normalize tools_dir when invoked programmatically (Typer passes OptionInfo)
    if not (tools_dir is None or isinstance(tools_dir, (str, Path))):
        tools_dir = None

    container = bootstrap(tools_dir)
    # Determine provider name (handle OptionInfo when called programmatically)
    provider_name = provider if isinstance(provider, str) else "anthropic"
    key = f"provider.{provider_name}"
    try:
        prov = container.resolve(key)
    except KeyError:
        typer.echo(f"Provider not found: {provider}")
        raise typer.Exit(code=2) from None

    # Masked API key preview
    raw = os.environ.get("MENTAT_ANTHROPIC_API_KEY")
    if not raw:
        typer.echo("API key: not set in environment")
    else:
        try:
            length = len(raw)
            preview = f"{raw[:6]}...{raw[-4:]} (len={length})"
        except Exception:
            preview = "<present>"
        typer.echo(f"API key: {preview}")

    client = getattr(prov, "client", None)
    typer.echo(f"Provider instance: {prov.__class__.__name__}")
    typer.echo(f"Client present: {client is not None}")
    if client is None:
        raise typer.Exit(code=0)

    # Print client type and a small attribute summary
    typer.echo(f"Client type: {type(client)}")
    attrs = [a for a in dir(client) if not a.startswith("_")]
    typer.echo("Client attrs: " + ", ".join(sorted(attrs)))

    # Inspect likely methods
    candidates = [
        (
            "client.completions.create",
            lambda: getattr(getattr(client, "completions", None), "create", None),
        ),
        (
            "client.responses.create",
            lambda: getattr(getattr(client, "responses", None), "create", None),
        ),
        (
            "client.messages.create",
            lambda: getattr(getattr(client, "messages", None), "create", None),
        ),
        (
            "client.chat.completions.create",
            lambda: getattr(
                getattr(getattr(client, "chat", None), "completions", None), "create", None
            ),
        ),
        (
            "client.chat.messages.create",
            lambda: getattr(
                getattr(getattr(client, "chat", None), "messages", None), "create", None
            ),
        ),
    ]

    for label, getter in candidates:
        fn = getter()
        typer.echo(f"\n{label}: exists? {fn is not None}")
        if fn is None:
            continue
        try:
            sig = inspect.signature(fn)
            typer.echo(f"  signature: {sig}")
        except Exception as e:
            typer.echo(f"  signature: <unable to inspect: {e}>")
        doc = (fn.__doc__ or "").strip().splitlines()[:3]
        if doc:
            typer.echo("  doc: ")
            for line in doc:
                typer.echo("    " + line)

    # Try to list models if available
    try:
        if hasattr(client, "models") and hasattr(client.models, "list"):
            typer.echo("\nAttempting models.list()...")
            try:
                models = client.models.list()
                ids = []
                try:
                    for m in models:
                        mid = getattr(m, "id", None) or (
                            m.get("id") if isinstance(m, dict) else None
                        )
                        if mid:
                            ids.append(mid)
                except TypeError:
                    if isinstance(models, dict):
                        data = models.get("data") or models.get("models")
                        if isinstance(data, list):
                            for m in data:
                                mid = getattr(m, "id", None) or (
                                    m.get("id") if isinstance(m, dict) else None
                                )
                                if mid:
                                    ids.append(mid)
                typer.echo(f"Discovered models: {ids}")
            except Exception as e:
                typer.echo(f"models.list() failed: {e}")
        else:
            typer.echo("models.list() not available on client")
    except Exception as e:
        typer.echo(f"Model discovery attempt failed: {e}")

    # Try provider-level connectivity check (async)
    import asyncio

    try:
        ok = asyncio.run(prov.test_connection())
        typer.echo(f"provider.test_connection(): {ok}")
    except Exception as e:
        typer.echo(f"provider.test_connection() failed: {e}")


if __name__ == "__main__":
    app()
