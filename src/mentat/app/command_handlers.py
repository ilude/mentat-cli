from __future__ import annotations

from typing import Callable

from ..core import Result
from ..infrastructure import ToolExecutionResult, ToolRepository
from .commands import RunTool


def handle_run_tool(repo: ToolRepository) -> Callable[[RunTool], Result[ToolExecutionResult]]:
    def _handler(cmd: RunTool) -> Result[ToolExecutionResult]:
        result = repo.execute_tool(cmd.name, cmd.args)
        return Result.success(result)

    return _handler
