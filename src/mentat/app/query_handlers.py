from __future__ import annotations

from typing import Callable

from ..core import Result
from ..infrastructure import ToolRepository
from .queries import ListTools


def handle_list_tools(repo: ToolRepository) -> Callable[[ListTools], Result[list[str]]]:
    def _handler(q: ListTools) -> Result[list[str]]:
        names = [t.name for t in repo.list_tools()]
        return Result.success(names)

    return _handler
