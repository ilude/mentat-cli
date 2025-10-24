from __future__ import annotations

from typing import Callable

from ..core import Result
from ..infrastructure import ToolRepository
from .queries import ListTools, ToolInfo


def handle_list_tools(repo: ToolRepository) -> Callable[[ListTools], Result[list[ToolInfo]]]:
    def _handler(q: ListTools) -> Result[list[ToolInfo]]:
        infos = [
            ToolInfo(name=t.name, description=t.description, command=t.command)
            for t in repo.list_tools()
        ]
        return Result.success(infos)

    return _handler
