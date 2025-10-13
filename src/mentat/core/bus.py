from __future__ import annotations

from typing import Any, Callable, Dict, Type, TypeVar

from .contracts import Command, Query, Result

R = TypeVar("R")


class CommandBus:
    def __init__(self) -> None:
        # Store handlers keyed by concrete Command type; use permissive callable types
        self._handlers: Dict[Type[Command], Callable[[Any], Result[Any]]] = {}

    def register(self, command_type: Type[Command], handler: Callable[[Any], Result[Any]]) -> None:
        self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> Result[Any]:
        handler = self._handlers.get(type(command))
        if handler is None:
            return Result.failure(f"No handler registered for command: {type(command).__name__}")
        return handler(command)


class QueryBus:
    def __init__(self) -> None:
        self._handlers: Dict[Type[Query[Any]], Callable[[Any], Result[Any]]] = {}

    def register(self, query_type: Type[Query[Any]], handler: Callable[[Any], Result[Any]]) -> None:
        self._handlers[query_type] = handler

    def ask(self, query: Query[Any]) -> Result[Any]:
        handler = self._handlers.get(type(query))
        if handler is None:
            return Result.failure(f"No handler registered for query: {type(query).__name__}")
        return handler(query)
