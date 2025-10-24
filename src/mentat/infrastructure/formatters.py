"""Output formatters for Mentat CLI."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..providers.interfaces import CompletionResponse


class OutputFormatter:
    """Formats provider responses in different output formats."""

    @staticmethod
    def format(response: CompletionResponse, format_type: str = "text") -> str:
        """Format a completion response.

        Args:
            response: CompletionResponse from provider
            format_type: Output format - "text", "json", or "markdown"

        Returns:
            Formatted output string

        Raises:
            ValueError: If format_type is not recognized
        """
        if format_type == "json":
            return OutputFormatter.format_json(response)
        elif format_type == "markdown":
            return OutputFormatter.format_markdown(response)
        elif format_type == "text":
            return OutputFormatter.format_text(response)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    @staticmethod
    def format_text(response: CompletionResponse) -> str:
        """Format response as plain text.

        Args:
            response: CompletionResponse from provider

        Returns:
            Plain text content
        """
        return response.content

    @staticmethod
    def format_json(response: CompletionResponse) -> str:
        """Format response as JSON.

        Args:
            response: CompletionResponse from provider

        Returns:
            JSON formatted response with metadata
        """
        output: Dict[str, Any] = {
            "content": response.content,
            "model": response.model,
            "finish_reason": response.finish_reason,
            "usage": response.usage,
        }

        if response.metadata:
            output["metadata"] = response.metadata

        return json.dumps(output, indent=2)

    @staticmethod
    def format_markdown(response: CompletionResponse) -> str:
        """Format response as Markdown with metadata.

        Args:
            response: CompletionResponse from provider

        Returns:
            Markdown formatted response
        """
        lines = []

        # Add metadata as YAML front-matter
        lines.append("---")
        lines.append(f"model: {response.model}")
        lines.append(f"finish_reason: {response.finish_reason}")
        if response.usage:
            lines.append(f"tokens_used: {response.usage.get('total_tokens', 0)}")
        lines.append("---")
        lines.append("")

        # Add content
        lines.append(response.content)

        return "\n".join(lines)


class OutputWriter:
    """Writes formatted output to files or stdout."""

    @staticmethod
    def write(content: str, output_file: Optional[str] = None) -> None:
        """Write content to file or stdout.

        Args:
            content: Content to write
            output_file: Optional file path. If None, writes to stdout

        Raises:
            IOError: If file write fails
        """
        if output_file is None:
            # Write to stdout
            print(content)
        else:
            # Write to file
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except IOError as exc:
                raise IOError(f"Failed to write to {output_file}: {exc}") from exc
