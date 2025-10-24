from __future__ import annotations

from typing import Any, Callable, List

from ..core import Result
from ..infrastructure import ToolExecutionResult, ToolRepository
from ..providers.interfaces import CompletionResponse, Message, MessageRole
from .commands import RunCommand, RunTool


def handle_run_tool(repo: ToolRepository) -> Callable[[RunTool], Result[ToolExecutionResult]]:
    def _handler(cmd: RunTool) -> Result[ToolExecutionResult]:
        result = repo.execute_tool(cmd.name, cmd.args)
        return Result.success(result)

    return _handler


def handle_run_command(
    provider: Any,
) -> Callable[[RunCommand], Result[CompletionResponse]]:
    """Create handler for RunCommand that executes through AI provider.

    Args:
        provider: AI provider instance that implements AIProvider protocol

    Returns:
        Handler function that takes RunCommand and returns Result[CompletionResponse]
    """

    def _handler(cmd: RunCommand) -> Result[CompletionResponse]:
        """Synchronous handler wrapper using asyncio."""
        import asyncio
        import threading

        async def _execute_async() -> CompletionResponse:
            messages: List[Message] = [Message(role=MessageRole.USER, content=cmd.prompt)]
            response = await provider.complete(messages)
            return response

        try:
            # Check if we're already in an event loop
            try:
                asyncio.get_running_loop()
                is_running = True
            except RuntimeError:
                is_running = False

            if is_running:
                # We're in an async context, run in a separate thread
                result_container: List[Any] = []
                error_container: List[Any] = []

                def run_in_thread() -> None:
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(_execute_async())
                            result_container.append(result)
                        finally:
                            new_loop.close()
                    except Exception as e:
                        error_container.append(e)

                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()

                if error_container:
                    raise error_container[0]
                if result_container:
                    response = result_container[0]
                else:
                    raise RuntimeError("No result from thread")
            else:
                # No running loop, safe to use asyncio.run
                response = asyncio.run(_execute_async())

            return Result.success(response)
        except Exception as exc:
            return Result.failure(str(exc))

    return _handler
