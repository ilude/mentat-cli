"""Unit tests for storage interfaces."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from mentat.infrastructure.storage.interfaces import BaseStorageBackend, StorageError


class MockStorageBackend(BaseStorageBackend):
    """Mock storage backend for testing interface compliance."""

    def __init__(self, base_path: Optional[Path] = None):
        super().__init__(base_path)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._conversations: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._contexts: Dict[str, Dict[str, Any]] = {}

    async def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data in memory."""
        self._sessions[session_id] = data

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from memory."""
        return self._sessions.get(session_id)

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""
        return list(self._sessions.keys())

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            # Also delete conversations
            if session_id in self._conversations:
                del self._conversations[session_id]
            return True
        return False

    async def store_conversation(
        self, session_id: str, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> None:
        """Store conversation in memory."""
        if session_id not in self._conversations:
            self._conversations[session_id] = {}
        self._conversations[session_id][conversation_id] = messages

    async def load_conversation(
        self, session_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Load conversation from memory."""
        return self._conversations.get(session_id, {}).get(conversation_id, [])

    async def store_project_context(self, project_path: str, context: Dict[str, Any]) -> None:
        """Store project context in memory."""
        self._contexts[project_path] = context

    async def load_project_context(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load project context from memory."""
        return self._contexts.get(project_path)


class TestStorageInterfaces:
    """Test storage interface compliance and behavior."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage backend."""
        return MockStorageBackend()

    @pytest.mark.asyncio
    async def test_interface_compliance(self, mock_storage):
        """Test that mock storage implements the interface correctly."""
        # Test session operations
        session_id = "test-session"
        session_data = {"test": "data"}

        await mock_storage.store_session(session_id, session_data)
        loaded = await mock_storage.load_session(session_id)
        assert loaded == session_data

        sessions = await mock_storage.list_sessions()
        assert session_id in sessions

        deleted = await mock_storage.delete_session(session_id)
        assert deleted is True

        # Test conversation operations
        messages = [{"role": "user", "content": "hello"}]
        await mock_storage.store_conversation("session", "conv", messages)
        loaded_messages = await mock_storage.load_conversation("session", "conv")
        assert loaded_messages == messages

        # Test context operations
        context = {"vcs": "git"}
        await mock_storage.store_project_context("/path", context)
        loaded_context = await mock_storage.load_project_context("/path")
        assert loaded_context == context

    @pytest.mark.asyncio
    async def test_base_storage_initialization(self):
        """Test base storage backend initialization."""
        # Default initialization
        backend = MockStorageBackend()
        assert backend.base_path == Path.home() / ".mentat"

        # Custom path initialization
        custom_path = Path("/tmp/custom")
        backend = MockStorageBackend(custom_path)
        assert backend.base_path == custom_path

    @pytest.mark.asyncio
    async def test_cleanup_default_implementation(self, mock_storage):
        """Test default cleanup implementation."""
        # Base implementation should return 0
        result = await mock_storage.cleanup_old_sessions(30)
        assert result == 0

    def test_storage_exceptions(self):
        """Test storage exception hierarchy."""
        # Base exception
        error = StorageError("test error")
        assert str(error) == "test error"

        # Specific exceptions
        from mentat.infrastructure.storage.interfaces import (
            ConversationNotFoundError,
            SessionNotFoundError,
        )

        session_error = SessionNotFoundError("session not found")
        assert isinstance(session_error, StorageError)

        conv_error = ConversationNotFoundError("conversation not found")
        assert isinstance(conv_error, StorageError)
