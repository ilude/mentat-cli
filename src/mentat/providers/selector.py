"""AI provider selection and initialization logic."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .interfaces import AIProvider


class ProviderSelector:
    """Selects and initializes AI providers based on configuration."""

    def __init__(self, provider_configs: Dict[str, Dict[str, Any]]) -> None:
        """Initialize selector with provider configurations.

        Args:
            provider_configs: Dictionary mapping provider names to their configs
                Example: {
                    "anthropic": {"api_key": "...", "model": "claude-3-sonnet"},
                    "openai": {"api_key": "...", "model": "gpt-4"}
                }
        """
        self.provider_configs = provider_configs
        self._instances: Dict[str, AIProvider] = {}

    def select(self, provider_name: Optional[str] = None) -> AIProvider:
        """Select and return a provider instance.

        Args:
            provider_name: Name of provider to use. If None, returns default (anthropic)

        Returns:
            AIProvider instance ready for use

        Raises:
            ValueError: If provider not found or not configured
            ImportError: If provider module not available
        """
        if provider_name is None:
            provider_name = "anthropic"

        # Return cached instance if available
        if provider_name in self._instances:
            return self._instances[provider_name]

        # Get provider config
        if provider_name not in self.provider_configs:
            raise ValueError(f"Provider '{provider_name}' not configured")

        config = self.provider_configs[provider_name]

        # Load and instantiate provider
        provider = self._load_provider(provider_name, config)
        self._instances[provider_name] = provider
        return provider

    def _load_provider(self, provider_name: str, config: Dict[str, Any]) -> AIProvider:
        """Load and instantiate a provider by name.

        Args:
            provider_name: Name of the provider (anthropic, openai, gemini, local)
            config: Provider configuration dict

        Returns:
            Instantiated provider

        Raises:
            ValueError: If provider name not recognized
            ImportError: If provider module not available
        """
        provider_map = {
            "anthropic": ("mentat.providers.anthropic_provider", "AnthropicProvider"),
            "openai": ("mentat.providers.openai", "OpenAIProvider"),
            "gemini": ("mentat.providers.gemini", "GeminiProvider"),
            "local": ("mentat.providers.local", "LocalProvider"),
        }

        if provider_name not in provider_map:
            raise ValueError(f"Unknown provider: {provider_name}")

        module_name, class_name = provider_map[provider_name]

        try:
            module = __import__(module_name, fromlist=[class_name])
            provider_class = getattr(module, class_name)
            return provider_class(config=config)
        except ImportError as exc:
            raise ImportError(f"Failed to load provider '{provider_name}': {exc}") from exc
        except AttributeError as exc:
            raise ValueError(
                f"Provider class '{class_name}' not found in '{module_name}': {exc}"
            ) from exc

    def list_available(self) -> list[str]:
        """List available configured providers.

        Returns:
            List of provider names that have configuration
        """
        return list(self.provider_configs.keys())

    def get_default(self) -> str:
        """Get the default provider name.

        Returns:
            Default provider name ("anthropic" unless overridden)
        """
        # Could be extended to read from config
        return "anthropic"

    def is_available(self, provider_name: str) -> bool:
        """Check if a provider is available and configured.

        Args:
            provider_name: Name of provider to check

        Returns:
            True if provider is configured, False otherwise
        """
        return provider_name in self.provider_configs
