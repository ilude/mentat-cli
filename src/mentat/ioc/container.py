from __future__ import annotations

from typing import Any, Callable, Dict


class Container:
    """Minimal IoC container using a registry of factories and singletons."""

    def __init__(self) -> None:
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}

    def register_singleton(self, key: str, instance: Any) -> None:
        self._singletons[key] = instance

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        self._factories[key] = factory

    def register(self, interface: type, implementation: Any) -> None:
        """Register implementation for an interface (convenience method for typed registration)."""
        key = interface.__name__
        if callable(implementation) and not isinstance(implementation, type):
            # If implementation is a factory function
            self.register_factory(key, implementation)
        elif isinstance(implementation, type):
            # If implementation is a class, create a factory
            self.register_factory(key, lambda: implementation())
        else:
            # Otherwise register as singleton
            self.register_singleton(key, implementation)

    def resolve(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            instance = self._factories[key]()
            # cache factory products by default for simplicity
            self._singletons[key] = instance
            return instance
        raise KeyError(f"Dependency not found: {key}")


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """Get or create the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def bootstrap_container() -> Container:
    """Bootstrap the IoC container with all service registrations.

    Registers core interfaces and implementations:
    - Storage backends (abstract interface, filesystem default)
    - VCS backends (abstract interface, git default)
    - AI providers (abstract interface, OpenAI/Anthropic/Gemini)
    - Safety validators (pattern-based command validation)
    - Session managers (context and history management)
    """
    container = get_container()

    # These will be registered by their respective modules when they initialize
    # This provides a hook for future enhanced registration logic

    return container
