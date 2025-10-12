from __future__ import annotations

from ..core import Result
from ..infrastructure import ToolRepository
from .queries import ListTools


def handle_list_tools(repo: ToolRepository):
    def _handler(q: ListTools) -> Result[list[str]]:
        names = [t.name for t in repo.list_tools()]
        return Result.success(names)

    return _handler
