"""Textual status bar widget for the Mentat REPL."""

from __future__ import annotations

from rich.text import Text
from textual.reactive import Reactive, reactive
from textual.widgets import Static


class StatusBar(Static):
    """Displays provider, model, and connection status in the REPL footer."""

    current_provider: Reactive[str] = reactive("anthropic")
    current_model: Reactive[str] = reactive("")
    connection_status: Reactive[str] = reactive("Ready")

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "",
        connection_status: str = "Ready",
    ) -> None:
        super().__init__(id="status-bar")
        self.current_provider = provider
        self.current_model = model
        self.connection_status = connection_status

    def set_provider(self, provider: str) -> None:
        """Update the active provider name."""
        self.current_provider = provider

    def set_model(self, model: str) -> None:
        """Update the active model name."""
        self.current_model = model

    def set_provider_and_model(self, provider: str, model: str) -> None:
        """Update both provider and model."""
        self.current_provider = provider
        self.current_model = model

    def set_connection_status(self, status: str) -> None:
        """Update the connection status indicator."""
        self.connection_status = status

    def render(self) -> Text:
        """Render the status line as Rich text."""
        provider = self.current_provider or "<unknown>"
        model = self.current_model or "<not set>"
        status = self.connection_status or "Idle"
        return Text.assemble(
            (" Provider: ", "bold"),
            (provider, "bold yellow" if provider == "anthropic" else "bold cyan"),
            (" • Model: ", "bold"),
            (model, ""),
            (" • Status: ", "bold"),
            (status, "green" if status.lower() == "ready" else "yellow"),
        )
