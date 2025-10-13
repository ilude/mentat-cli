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

    def resolve(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            instance = self._factories[key]()
            # cache factory products by default for simplicity
            self._singletons[key] = instance
            return instance
        raise KeyError(f"Dependency not found: {key}")
