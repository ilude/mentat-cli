"""OpenAI provider implementation for Mentat CLI."""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Dict, List, Optional

from .interfaces import (
    BaseAIProvider,
    CompletionResponse,
    Message,
    ProviderCapabilities,
    ProviderType,
)


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider implementation using the OpenAI Python SDK."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Configuration dictionary with optional keys:
                - api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
                - model: Model name (defaults to "gpt-4")
                - organization: Organization ID for multi-org accounts
                - base_url: Custom base URL for API endpoint
        """
        super().__init__(config)
        self.model = config.get("model", "gpt-4")

        # Initialize OpenAI client
        try:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]

            self.openai_async = AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            ) from exc

        # Get API key from config or environment
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided in config or OPENAI_API_KEY environment variable"
            )

        # Build client kwargs
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if "organization" in config:
            client_kwargs["organization"] = config["organization"]
        if "base_url" in config:
            client_kwargs["base_url"] = config["base_url"]

        self.client = self.openai_async(**client_kwargs)

    def get_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.OPENAI

    def get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI provider capabilities."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=True,
            max_context_length=128000,  # GPT-4 context window
            supported_formats=["json", "text"],
        )

    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion using OpenAI API.

        Args:
            messages: List of messages in conversation
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
            **kwargs: Additional OpenAI API parameters

        Returns:
            CompletionResponse with generated text

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded
            ProviderUnavailableError: If service unavailable
        """
        model_to_use = model or self.model

        # Convert Message objects to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append(
                {
                    "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                    "content": msg.content,
                }
            )

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": model_to_use,
            "messages": openai_messages,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        try:
            response = await self.client.chat.completions.create(**request_params)

            # Extract content
            content = response.choices[0].message.content or ""

            # Build usage dict
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            return CompletionResponse(
                content=content,
                model=response.model,
                usage=usage_dict,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
        except Exception as exc:
            # Re-raise with more context
            raise exc

    async def stream_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream completion using OpenAI API.

        Args:
            messages: List of messages in conversation
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
            **kwargs: Additional OpenAI API parameters

        Yields:
            Streamed text chunks
        """
        model_to_use = model or self.model

        # Convert Message objects to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append(
                {
                    "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                    "content": msg.content,
                }
            )

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": model_to_use,
            "messages": openai_messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }

        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        try:
            stream = await self.client.chat.completions.create(**request_params)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            raise exc

    async def test_connection(self) -> bool:
        """Test connection to OpenAI API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a minimal API call to verify connection
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return response is not None
        except Exception:
            return False
