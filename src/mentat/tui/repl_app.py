"""Textual-based REPL application for Mentat CLI."""

from __future__ import annotations

import asyncio
import logging
import shlex
import sys
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
            - `F8` — Toggle native mouse selection (drag to select like a normal terminal)

            Tip: In the VS Code integrated terminal, hold Shift while dragging to force text
            selection even when a full-screen app is active. Use F8 to make selection easier
            when needed.
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
        ("ctrl+d", "safe_quit", "Exit"),
        ("ctrl+l", "focus_input", "Focus Input"),
        ("/", "slash_focus", "Slash Command"),
        ("f1", "show_help", "Help"),
        ("f8", "toggle_mouse_selection", "Mouse Select"),
        ("f9", "toggle_copy_mode", "Copy Mode"),
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
        # When True, Textual mouse reporting is disabled so the terminal can
        # handle native drag-to-select. Toggle with F8.
        self._native_selection: bool = False
        # When True, "copy mode" is enabled. Intended for future enhancements where
        # drag-selecting copies a range to the clipboard. Currently used only for
        # status messaging.
        self._copy_mode: bool = False

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
        # Ensure mouse reporting is enabled initially
        self._set_mouse_reporting(True)

    def action_safe_quit(self) -> None:
        """Gracefully exit the app without tearing down the host terminal.

        - Re-enable terminal mouse reporting (in case native selection was toggled).
        - Schedule exit on the next tick to avoid exiting mid-event handler.
        """
        try:
            # Restore default mouse reporting before leaving
            self._set_mouse_reporting(True)
        except Exception:
            pass
        # Defer exit slightly to allow the current handler to unwind cleanly
        self.set_timer(0.01, lambda: self.exit(return_code=0))

    def action_focus_input(self) -> None:
        self._prompt_input.focus()

    def action_slash_focus(self) -> None:
        self._prompt_input.focus()
        if not self._prompt_input.value.startswith("/"):
            self._prompt_input.value = "/"
        self._prompt_input.cursor_position = len(self._prompt_input.value)

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_toggle_mouse_selection(self) -> None:
        """Toggle terminal-native mouse selection.

        When enabled, Textual's mouse reporting is disabled so your terminal
        can handle drag-to-select like a normal terminal. Press F8 again to
        re-enable in-app mouse handling.
        """
        self._native_selection = not self._native_selection
        self._set_mouse_reporting(not self._native_selection)
        status = "Select mode" if self._native_selection else "Ready"
        try:
            self._status_bar.set_connection_status(status)
        except Exception:
            pass
        # Give the user clear feedback in the chat log as well
        if self._native_selection:
            self._log_system("[dim]Native selection enabled — drag with the mouse to select.[/]")
            self._log_system(
                "[dim]Tip: In VS Code, hold Shift while dragging. Press F8 to return.[/]"
            )
        else:
            self._log_system("[dim]Native selection off — in-app mouse handling restored.[/]")

    @property
    def copy_mode_enabled(self) -> bool:
        """Whether copy mode is currently enabled."""
        return self._copy_mode

    def action_toggle_copy_mode(self) -> None:
        """Toggle in-app copy mode: show status and log guidance.

        Note: This is a placeholder for a future behavior where drag-selecting
        copies a line range to the clipboard. For now, it only updates the
        status bar and logs helpful messages.
        """
        self._copy_mode = not self._copy_mode
        try:
            mode = "Copy mode" if self._copy_mode else "Ready"
            self._status_bar.set_connection_status(mode)
        except Exception:
            pass
        if self._copy_mode:
            self._log_system(
                "[dim]Copy mode enabled — drag to select lines; release to copy (future).[/]"
            )
        else:
            self._log_system("[dim]Copy mode off.[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if text:
            self._append_history(f"$ {text}")
            self._dispatch_command(text)

    def _dispatch_command(self, text: str) -> None:
        lower = text.lower()
        if lower in ("exit", "quit", ":q"):
            # Use our graceful quit action to avoid abrupt termination
            self.action_safe_quit()
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
            self._write_chat(stdout.rstrip("\n"))
        if stderr:
            self._write_chat(f"[red]{stderr.rstrip('\n')}[/]")
        self._write_chat(f"[dim]exit {exit_code}[/]")

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
                self.call_from_thread(lambda c=chunk: self._write_chat(c))
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
        self._write_chat(message)

    def _append_history(self, message: str) -> None:
        self._history.append(message)
        self._history_log.write(message)

    def _set_mouse_reporting(self, enabled: bool) -> None:
        """Enable/disable terminal mouse reporting via escape sequences.

        This allows the user to select text with the mouse when disabled.
        We use SGR (1006) and button tracking (1002) toggles along with the
        basic mouse reporting (1000).
        """
        # These control sequences are standard across terminals.
        enable_seq = "\x1b[?1000h\x1b[?1002h\x1b[?1006h"
        disable_seq = "\x1b[?1000l\x1b[?1002l\x1b[?1006l"
        try:
            sys.stdout.write(enable_seq if enabled else disable_seq)
            sys.stdout.flush()
        except Exception:
            # Ignore failures silently; worst case, selection toggle won't work
            pass

    def _looks_like_markdown(self, s: str) -> bool:
        """Heuristic to decide if a string should be rendered as Markdown.

        This is intentionally conservative: we prefer to render Markdown when there
        are explicit markers (fenced code blocks, headings, lists, or multiple
        paragraphs). If the string contains Rich markup tokens (e.g. [bold]) we
        treat it as markup instead.
        """
        if not s or not isinstance(s, str):
            return False
        # If it looks like Rich markup, prefer markup mode
        if ("[" in s and "]" in s) and any(
            tok in s for tok in ("[bold", "[red", "[green", "[cyan", "[/]", "[/bold]")
        ):
            return False
        if "```" in s:
            return True
        if "\n\n" in s:
            return True
        first_lines = s.splitlines()[:4]
        for line in first_lines:
            stripped = line.lstrip()
            if not stripped:
                continue
            if stripped.startswith(("#", ">", "-", "*", "1.")):
                return True
        if "**" in s or "__" in s or ("[" in s and "](" in s):
            return True
        return False

    def _write_chat(self, message: Any) -> None:
        """Write to the chat log, rendering Markdown when appropriate.

        Accepts either strings or Rich renderables. Strings are examined with
        _looks_like_markdown to decide whether to wrap them with
        rich.markdown.Markdown before writing.
        """
        # Accept renderables directly
        if not isinstance(message, str):
            self._chat_log.write(message)
            return
        # Decide whether to render as Markdown or plain/markup text
        if self._looks_like_markdown(message):
            self._chat_log.write(Markdown(message))
        else:
            self._chat_log.write(message)

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
            self._write_chat(f"  • {line}")
