from __future__ import annotations

from typing import Callable

from ..core import Result
from ..infrastructure import ToolRepository
from .commands import RunTool


def handle_run_tool(repo: ToolRepository) -> Callable[[RunTool], Result[int]]:
    def _handler(cmd: RunTool) -> Result[int]:
        code = repo.run_tool(cmd.name, cmd.args)
        return Result.success(code)

    return _handler
