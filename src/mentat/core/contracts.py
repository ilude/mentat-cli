from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class Command:
    """Marker base class for write operations."""


class Query(Generic[T]):
    """Marker base class for read operations returning type T."""


@dataclass(slots=True)
class Result(Generic[T]):
    ok: bool
    value: Optional[T] = None
    error: Optional[str] = None

    @staticmethod
    def success(value: Optional[T] = None) -> "Result[T]":
        return Result(ok=True, value=value)

    @staticmethod
    def failure(error: str) -> "Result[Any]":
        return Result(ok=False, error=error)
