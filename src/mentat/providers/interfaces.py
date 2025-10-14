"""AI provider interfaces for Mentat CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class ProviderType(Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


class MessageRole(Enum):
    """Message roles in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    def __eq__(self, other: object) -> bool:
        """Allow comparison with strings for backward compatibility."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


@dataclass
class Message:
    """Conversation message."""

    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessage:
    """Chat message for conversations."""

    role: str
    content: str
    name: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from chat completion."""

    content: str
    model: str
    usage: Optional["Usage"] = None
    finish_reason: Optional[str] = None


@dataclass
class Usage:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ModelInfo:
    """Information about an AI model."""

    id: str
    name: str
    context_length: int
    output_length: int  # Alias for max_output_tokens for test compatibility
    description: Optional[str] = None

    @property
    def max_output_tokens(self) -> int:
        """Alias for output_length for backward compatibility."""
        return self.output_length


@dataclass
class ProviderCapabilities:
    """Provider capability information."""

    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    max_context_length: int = 4096
    supported_formats: Optional[List[str]] = None

    # Backward-compatibility aliases expected by some tests
    @property
    def supports_functions(self) -> bool:
        return self.supports_function_calling

    @supports_functions.setter
    def supports_functions(self, value: bool) -> None:
        self.supports_function_calling = value

    @property
    def supports_images(self) -> bool:
        return self.supports_vision

    @supports_images.setter
    def supports_images(self, value: bool) -> None:
        self.supports_vision = value

    @property
    def max_context_tokens(self) -> int:
        return self.max_context_length

    @max_context_tokens.setter
    def max_context_tokens(self, value: int) -> None:
        self.max_context_length = value

    @property
    def supported_models(self) -> List[str]:
        return self.supported_formats or []

    @supported_models.setter
    def supported_models(self, models: List[str]) -> None:
        self.supported_formats = models

    def __post_init__(self) -> None:
        if self.supported_formats is None:
            self.supported_formats = []

    def __init__(
        self,
        supports_streaming: bool = False,
        supports_function_calling: Optional[bool] = None,
        supports_vision: Optional[bool] = None,
        max_context_length: Optional[int] = None,
        supported_formats: Optional[List[str]] = None,
        # legacy/alias kwargs
        supports_functions: Optional[bool] = None,
        supports_images: Optional[bool] = None,
        max_context_tokens: Optional[int] = None,
        supported_models: Optional[List[str]] = None,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        # Normalize aliases
        self.supports_streaming = supports_streaming
        self.supports_function_calling = (
            supports_function_calling
            if supports_function_calling is not None
            else bool(supports_functions)
        )
        self.supports_vision = (
            supports_vision if supports_vision is not None else bool(supports_images)
        )
        self.max_context_length = (
            max_context_length if max_context_length is not None else (max_context_tokens or 4096)
        )
        self.supported_formats = (
            supported_formats if supported_formats is not None else (supported_models or [])
        )


@dataclass
class CompletionResponse:
    """Response from AI provider."""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(Protocol):
    """Protocol for AI provider implementations."""

    def get_type(self) -> ProviderType:
        """Get the provider type."""
        ...

    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        ...

    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion for messages."""
        ...

    async def stream_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream completion for messages."""
        ...

    async def is_available(self) -> bool:
        """Check if provider is available."""
        ...

    async def test_connection(self) -> bool:
        """Test connection to provider."""
        ...


class BaseAIProvider(ABC):
    """Base class for AI provider implementations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config

    @abstractmethod
    def get_type(self) -> ProviderType:
        """Get the provider type."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate completion for messages."""
        pass

    async def stream_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream completion for messages. Default implementation."""
        # Default implementation for providers that don't support streaming
        response = await self.complete(messages, model, max_tokens, temperature, **kwargs)
        yield response.content

    async def is_available(self) -> bool:
        """Check if provider is available. Default implementation."""
        try:
            return await self.test_connection()
        except Exception:
            return False

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to provider."""
        pass


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    pass


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails."""

    pass


class InvalidRequestError(ProviderError):
    """Raised when request to provider is invalid."""

    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderUnavailableError(ProviderError):
    """Raised when provider is unavailable."""

    pass


class ProviderAuthError(ProviderError):
    """Raised when provider authentication fails."""

    pass


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""

    pass
