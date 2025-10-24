"""Textual-based REPL application for Mentat CLI."""

from __future__ import annotations

import asyncio
import logging
import shlex
from typing import Any, Optional

from rich.markdown import Markdown
from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, RichLog, Static, TabbedContent, TabPane

from mentat.app.commands import RunTool
from mentat.core import CommandBus
from mentat.ioc.container import Container as IoCContainer
from mentat.providers.interfaces import Message, MessageRole
from mentat.tui.status import StatusBar

logger = logging.getLogger(__name__)


class HelpModal(ModalScreen[None]):
    """Modal displaying available commands and shortcuts."""

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    #help-panel {
        width: 60;
        max-height: 20;
        border: solid $accent;
        background: $panel;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("ctrl+c", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        help_md = Markdown(
            """
            # Mentat REPL Help

            **Quick commands**
            - `/model` — Select provider and model
            - `/list` — List models for the current provider
            - `/help` — Show this help panel
            - `run <tool> [args...]` — Execute a configured tool

            **Shortcuts**
            - `Ctrl+L` — Focus the input field
            - `/` — Jump to the input with `/` prefilled
            - `Ctrl+D` — Exit the REPL
            - `F1` — Open help
            """
        )
        yield Static(Panel(help_md, title="Mentat Help"), id="help-panel")


class MentatReplApp(App[None]):
    """Textual application hosting the Mentat interactive REPL."""

    CSS = """
    MentatReplApp {
        layout: vertical;
    }

    /* Main content area fills available space */
    #content {
        layout: vertical;
        height: 1fr;
    }

    /* Tabs container */
    #tabs {
        height: 100%;
    }

    TabPane {
        padding: 1 2;
    }

    #chat-pane, #history-pane, #settings-pane {
        layout: vertical;
    }

    /* Scrollable areas */
    #chat-log, #history-log {
        height: 1fr;
        overflow-y: auto;
    }

    /* Status bar and prompt section */
    #chrome {
        layout: vertical;
        height: auto;  /* Let it size based on contents */
        border-top: solid $surface;
        background: $surface;
    }

    #status-bar {
        padding: 0 1;
        background: $surface;
        height: 1;
    }

    #prompt-container {
        padding: 1 2;
        border-top: solid $accent;
        background: $panel;
        height: auto;  /* Size based on input */
    }

    #prompt-container Input {
        width: 100%;
    }

    /* Footer positioning */
    Footer {
        border-top: solid $surface;
    }
    """

    BINDINGS = [
        ("ctrl+d", "quit", "Exit"),
        ("ctrl+l", "focus_input", "Focus Input"),
        ("/", "slash_focus", "Slash Command"),
        ("f1", "show_help", "Help"),
    ]

    def __init__(
        self,
        container: IoCContainer,
        default_provider: str = "anthropic",
        default_model: str = "",
        tools_dir: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._container = container
        self._command_bus: CommandBus = container.resolve("command_bus")
        self._default_provider = default_provider
        self.current_provider = default_provider
        self.current_model = default_model
        self._tools_dir = tools_dir
        self._status_bar = StatusBar(default_provider, default_model or "", "Ready")
        self._chat_log = RichLog(id="chat-log", highlight=False, markup=True, wrap=True)
        self._history_log = RichLog(id="history-log", highlight=False, markup=True, wrap=True)
        self._settings_panel = Static(id="settings-panel")
        self._prompt_input = Input(
            placeholder="Ask the model, run /command, or 'run <tool>'",
        )
        self._history: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Container(id="content"):
            with TabbedContent(id="tabs"):
                with TabPane("Chat", id="chat-pane"):
                    yield self._chat_log
                with TabPane("History", id="history-pane"):
                    yield self._history_log
                with TabPane("Settings", id="settings-pane"):
                    yield self._settings_panel
        with Container(id="chrome"):
            yield self._status_bar
            with Container(id="prompt-container"):
                yield self._prompt_input
        yield Footer()

    def on_mount(self) -> None:
        self._prompt_input.focus()
        self._refresh_settings_panel()
        self._status_bar.set_provider_and_model(self.current_provider, self.current_model)
        self._status_bar.set_connection_status("Ready")

    def action_focus_input(self) -> None:
        self._prompt_input.focus()

    def action_slash_focus(self) -> None:
        self._prompt_input.focus()
        if not self._prompt_input.value.startswith("/"):
            self._prompt_input.value = "/"
        self._prompt_input.cursor_position = len(self._prompt_input.value)

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if text:
            self._append_history(f"$ {text}")
            self._dispatch_command(text)

    def _dispatch_command(self, text: str) -> None:
        lower = text.lower()
        if lower in ("exit", "quit", ":q"):
            self.exit()
            return
        if text == "?":
            self._show_quick_commands()
            return
        if text.startswith("/"):
            self._handle_slash_command(text)
            return
        if lower.startswith("run "):
            self._handle_run_tool(text)
            return
        self._handle_prompt(text)

    def _handle_slash_command(self, text: str) -> None:
        if text == "/model":
            self._handle_model_command()
        elif text == "/list":
            self._handle_list_command()
        elif text == "/help":
            self.push_screen(HelpModal())
        else:
            self._log_system(f"[yellow]Unknown command:[/] {text}")

    def _handle_model_command(self) -> None:
        from mentat.tui.model_selector import ModelSelectorScreen

        providers = ["anthropic", "openai"]

        def get_models(provider_name: str) -> list[str]:
            provider = self._resolve_provider(provider_name)
            if provider is None:
                return []
            if hasattr(provider, "list_models") and callable(provider.list_models):
                try:
                    models = provider.list_models()
                    if isinstance(models, list):
                        return [str(model) for model in models if model]
                except Exception as exc:  # pragma: no cover - provider SDK errors
                    logger.error("list_models failed for %s: %s", provider_name, exc)
                    return []
            model_attr = getattr(provider, "model", None)
            return [str(model_attr)] if model_attr else []

        def on_select(provider_name: str, model_name: str) -> None:
            self.current_provider = provider_name
            self.current_model = model_name
            self._status_bar.set_provider_and_model(provider_name, model_name)
            self._status_bar.set_connection_status("Ready")
            self._refresh_settings_panel()
            msg = (
                f"[green]Provider set to[/] [bold]{provider_name}[/] • "
                f"[green]Model:[/] {model_name or '<not set>'}"
            )
            self._log_system(msg)

        screen = ModelSelectorScreen(
            providers,
            get_models,
            on_select,
            dismiss_mode="pop",
        )
        self.push_screen(screen)

    def _handle_list_command(self) -> None:
        provider_name = self.current_provider
        self._status_bar.set_connection_status("Loading models...")

        def worker() -> None:
            provider = self._resolve_provider(provider_name)
            if provider is None:
                self.call_from_thread(
                    lambda: self._handle_list_failure(
                        f"[red]Provider '{provider_name}' not configured.[/]"
                    )
                )
                return
            if not hasattr(provider, "list_models") or not callable(provider.list_models):
                self.call_from_thread(
                    lambda: self._handle_list_failure(
                        "[yellow]Provider does not support list_models().[/]"
                    )
                )
                return
            try:
                models = provider.list_models()
            except Exception as exc:  # pragma: no cover - provider SDK errors
                self.call_from_thread(
                    lambda e=exc: self._handle_list_failure(f"[red]Error listing models:[/] {e}")
                )
                return
            self.call_from_thread(lambda: self._display_models(provider_name, models))

        self.run_worker(worker, thread=True, name="list-models")

    def _display_models(self, provider_name: str, models: Any) -> None:
        self._status_bar.set_connection_status("Ready")
        if not models:
            self._log_system("[yellow]No models discovered.[/]")
            return
        if not isinstance(models, list):
            self._log_system(f"[yellow]Unexpected model payload:[/] {models}")
            return
        self._log_system(f"[green]Models for {provider_name}:[/]")
        for model in models:
            self._chat_log.write(f"  • {model}")

    def _handle_list_failure(self, message: str) -> None:
        self._status_bar.set_connection_status("Ready")
        self._log_system(message)

    def _handle_run_tool(self, text: str) -> None:
        try:
            parts = shlex.split(text)
        except ValueError as exc:
            self._log_system(f"[red]Unable to parse command:[/] {exc}")
            return
        if len(parts) < 2:
            self._log_system("[yellow]Usage: run <tool> [args...][/]")
            return
        name = parts[1]
        args = parts[2:]
        self._status_bar.set_connection_status(f"Running tool '{name}'")
        self._chat_log.write(f"[bold cyan]▶ Tool:[/] {name} {' '.join(args)}")

        def worker() -> None:
            result = self._command_bus.dispatch(RunTool(name=name, args=args))
            self.call_from_thread(lambda: self._handle_tool_result(name, result))

        self.run_worker(worker, thread=True, name=f"run-tool-{name}")

    def _handle_tool_result(self, name: str, result: Any) -> None:
        self._status_bar.set_connection_status("Ready")
        if not result.ok or result.value is None:
            error = result.error or "Unknown error"
            self._log_system(f"[red]Tool '{name}' failed:[/] {error}")
            return
        payload = result.value
        stdout = getattr(payload, "stdout", "")
        stderr = getattr(payload, "stderr", "")
        exit_code = getattr(payload, "exit_code", 0)
        if stdout:
            self._chat_log.write(stdout.rstrip("\n"))
        if stderr:
            self._chat_log.write(f"[red]{stderr.rstrip('\n')}[/]")
        self._chat_log.write(f"[dim]exit {exit_code}[/]")

    def _handle_prompt(self, prompt: str) -> None:
        self._focus_chat_tab()
        self._chat_log.write(f"[bold magenta]You:[/] {prompt}")
        self._status_bar.set_connection_status("Thinking…")

        async def run_completion() -> None:
            provider = self._resolve_provider(self.current_provider)
            if provider is None:
                self.call_from_thread(
                    lambda: self._log_system(
                        f"[red]Provider '{self.current_provider}' not configured.[/]"
                    )
                )
                self.call_from_thread(lambda: self._status_bar.set_connection_status("Ready"))
                return
            try:
                response = await provider.complete([Message(role=MessageRole.USER, content=prompt)])
            except Exception as exc:  # pragma: no cover - provider SDK errors
                logger.error("Provider error: %s", exc, exc_info=True)
                self.call_from_thread(
                    lambda e=exc: self._log_system(f"[red]Provider error:[/] {e}")
                )
                self.call_from_thread(lambda: self._status_bar.set_connection_status("Ready"))
                return

            content = getattr(response, "content", "")
            chunks = self._chunk_response(content)
            for chunk in chunks:
                self.call_from_thread(lambda c=chunk: self._chat_log.write(c))
            self.call_from_thread(lambda: self._status_bar.set_connection_status("Ready"))

        self.run_worker(lambda: asyncio.run(run_completion()), thread=True, name="prompt")

    def _chunk_response(self, content: Any) -> list[str]:
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = "\n".join(str(part) for part in content)
        else:
            text = str(content)
        if not text:
            return ["<empty response>"]
        return [segment.strip() for segment in text.split("\n\n") if segment.strip()]

    def _log_system(self, message: str) -> None:
        self._focus_chat_tab()
        self._chat_log.write(message)

    def _append_history(self, message: str) -> None:
        self._history.append(message)
        self._history_log.write(message)

    def _resolve_provider(self, provider_name: str) -> Optional[Any]:
        key = f"provider.{provider_name}"
        try:
            return self._container.resolve(key)
        except Exception:  # pragma: no cover - container lookup failure
            return None

    def _focus_chat_tab(self) -> None:
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "chat-pane"
        except Exception:  # pragma: no cover - tab not yet mounted
            pass

    def _refresh_settings_panel(self) -> None:
        config_lines = [
            f"* **Provider:** {self.current_provider}",
            f"* **Model:** {self.current_model or '<not set>'}",
        ]
        if self._tools_dir:
            config_lines.append(f"* **Tools dir:** `{self._tools_dir}`")
        info = "\n".join(config_lines)
        self._settings_panel.update(Panel(Markdown(info), title="Session"))

    def _show_quick_commands(self) -> None:
        commands = [
            "Type /model to choose provider and model",
            "Type /list to list models for the active provider",
            "Type /help for the full help modal",
            "Use run <tool> [args...] to execute a tool",
            "Enter exit or quit to leave the REPL",
        ]
        self._log_system("[bold]Available commands:[/]")
        for line in commands:
            self._chat_log.write(f"  • {line}")
