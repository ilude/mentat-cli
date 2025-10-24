from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import typer

from mentat.providers.anthropic_provider import AnthropicProvider

from .app import (
    ListTools,
    RunCommand,
    RunTool,
    handle_list_tools,
    handle_run_command,
    handle_run_tool,
)
from .config import load_config
from .core import CommandBus, QueryBus
from .infrastructure import FsToolRepository
from .infrastructure.formatters import OutputFormatter, OutputWriter
from .ioc import Container

logger = logging.getLogger(__name__)

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

    # Configure logging for debugging (write to file to avoid interfering with TUI)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=".mentat_debug.log",
        filemode="w",
    )

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

    # Import REPL utilities
    import shlex

    from mentat.tui.status import REPLStatus

    # Initialize REPL status tracker
    repl_status = REPLStatus(default_provider="anthropic", default_model="")

    def _resolve_provider(provider_name: str = "anthropic") -> Optional[Any]:
        """Resolve a provider by name (retained for compatibility)."""
        return resolve_provider(container, provider_name)

    # Display welcome message and status bar
    typer.echo("Mentat interactive — type a prompt to send to the AI provider.")
    prov_preview = _resolve_provider("anthropic")
    if prov_preview is not None:
        default_model = getattr(prov_preview, "model", "<unknown>")
        repl_status.set_provider_and_model("anthropic", default_model)

    typer.echo("")
    repl_status.display()
    typer.echo("")
    typer.echo("Commands: /model (select provider/model), /list (list models), /help (help)")
    typer.echo("")

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
        if cmd.lower() in ("help", "h", "?", "/help"):
            typer.echo("Commands:")
            typer.echo("  /model       - Select AI provider and model interactively")
            typer.echo("  /list        - List available models for current provider")
            typer.echo("  /help        - Show this help message")
            typer.echo("  run <tool>   - Execute a tool")
            typer.echo("  exit, quit   - Exit the REPL")
            typer.echo("")
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

        # /model - Interactive provider/model selector
        if cmd == "/model":
            handle_command_model(container, repl_status)
            continue

        if cmd == "/list":
            handle_command_list(container, repl_status.provider)
            continue

        # Default: send to provider
        handle_default_send(container, repl_status.provider, cmd)
        continue


def resolve_provider(container: "Container", provider_name: str) -> Optional[Any]:
    """Resolve a provider by name from the IoC container."""
    key = f"provider.{provider_name}"
    try:
        return container.resolve(key)
    except Exception:
        return None


def handle_command_model(container: "Container", repl_status: Any) -> None:
    """Show the interactive provider/model selector and update status."""
    from mentat.tui.model_selector import show_model_selector

    logger.debug("User requested /model command")
    providers = ["anthropic", "openai"]
    logger.debug("Available providers: %s", providers)

    def get_models_for_provider(provider_name: str) -> list[str]:
        logger.debug("get_models_for_provider called for: %s", provider_name)
        prov = resolve_provider(container, provider_name)
        if prov is None:
            logger.warning("Could not resolve provider: %s", provider_name)
            return []
        if hasattr(prov, "list_models") and callable(prov.list_models):
            try:
                logger.debug("Calling list_models() on %s provider", provider_name)
                models = prov.list_models()
                if isinstance(models, list) and models:
                    logger.debug("Provider %s returned %d models", provider_name, len(models))
                    return [str(m) for m in models]
            except Exception as e:  # pragma: no cover - provider SDK issues
                logger.error(
                    "Error calling list_models() on %s: %s", provider_name, e, exc_info=True
                )
        model = getattr(prov, "model", None)
        logger.debug("Falling back to model attribute for %s: %s", provider_name, model)
        return [str(model)] if model else []

    def on_model_selected(provider_name: str, model_name: str) -> None:
        logger.info("Model selected: provider=%s, model=%s", provider_name, model_name)
        repl_status.set_provider_and_model(provider_name, model_name)

    logger.debug("Showing model selector")
    show_model_selector(providers, get_models_for_provider, on_model_selected)
    logger.debug("Model selector exited")

    # After selector exits, display the new selection
    typer.echo("")
    typer.echo(f"✓ Selected: Provider={repl_status.provider} Model={repl_status.model}")
    repl_status.display()
    typer.echo("")


def handle_command_list(container: "Container", provider_name: str) -> None:
    """List available models for the current provider."""
    prov = resolve_provider(container, provider_name)
    if prov is None:
        typer.echo(f"Provider '{provider_name}' not configured")
        return
    if not hasattr(prov, "list_models"):
        typer.echo("Provider does not support listing models")
        return
    try:
        models = prov.list_models()
        if not models:
            typer.echo("No models discovered")
            return
        typer.echo("Available models:")
        for model in models:
            typer.echo(f"  - {model}")
    except Exception as e:  # pragma: no cover - provider SDK errors
        typer.echo(f"Error listing models: {e}")


def handle_default_send(container: "Container", provider_name: str, cmd: str) -> None:
    """Send a prompt to the current provider and print the response."""
    import asyncio

    from mentat.providers.interfaces import Message, MessageRole

    prov = resolve_provider(container, provider_name)
    if prov is None:
        typer.echo(f"Provider '{provider_name}' not configured")
        return
    try:
        resp = asyncio.run(prov.complete([Message(role=MessageRole.USER, content=cmd)]))
        typer.echo(resp.content)
    except Exception as exc:  # pragma: no cover - runtime/provider errors
        typer.echo(f"Provider error: {exc}")


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
            # Load from project root (.env file should be there)
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

    # Register OpenAI provider factory
    openai_cfg = None
    try:
        openai_cfg = cfg.providers.openai
    except Exception:
        openai_cfg = None

    def _make_openai() -> Any:
        from mentat.providers.openai import OpenAIProvider

        cfg_dict = {}
        if openai_cfg is not None:
            cfg_dict = {k: v for k, v in openai_cfg.dict().items() if v is not None}
        return OpenAIProvider(config=cfg_dict)

    container.register_factory("provider.openai", _make_openai)

    # Note: RunCommand handler is NOT registered here because it depends on
    # which provider the user selects. It's registered dynamically in the prompt command.

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


@app.command()
def prompt(
    text: str = typer.Argument(..., help="Development task prompt"),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format (text, json, markdown)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (if not specified, writes to stdout)",
    ),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-p",
        help="AI provider to use (e.g. 'anthropic')",
    ),
    tools_dir: Optional[Path] = TOOLS_DIR_OPTION,
) -> None:
    """Execute a single AI-assisted development task non-interactively.

    This is the core non-interactive command (User Story 1). It takes a prompt,
    sends it to the selected AI provider, formats the response, and optionally
    saves it to a file.

    Examples:
        mentat prompt "create a Python function to parse JSON"
        mentat prompt "analyze this code for bugs" -f json -o analysis.json
        mentat prompt "write tests" --provider anthropic -f markdown
    """
    # Normalize inputs when called programmatically
    format_type = format if isinstance(format, str) else "text"
    output_file = output if isinstance(output, str) else None
    provider_name = provider if isinstance(provider, str) else "anthropic"

    # Validate format
    valid_formats = ("text", "json", "markdown")
    if format_type not in valid_formats:
        typer.echo(f"Invalid format '{format_type}'. Must be one of: {', '.join(valid_formats)}")
        raise typer.Exit(code=2)

    try:
        container = bootstrap(tools_dir)
        bus: CommandBus = container.resolve("command_bus")

        # Resolve the selected provider
        provider_key = f"provider.{provider_name}"
        try:
            selected_provider = container.resolve(provider_key)
        except KeyError:
            typer.echo(f"Provider not found: {provider_name}", err=True)
            raise typer.Exit(code=2) from None

        # Register the RunCommand handler with the selected provider
        handler = handle_run_command(selected_provider)
        bus.register(RunCommand, handler)

        # Dispatch the RunCommand through the command bus
        cmd = RunCommand(prompt=text, format=format_type, output_file=output_file)
        result = bus.dispatch(cmd)

        if not result.ok or result.value is None:
            typer.echo(f"Error: {result.error or 'Unknown error'}", err=True)
            raise typer.Exit(code=1)

        # Format the response
        response = result.value
        formatted_output = OutputFormatter.format(response, format_type)

        # Write output
        OutputWriter.write(formatted_output, output_file)

        raise typer.Exit(code=0)

    except typer.Exit:
        raise
    except KeyError as exc:
        typer.echo(f"Provider not found: {provider_name}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
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
