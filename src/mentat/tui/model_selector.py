"""Interactive model selector TUI using Textual.

This screen previously used a raw background thread with ``app.call_from_thread``
to marshal results back to the UI. We've switched to posting a custom Textual
Message from the worker thread instead, which is the recommended and more
robust pattern for cross-thread UI updates in Textual. This avoids any silent
failures in ``call_from_thread`` and ensures exceptions surface in the app
loop.
"""

from __future__ import annotations

import logging
import threading
import traceback
from typing import Callable, Literal, Optional

from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

logger = logging.getLogger(__name__)


class ModelSelectorScreen(Screen):
    """Interactive screen for selecting AI provider and model.

    First shows list of available providers, then shows models for selected provider.
    """

    DEFAULT_CSS = """
    ModelSelectorScreen {
        background: $surface;
        color: $text;
    }

    #title {
        dock: top;
        height: 1;
        content-align: center middle;
        background: $boost;
        color: $text;
    }

    #list_view {
        border: solid $accent;
        height: 1fr;
    }

    #instructions {
        dock: bottom;
        height: 1;
        content-align: center middle;
        background: $panel;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        providers: list[str],
        get_models: Callable[[str], list[str]],
        on_select: Callable[[str, str], None],
    ) -> None:
        """Initialize model selector.

        Args:
            providers: List of available provider names
            get_models: Callable that takes provider name and returns list of models
            on_select: Callback when provider/model is selected (provider_name, model_name)
        """
        super().__init__()
        self.providers = providers
        self.get_models = get_models
        self.on_select = on_select
        self.selected_provider: Optional[str] = None
        self._models: Optional[list[str]] = None
        # Track whether we're selecting providers or models
        self._state: Literal["providers", "models"] = "providers"
        # Track which provider we're currently fetching models for (guard late updates)
        self._pending_fetch_provider: Optional[str] = None

    # --- Small UI helpers for readability/maintainability ---
    def _show_loading(self) -> None:
        """Clear list and show a loading placeholder."""
        list_view = self.query_one("#list_view", ListView)
        list_view.clear()
        list_view.append(ListItem(Static("Loading models...")))
        list_view.focus()
        if list_view.children:
            try:
                list_view.index = 0
                logger.debug("Set loading index to 0")
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Error setting loading index: {e}")

    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        yield Static("Select Provider", id="title")
        yield ListView(
            *[ListItem(Static(p)) for p in self.providers],
            id="list_view",
        )
        yield Static("↑/↓ Navigate • Enter Select • Esc Cancel", id="instructions")

    def on_mount(self) -> None:
        """Focus the list view when screen loads."""
        list_view = self.query_one("#list_view", ListView)
        list_view.focus()
        logger.debug("ModelSelectorScreen mounted; ListView focused")

    def _show_model_list(self, models: list[str]) -> None:
        """Show model list after provider is selected."""
        try:
            logger.debug(f"_show_model_list called with {len(models)} models")

            # Update title
            title = self.query_one("#title", Static)
            title.update(f"Select Model ({self.selected_provider})")
            logger.debug("Updated title")

            # Update list view with models
            list_view = self.query_one("#list_view", ListView)
            logger.debug(f"ListView before clear: {len(list_view.children)} children")
            list_view.clear()
            logger.debug("ListView cleared")

            # Display models or error message
            if not models:
                list_view.append(ListItem(Static("<no models available>")))
                logger.debug("Added no models available message")
            else:
                for model in models:
                    list_view.append(ListItem(Static(model)))
                logger.debug("Added all models: %d", len(models))

            # store models for selection
            self._models = models if models else []
            logger.debug(f"Stored {len(self._models)} models")

            # Re-focus list view and ensure first item is selected
            list_view.focus()
            logger.debug(f"Focused ListView, has {len(list_view.children)} children")

            if list_view.children:
                # Explicitly select the first item
                try:
                    list_view.index = 0
                    logger.debug(f"Set index to 0, current index is: {list_view.index}")
                except Exception as e:
                    logger.error(f"Error setting index: {e}")

            # Change instruction text
            instructions = self.query_one("#instructions", Static)
            instructions.update("↑/↓ Navigate • Enter Select • Esc Back")
            logger.debug("Updated instructions")

            logger.debug("_show_model_list completed successfully")
        except Exception as e:
            logger.error(f"Error in _show_model_list: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    # --- Thread-safe UI handoff via Textual Message ---
    class ModelsLoaded(Message):
        """Message posted from the worker thread when models are fetched."""

        def __init__(self, models: list[str]) -> None:
            super().__init__()
            self.models = models

    def on_model_selector_screen_models_loaded(
        self, message: "ModelSelectorScreen.ModelsLoaded"
    ) -> None:
        """Handle models loaded message by updating the list view on the UI thread."""
        try:
            # Keep the debug message under line-length limits
            logger.debug(
                "on_models_loaded received %d models for provider %s",
                len(message.models),
                self.selected_provider,
            )
            self._show_model_list(message.models)
        except Exception:
            logger.error("Failed to handle ModelsLoaded message", exc_info=True)

    def action_select_item(self) -> None:
        """Handle selection of provider or model based on current state."""
        if self._state == "providers":
            # Transition to model selection
            self._transition_to_model_selection()
        elif self._state == "models":
            # Select the model and exit
            if self.selected_provider is None or not self._models:
                return

            list_view = self.query_one("#list_view", ListView)
            current_index = list_view.index

            # Check if index is valid
            if current_index is None:
                # If no index, try to use first model
                current_index = 0

            # Safely bound the index
            if current_index < 0 or current_index >= len(self._models):
                current_index = 0

            # Verify we have a valid model to select
            if current_index >= len(self._models):
                return

            selected_model = self._models[current_index]
            self.on_select(self.selected_provider, selected_model)
            self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Respond to ListView selection (Enter/activate) reliably.

        This ensures selection works even if key bindings on the focused widget
        consume Enter before Screen-level bindings.
        """
        try:
            logger.debug(f"on_list_view_selected: state={self._state} index={event.index}")
        except Exception:
            logger.debug(f"on_list_view_selected: state={self._state}")
        if self._state == "providers":
            self._transition_to_model_selection()
            event.stop()
            return
        if self._state == "models":
            # Mirror logic from action_select_item
            if self.selected_provider is None or not self._models:
                return
            list_view = self.query_one("#list_view", ListView)
            current_index = list_view.index
            if current_index is None:
                current_index = 0
            if current_index < 0 or current_index >= len(self._models):
                current_index = 0
            if current_index >= len(self._models):
                return
            selected_model = self._models[current_index]
            self.on_select(self.selected_provider, selected_model)
            self.app.exit()

    def _transition_to_model_selection(self) -> None:
        """Transition from provider selection to model selection."""
        list_view = self.query_one("#list_view", ListView)
        current_index = list_view.index
        # Validate index is in bounds for provider list
        if current_index is None or current_index < 0 or current_index >= len(self.providers):
            current_index = 0
        provider = self.providers[current_index]
        self.selected_provider = provider
        self._state = "models"
        # Note the provider we're about to fetch to guard against late arrivals
        self._pending_fetch_provider = provider

        # Clear and show loading placeholder while we fetch models in a background thread
        self._show_loading()

        def _fetch() -> None:
            models: list[str] = []
            try:
                logger.debug(f"Fetching models for provider: {provider}")
                models = self.get_models(provider)
                logger.debug(
                    f"Successfully fetched {len(models)} models for {provider}: {models[:3]}"
                )
                if not models:
                    # If no models returned, show an error message
                    logger.warning(f"Provider {provider} returned empty model list")
                    models = ["<no models available from provider>"]
            except Exception as e:
                # Log full exception details for debugging
                logger.error(f"Error fetching models for {provider}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # If error during fetch, show it
                error_msg = str(e)[:60] if str(e) else "unknown error"
                models = [f"<error: {error_msg}>"]
            finally:
                # Always schedule UI update by posting a Message from the thread
                try:
                    # Schedule posting the message to this Screen on the UI thread
                    def _post() -> None:
                        try:
                            # Guard: drop update if screen is no longer in 'models' state
                            # or if the selected provider changed
                            if self._state != "models":
                                logger.debug("Discarding models update; state=%s", self._state)
                                return
                            if self._pending_fetch_provider != provider:
                                logger.debug(
                                    "Discarding models update; pending=%s current=%s",
                                    self._pending_fetch_provider,
                                    provider,
                                )
                                return
                            # Ensure the screen is still active if Textual exposes is_mounted
                            if hasattr(self, "is_mounted") and not self.is_mounted:
                                logger.debug("Discarding models update; screen not mounted")
                                return
                            logger.debug(
                                f"Posting ModelsLoaded message to UI with {len(models)} models"
                            )
                            self.post_message(ModelSelectorScreen.ModelsLoaded(models))
                        except Exception:
                            logger.error("post_message failed", exc_info=True)

                    self.app.call_from_thread(_post)
                except Exception as e:
                    logger.error(f"Error scheduling ModelsLoaded message: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        logger.debug(f"Started background fetch thread for provider: {provider}")

    def action_cancel(self) -> None:
        """Handle cancel."""
        self.app.exit()

    BINDINGS = [
        ("enter", "select_item", "Select"),
        ("escape", "cancel", "Cancel"),
    ]


def show_model_selector(
    providers: list[str],
    get_models: Callable[[str], list[str]],
    on_select: Callable[[str, str], None],
) -> None:
    """Show interactive model selector in a Textual app.

    Args:
        providers: List of available provider names
        get_models: Callable that takes provider name and returns list of models
        on_select: Callback when provider/model is selected (provider_name, model_name)
    """
    from textual.app import App

    class ModelSelectorApp(App):
        """Wrapper app for model selector."""

        def on_mount(self) -> None:
            self.push_screen(ModelSelectorScreen(providers, get_models, on_select))

    app = ModelSelectorApp()
    app.run()
