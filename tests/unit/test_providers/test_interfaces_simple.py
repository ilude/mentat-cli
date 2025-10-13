"""Tests for provider interfaces - basic tests."""

from typing import Any, AsyncIterator, List, Optional

import pytest

from mentat.providers.interfaces import (
    AIProvider,
    BaseAIProvider,
    CompletionResponse,
    Message,
    MessageRole,
    ProviderCapabilities,
    ProviderType,
)


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing."""

    def __init__(self, provider_type: ProviderType = ProviderType.LOCAL):
        self._type = provider_type
        self._available = True

    def get_type(self) -> ProviderType:
        return self._type

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_functions=False,
            supports_images=False,
            max_context_tokens=4096,
            max_output_tokens=1024,
            supported_models=["mock-model-1", "mock-model-2"],
        )

    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Mock completion."""
        response_text = f"Mock response to {len(messages)} messages"
        return CompletionResponse(
            content=response_text,
            model=model or "mock-model-1",
            usage={"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
            finish_reason="stop",
        )

    async def stream_complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Mock streaming completion."""
        parts = ["Mock ", "streaming ", "response"]
        for part in parts:
            yield part

    async def is_available(self) -> bool:
        return self._available

    async def test_connection(self) -> bool:
        return self._available


class TestProviderEnums:
    """Test provider enumeration classes."""

    def test_provider_type_enum(self):
        """Test ProviderType enum values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.LOCAL.value == "local"

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"


class TestDataModels:
    """Test data model classes."""

    def test_message_creation(self):
        """Test Message creation."""
        message = Message(role=MessageRole.USER, content="Hello world")

        assert message.role == MessageRole.USER
        assert message.content == "Hello world"
        assert message.metadata is None

    def test_message_with_metadata(self):
        """Test Message with metadata."""
        metadata = {"source": "test", "timestamp": "2023-01-01"}
        message = Message(role=MessageRole.ASSISTANT, content="Response", metadata=metadata)

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Response"
        assert message.metadata == metadata

    def test_provider_capabilities_creation(self):
        """Test ProviderCapabilities creation."""
        capabilities = ProviderCapabilities(
            supports_streaming=True,
            supports_functions=True,
            max_context_tokens=8192,
            supported_models=["model-1", "model-2"],
        )

        assert capabilities.supports_streaming is True
        assert capabilities.supports_functions is True
        assert capabilities.supports_images is False  # default
        assert capabilities.max_context_tokens == 8192
        assert capabilities.supported_models == ["model-1", "model-2"]

    def test_provider_capabilities_defaults(self):
        """Test ProviderCapabilities default values."""
        capabilities = ProviderCapabilities()

        assert capabilities.supports_streaming is False
        assert capabilities.supports_functions is False
        assert capabilities.supports_images is False
        assert capabilities.max_context_tokens == 4096
        assert capabilities.supported_models == []

    def test_completion_response_creation(self):
        """Test CompletionResponse creation."""
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        response = CompletionResponse(
            content="Test response", model="test-model", usage=usage, finish_reason="stop"
        )

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.usage == usage
        assert response.finish_reason == "stop"
        assert response.metadata is None

    def test_completion_response_with_metadata(self):
        """Test CompletionResponse with metadata."""
        metadata = {"processing_time": 1.5, "provider": "test"}
        response = CompletionResponse(
            content="Response",
            model="model",
            usage={"total_tokens": 100},
            finish_reason="length",
            metadata=metadata,
        )

        assert response.metadata == metadata


class TestMockProvider:
    """Test mock AI provider implementation."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        return MockAIProvider()

    def test_provider_type(self, mock_provider):
        """Test provider type."""
        assert mock_provider.get_type() == ProviderType.LOCAL

    def test_provider_capabilities(self, mock_provider):
        """Test provider capabilities."""
        capabilities = mock_provider.get_capabilities()

        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.supports_streaming is True
        assert capabilities.max_context_tokens == 4096
        assert capabilities.supported_models is not None
        assert len(capabilities.supported_models) == 2

    @pytest.mark.asyncio
    async def test_completion(self, mock_provider):
        """Test completion generation."""
        messages = [Message(role=MessageRole.USER, content="Hello")]

        response = await mock_provider.complete(messages)

        assert isinstance(response, CompletionResponse)
        assert "Mock response to 1 messages" in response.content
        assert response.model == "mock-model-1"
        assert isinstance(response.usage, dict)

    @pytest.mark.asyncio
    async def test_completion_with_model(self, mock_provider):
        """Test completion with specific model."""
        messages = [Message(role=MessageRole.USER, content="Test")]

        response = await mock_provider.complete(messages, model="custom-model")

        assert response.model == "custom-model"

    @pytest.mark.asyncio
    async def test_stream_completion(self, mock_provider):
        """Test streaming completion."""
        messages = [Message(role=MessageRole.USER, content="Stream test")]

        chunks = []
        async for chunk in mock_provider.stream_complete(messages):
            chunks.append(chunk)

        assert chunks == ["Mock ", "streaming ", "response"]

    @pytest.mark.asyncio
    async def test_availability(self, mock_provider):
        """Test provider availability check."""
        available = await mock_provider.is_available()
        assert available is True

    @pytest.mark.asyncio
    async def test_connection_test(self, mock_provider):
        """Test connection testing."""
        connection_ok = await mock_provider.test_connection()
        assert connection_ok is True


class TestProviderProtocol:
    """Test provider protocol compliance."""

    def test_protocol_attributes(self):
        """Test that AIProvider protocol has required attributes."""
        # This tests that the protocol is properly defined
        assert hasattr(AIProvider, "get_type")
        assert hasattr(AIProvider, "get_capabilities")
        assert hasattr(AIProvider, "complete")
        assert hasattr(AIProvider, "stream_complete")
        assert hasattr(AIProvider, "is_available")
        assert hasattr(AIProvider, "test_connection")

    def test_mock_provider_implements_protocol(self):
        """Test that mock provider implements the protocol."""
        provider = MockAIProvider()

        # Should have all required methods
        assert hasattr(provider, "get_type")
        assert hasattr(provider, "get_capabilities")
        assert hasattr(provider, "complete")
        assert hasattr(provider, "stream_complete")
        assert hasattr(provider, "is_available")
        assert hasattr(provider, "test_connection")


class TestProviderTypes:
    """Test different provider types."""

    @pytest.mark.parametrize(
        "provider_type",
        [ProviderType.OPENAI, ProviderType.ANTHROPIC, ProviderType.GEMINI, ProviderType.LOCAL],
    )
    def test_different_provider_types(self, provider_type):
        """Test creating providers with different types."""
        provider = MockAIProvider(provider_type)
        assert provider.get_type() == provider_type

    def test_provider_type_string_values(self):
        """Test that provider types have correct string values."""
        types_and_values = [
            (ProviderType.OPENAI, "openai"),
            (ProviderType.ANTHROPIC, "anthropic"),
            (ProviderType.GEMINI, "gemini"),
            (ProviderType.LOCAL, "local"),
        ]

        for provider_type, expected_value in types_and_values:
            assert provider_type.value == expected_value


class TestMessageHandling:
    """Test message handling scenarios."""

    def test_conversation_flow(self):
        """Test typical conversation message flow."""
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello!"),
            Message(role=MessageRole.ASSISTANT, content="Hi there! How can I help you?"),
            Message(role=MessageRole.USER, content="Tell me about Python."),
        ]

        assert len(messages) == 4
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[-1].role == MessageRole.USER

    def test_message_serialization_data(self):
        """Test that message data is accessible."""
        message = Message(
            role=MessageRole.USER,
            content="Test message",
            metadata={"id": "msg_1", "timestamp": "2023-01-01T12:00:00Z"},
        )

        # Should be able to access all fields
        assert message.role.value == "user"
        assert message.content == "Test message"
        assert message.metadata is not None
        assert message.metadata["id"] == "msg_1"
