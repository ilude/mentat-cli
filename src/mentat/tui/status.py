"""REPL status bar showing provider and model."""

from __future__ import annotations


class REPLStatus:
    """Tracks and displays REPL status (provider and model)."""

    def __init__(self, default_provider: str = "anthropic", default_model: str = "") -> None:
        """Initialize REPL status.

        Args:
            default_provider: Default provider name (e.g., "anthropic")
            default_model: Default model name (empty string until user selects)
        """
        self.provider = default_provider
        self.model = default_model

    def set_provider(self, provider: str) -> None:
        """Set active provider."""
        self.provider = provider

    def set_model(self, model: str) -> None:
        """Set active model."""
        self.model = model

    def set_provider_and_model(self, provider: str, model: str) -> None:
        """Set both provider and model."""
        self.provider = provider
        self.model = model

    def format_status_bar(self, width: int = 80) -> str:
        """Format status bar for display.

        Layout:
        - Left: Provider name
        - Right: Model name
        - Middle: Filled with spaces

        Args:
            width: Terminal width in characters

        Returns:
            Formatted status bar string
        """
        left = f"Provider: {self.provider}"
        right = f"Model: {self.model}" if self.model else "Model: <not set>"

        # Calculate middle spacing
        middle_width = width - len(left) - len(right)
        if middle_width < 1:
            middle_width = 1

        status_bar = left + " " * middle_width + right
        # Truncate if needed
        if len(status_bar) > width:
            status_bar = status_bar[:width]

        return status_bar

    def display(self, width: int = 80) -> None:
        """Print status bar to console.

        Args:
            width: Terminal width in characters
        """
        import shutil

        # Get actual terminal width if not specified
        if width == 80:
            width = shutil.get_terminal_size((80, 20)).columns

        status = self.format_status_bar(width)
        # Print with inverse video (white on black)
        print(f"\033[7m{status}\033[0m")

    def display_update(self) -> str:
        """Return status message for display after update.

        Returns:
            Short message indicating what was changed
        """
        return f"Provider: {self.provider} | Model: {self.model or '<not set>'}"
