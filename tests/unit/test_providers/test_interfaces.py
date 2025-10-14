"""Tests for provider interfaces."""

from typing import AsyncGenerator, Dict, List

import pytest

from mentat.providers.interfaces import (
    AIProvider,
    AuthenticationError,
    ChatMessage,
    ChatResponse,
    InvalidRequestError,
    ModelInfo,
    ProviderCapabilities,
    ProviderError,
    RateLimitError,
    Usage,
)


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""

    def __init__(self, name: str = "mock"):
        self._name = name
        self._authenticated = False
        self._models = [
            ModelInfo("mock-model-1", "Mock Model 1", 4096, 2048),
            ModelInfo("mock-model-2", "Mock Model 2", 8192, 4096),
        ]

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
            max_context_length=8192,
            supported_formats=["text", "json"],
        )

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Mock authentication."""
        if credentials.get("api_key") == "valid_key":
            self._authenticated = True
            return True
        return False

    def is_authenticated(self) -> bool:
        return self._authenticated

    async def get_available_models(self) -> List[ModelInfo]:
        return self._models

    async def chat_completion(
        self, messages: List[ChatMessage], model: str = "mock-model-1", **kwargs
    ) -> ChatResponse:
        """Mock chat completion."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated")

        if model not in [m.id for m in self._models]:
            raise InvalidRequestError(f"Model {model} not found")

        # Mock response
        response_text = f"Mock response for {len(messages)} messages"
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

        return ChatResponse(content=response_text, model=model, usage=usage, finish_reason="stop")

    async def stream_chat_completion(
        self, messages: List[ChatMessage], model: str = "mock-model-1", **kwargs
    ) -> AsyncGenerator[str, None]:
        """Mock streaming chat completion."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated")

        response_parts = ["Mock ", "streaming ", "response"]
        for part in response_parts:
            yield part


class TestAIProviderInterface:
    """Test AI provider interface."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock AI provider."""
        return MockAIProvider()

    def test_provider_properties(self, mock_provider):
        """Test provider basic properties."""
        assert mock_provider.name == "mock"

        capabilities = mock_provider.capabilities
        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.max_context_length == 8192

    @pytest.mark.asyncio
    async def test_authentication_success(self, mock_provider):
        """Test successful authentication."""
        assert mock_provider.is_authenticated() is False

        result = await mock_provider.authenticate({"api_key": "valid_key"})
        assert result is True
        assert mock_provider.is_authenticated() is True

    @pytest.mark.asyncio
    async def test_authentication_failure(self, mock_provider):
        """Test failed authentication."""
        result = await mock_provider.authenticate({"api_key": "invalid_key"})
        assert result is False
        assert mock_provider.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_get_available_models(self, mock_provider):
        """Test getting available models."""
        models = await mock_provider.get_available_models()

        assert len(models) == 2
        assert all(isinstance(model, ModelInfo) for model in models)
        assert models[0].id == "mock-model-1"
        assert models[1].id == "mock-model-2"

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, mock_provider):
        """Test successful chat completion."""
        # Authenticate first
        await mock_provider.authenticate({"api_key": "valid_key"})

        messages = [ChatMessage(role="user", content="Hello, world!")]

        response = await mock_provider.chat_completion(messages)

        assert isinstance(response, ChatResponse)
        assert response.content == "Mock response for 1 messages"
        assert response.model == "mock-model-1"
        assert isinstance(response.usage, Usage)
        assert response.usage.total_tokens == 150

    @pytest.mark.asyncio
    async def test_chat_completion_not_authenticated(self, mock_provider):
        """Test chat completion without authentication."""
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AuthenticationError):
            await mock_provider.chat_completion(messages)

    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self, mock_provider):
        """Test chat completion with invalid model."""
        await mock_provider.authenticate({"api_key": "valid_key"})

        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(InvalidRequestError):
            await mock_provider.chat_completion(messages, model="nonexistent-model")

    @pytest.mark.asyncio
    async def test_stream_chat_completion(self, mock_provider):
        """Test streaming chat completion."""
        await mock_provider.authenticate({"api_key": "valid_key"})

        messages = [ChatMessage(role="user", content="Hello")]

        response_parts = []
        async for chunk in mock_provider.stream_chat_completion(messages):
            response_parts.append(chunk)

        assert response_parts == ["Mock ", "streaming ", "response"]

    @pytest.mark.asyncio
    async def test_stream_chat_completion_not_authenticated(self, mock_provider):
        """Test streaming without authentication."""
        messages = [ChatMessage(role="user", content="Hello")]

        with pytest.raises(AuthenticationError):
            async for _ in mock_provider.stream_chat_completion(messages):
                pass


class TestDataModels:
    """Test data model classes."""

    def test_chat_message_creation(self):
        """Test ChatMessage creation."""
        message = ChatMessage(role="user", content="Hello, world!")

        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.name is None

    def test_chat_message_with_name(self):
        """Test ChatMessage with name."""
        message = ChatMessage(role="assistant", content="Response", name="assistant_1")

        assert message.role == "assistant"
        assert message.content == "Response"
        assert message.name == "assistant_1"

    def test_chat_response_creation(self):
        """Test ChatResponse creation."""
        usage = Usage(prompt_tokens=50, completion_tokens=25, total_tokens=75)
        response = ChatResponse(
            content="Test response", model="test-model", usage=usage, finish_reason="stop"
        )

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.usage == usage
        assert response.finish_reason == "stop"

    def test_usage_creation(self):
        """Test Usage model creation."""
        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        model = ModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo", 4096, 2048)

        assert model.id == "gpt-3.5-turbo"
        assert model.name == "GPT-3.5 Turbo"
        assert model.context_length == 4096
        assert model.output_length == 2048

    def test_provider_capabilities_creation(self):
        """Test ProviderCapabilities creation."""
        capabilities = ProviderCapabilities(
            supports_streaming=True,
            supports_function_calling=False,
            supports_vision=True,
            max_context_length=8192,
            supported_formats=["text", "json", "markdown"],
        )

        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is False
        assert capabilities.supports_vision is True
        assert capabilities.max_context_length == 8192
        assert capabilities.supported_formats == ["text", "json", "markdown"]


class TestProviderExceptions:
    """Test provider exception classes."""

    def test_provider_error(self):
        """Test base ProviderError."""
        error = ProviderError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        assert str(error) == "Invalid API key"
        assert isinstance(error, ProviderError)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60
        assert isinstance(error, ProviderError)

    def test_invalid_request_error(self):
        """Test InvalidRequestError."""
        error = InvalidRequestError("Invalid model specified")
        assert str(error) == "Invalid model specified"
        assert isinstance(error, ProviderError)

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        # All specific exceptions should inherit from ProviderError
        assert issubclass(AuthenticationError, ProviderError)
        assert issubclass(RateLimitError, ProviderError)
        assert issubclass(InvalidRequestError, ProviderError)

        # ProviderError should inherit from Exception
        assert issubclass(ProviderError, Exception)


class TestProviderIntegration:
    """Test provider integration scenarios."""

    @pytest.fixture
    def authenticated_provider(self):
        """Create authenticated mock provider."""
        provider = MockAIProvider()
        return provider

    @pytest.mark.asyncio
    async def test_full_workflow(self, authenticated_provider):
        """Test complete provider workflow."""
        # 1. Authenticate
        auth_result = await authenticated_provider.authenticate({"api_key": "valid_key"})
        assert auth_result is True

        # 2. Get available models
        models = await authenticated_provider.get_available_models()
        assert len(models) > 0

        # 3. Use first available model for chat
        model = models[0]
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello!"),
        ]

        response = await authenticated_provider.chat_completion(messages, model=model.id)
        assert response.content is not None
        assert response.model == model.id

    @pytest.mark.asyncio
    async def test_error_recovery(self, authenticated_provider):
        """Test error handling and recovery."""
        # Try without authentication
        messages = [ChatMessage(role="user", content="Test")]

        with pytest.raises(AuthenticationError):
            await authenticated_provider.chat_completion(messages)

        # Authenticate and try again
        await authenticated_provider.authenticate({"api_key": "valid_key"})

        response = await authenticated_provider.chat_completion(messages)
        assert response.content is not None

    def test_provider_comparison(self):
        """Test comparing providers."""
        provider1 = MockAIProvider("provider1")
        provider2 = MockAIProvider("provider2")

        assert provider1.name != provider2.name

        # Both should have same capabilities structure
        cap1 = provider1.capabilities
        cap2 = provider2.capabilities

        assert cap1.supports_streaming == cap2.supports_streaming
        assert cap1.max_context_length == cap2.max_context_length
