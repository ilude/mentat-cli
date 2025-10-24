"""Integration tests for the RunCommand handler and non-interactive execution."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from mentat.app.command_handlers import handle_run_command
from mentat.app.commands import RunCommand
from mentat.core import CommandBus, Result
from mentat.infrastructure.formatters import OutputFormatter
from mentat.providers.interfaces import CompletionResponse, MessageRole


@pytest.fixture
def mock_provider():
    """Create a mock AI provider for testing."""
    provider = AsyncMock()
    provider.complete = AsyncMock(
        return_value=CompletionResponse(
            content="Generated code: def parse_json(s): return json.loads(s)",
            model="claude-3-sonnet",
            usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
            finish_reason="stop",
        )
    )
    return provider


@pytest.fixture
def command_bus():
    """Create a command bus for testing."""
    return CommandBus()


class TestRunCommand:
    """Tests for RunCommand DTO."""

    def test_run_command_creation(self):
        """Test creating a RunCommand."""
        cmd = RunCommand(prompt="create a function", format="json")
        assert cmd.prompt == "create a function"
        assert cmd.format == "json"
        assert cmd.output_file is None

    def test_run_command_with_output_file(self):
        """Test RunCommand with output file."""
        cmd = RunCommand(prompt="test", format="markdown", output_file="/tmp/output.md")
        assert cmd.output_file == "/tmp/output.md"

    def test_run_command_default_format(self):
        """Test RunCommand with default format."""
        cmd = RunCommand(prompt="test")
        assert cmd.format == "text"


class TestRunCommandHandler:
    """Tests for the RunCommand handler."""

    @pytest.mark.asyncio
    async def test_handle_run_command_success(self, mock_provider):
        """Test successful command execution through handler."""
        handler = handle_run_command(mock_provider)
        cmd = RunCommand(prompt="create a function", format="text")

        result: Result = handler(cmd)

        assert result.ok
        assert result.value is not None
        assert result.value.content == "Generated code: def parse_json(s): return json.loads(s)"
        mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_run_command_with_message_format(self, mock_provider):
        """Test that handler converts prompt to Message."""
        handler = handle_run_command(mock_provider)
        cmd = RunCommand(prompt="test prompt", format="text")

        handler(cmd)

        # Verify the provider was called with Message objects
        call_args = mock_provider.complete.call_args
        assert call_args is not None
        messages = call_args[0][0]
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "test prompt"

    @pytest.mark.asyncio
    async def test_handle_run_command_failure(self, mock_provider):
        """Test handler error handling."""
        mock_provider.complete = AsyncMock(side_effect=Exception("API error"))
        handler = handle_run_command(mock_provider)
        cmd = RunCommand(prompt="test", format="text")

        result: Result = handler(cmd)

        assert not result.ok
        assert result.error is not None
        assert "API error" in result.error


class TestOutputFormatter:
    """Tests for output formatting."""

    @pytest.fixture
    def sample_response(self):
        """Create a sample completion response."""
        return CompletionResponse(
            content="def hello():\n    return 'world'",
            model="claude-3-sonnet",
            usage={"prompt_tokens": 5, "completion_tokens": 20, "total_tokens": 25},
            finish_reason="stop",
        )

    def test_format_text(self, sample_response):
        """Test text format output."""
        output = OutputFormatter.format(sample_response, "text")
        assert output == "def hello():\n    return 'world'"

    def test_format_json(self, sample_response):
        """Test JSON format output."""
        output = OutputFormatter.format(sample_response, "json")
        data = json.loads(output)
        assert data["content"] == "def hello():\n    return 'world'"
        assert data["model"] == "claude-3-sonnet"
        assert data["usage"]["total_tokens"] == 25

    def test_format_markdown(self, sample_response):
        """Test Markdown format output."""
        output = OutputFormatter.format(sample_response, "markdown")
        assert "---" in output  # YAML front-matter
        assert sample_response.model in output
        assert "def hello():" in output

    def test_format_invalid_format(self, sample_response):
        """Test invalid format raises error."""
        with pytest.raises(ValueError, match="Unknown format type"):
            OutputFormatter.format(sample_response, "invalid")


class TestCommandBusIntegration:
    """Integration tests for RunCommand through command bus."""

    def test_register_and_dispatch_run_command(self, mock_provider, command_bus):
        """Test registering and dispatching RunCommand."""
        handler = handle_run_command(mock_provider)
        command_bus.register(RunCommand, handler)

        cmd = RunCommand(prompt="test", format="text")
        result = command_bus.dispatch(cmd)

        assert result.ok
        assert result.value is not None
        assert "parse_json" in result.value.content

    def test_multiple_commands_in_sequence(self, mock_provider, command_bus):
        """Test executing multiple commands in sequence."""
        handler = handle_run_command(mock_provider)
        command_bus.register(RunCommand, handler)

        for i in range(3):
            cmd = RunCommand(prompt=f"test prompt {i}", format="text")
            result = command_bus.dispatch(cmd)
            assert result.ok
            assert result.value is not None

        assert mock_provider.complete.call_count == 3


class TestEndToEndRunCommand:
    """End-to-end tests for the entire RunCommand flow."""

    @pytest.mark.asyncio
    async def test_e2e_prompt_execution(self, mock_provider, tmp_path):
        """Test full prompt execution flow."""
        # Setup
        handler = handle_run_command(mock_provider)
        cmd = RunCommand(
            prompt="create a Python function to parse JSON",
            format="json",
            output_file=str(tmp_path / "output.json"),
        )

        # Execute
        result = handler(cmd)

        # Verify
        assert result.ok
        response = result.value
        assert response is not None
        assert response.content is not None

        # Format output
        formatted = OutputFormatter.format(response, "json")
        assert "parse_json" in formatted

    def test_e2e_with_different_formats(self, mock_provider):
        """Test execution with different output formats."""
        handler = handle_run_command(mock_provider)

        for format_type in ("text", "json", "markdown"):
            cmd = RunCommand(prompt="test", format=format_type)
            result = handler(cmd)
            assert result.ok

            # Verify formatting works
            response = result.value
            assert response is not None
            formatted = OutputFormatter.format(response, format_type)
            assert len(formatted) > 0

    def test_e2e_with_error_handling(self, mock_provider):
        """Test error handling in full flow."""
        mock_provider.complete = AsyncMock(side_effect=ValueError("Invalid prompt"))
        handler = handle_run_command(mock_provider)
        cmd = RunCommand(prompt="bad input", format="text")

        result = handler(cmd)

        assert not result.ok
        assert result.error is not None
        assert "Invalid prompt" in result.error
