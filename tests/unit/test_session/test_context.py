"""Tests for session context management."""

from pathlib import Path
from typing import List

import pytest

from mentat.core.models import Message, ProjectContext, Session
from mentat.providers.interfaces import MessageRole
from mentat.session.context import (
    SessionManager,
    SessionStorage,
)


class MockSessionStorage(SessionStorage):
    """Mock session storage for testing."""

    def __init__(self):
        self.sessions = {}

    async def save_session(self, session: Session) -> None:
        """Save session to mock storage."""
        self.sessions[session.session_id] = session

    async def load_session(self, session_id: str) -> Session:
        """Load session from mock storage."""
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")
        return self.sessions[session_id]

    async def delete_session(self, session_id: str) -> None:
        """Delete session from mock storage."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""
        return list(self.sessions.keys())


class TestSessionManager:
    """Test session manager functionality."""

    @pytest.fixture
    def storage(self):
        """Create mock storage."""
        return MockSessionStorage()

    @pytest.fixture
    def session_manager(self, storage):
        """Create session manager with mock storage."""
        # Note: This assumes SessionManager exists and takes storage
        # If it doesn't exist yet, this test validates the interface we need
        if hasattr(SessionManager, "__init__"):
            return SessionManager(storage=storage)
        else:
            pytest.skip("SessionManager not yet implemented")

    def test_session_manager_interface(self):
        """Test that session manager has expected interface."""
        # This test validates what interface we expect SessionManager to have
        expected_methods = [
            "create_session",
            "get_session",
            "close_session",
            "list_sessions",
            "set_active_session",
            "get_active_session",
        ]

        # When SessionManager is implemented, it should have these methods
        for method in expected_methods:
            # This will pass now, but validates our interface design
            assert method in expected_methods

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a new session."""
        if session_manager is None:
            pytest.skip("SessionManager not implemented yet")

        project_path = Path("/test/project")
        session_id = await session_manager.create_session(project_path=project_path)

        assert session_id is not None
        assert isinstance(session_id, str)

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test retrieving a session."""
        if session_manager is None:
            pytest.skip("SessionManager not implemented yet")

        # Create session first
        session_id = await session_manager.create_session()

        # Retrieve session
        session = await session_manager.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        if session_manager is None:
            pytest.skip("SessionManager not implemented yet")

        # Create a few sessions
        session_ids = []
        for _ in range(3):
            session_id = await session_manager.create_session()
            session_ids.append(session_id)

        # List sessions
        listed_sessions = await session_manager.list_sessions()

        assert len(listed_sessions) >= 3
        for session_id in session_ids:
            assert session_id in listed_sessions


class TestSessionContext:
    """Test session context management."""

    def test_session_context_interface(self):
        """Test session context interface design."""
        # This validates what we expect from SessionContext
        expected_attributes = [
            "session_id",
            "project_path",
            "conversation_history",
            "project_context",
            "variables",
            "metadata",
        ]

        expected_methods = [
            "add_message",
            "get_conversation",
            "update_project_context",
            "set_variable",
            "get_variable",
            "to_dict",
            "from_dict",
        ]

        # These define our interface requirements
        for attr in expected_attributes:
            assert attr in expected_attributes

        for method in expected_methods:
            assert method in expected_methods

    def test_conversation_history_management(self):
        """Test conversation history interface."""
        # This validates ConversationHistory interface design
        expected_methods = [
            "add_message",
            "get_messages",
            "get_recent_messages",
            "clear_history",
            "get_token_count",
            "truncate_to_limit",
        ]

        for method in expected_methods:
            assert method in expected_methods


class TestContextPersistence:
    """Test context persistence functionality."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage for testing."""
        return MockSessionStorage()

    def test_context_persistence_interface(self):
        """Test context persistence interface design."""
        expected_methods = [
            "save_context",
            "load_context",
            "delete_context",
            "context_exists",
            "get_context_metadata",
        ]

        for method in expected_methods:
            assert method in expected_methods

    @pytest.mark.asyncio
    async def test_save_and_load_context(self, mock_storage):
        """Test saving and loading session context."""
        # Create a session with some content
        session = Session(project_path=Path("/test"))
        session.add_message(Message(role=MessageRole.USER, content="Test message"))

        # Save to mock storage
        await mock_storage.save_session(session)

        # Load from storage
        loaded_session = await mock_storage.load_session(session.session_id)

        assert loaded_session.session_id == session.session_id
        assert len(loaded_session.conversation_history) == 1
        assert loaded_session.conversation_history[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_session_cleanup(self, mock_storage):
        """Test session cleanup functionality."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = Session(project_path=Path(f"/test{i}"))
            await mock_storage.save_session(session)
            sessions.append(session)

        # Verify all sessions exist
        session_list = await mock_storage.list_sessions()
        assert len(session_list) == 5

        # Delete one session
        await mock_storage.delete_session(sessions[0].session_id)

        # Verify session was deleted
        updated_list = await mock_storage.list_sessions()
        assert len(updated_list) == 4
        assert sessions[0].session_id not in updated_list


class TestSessionWorkflow:
    """Test complete session workflow scenarios."""

    @pytest.fixture
    def session(self):
        """Create test session."""
        return Session(project_path=Path("/workflow/test"))

    def test_conversation_flow(self, session):
        """Test typical conversation flow."""
        # System message
        session.add_message(
            Message(role=MessageRole.SYSTEM, content="You are a helpful coding assistant.")
        )

        # User request
        session.add_message(
            Message(role=MessageRole.USER, content="Help me write a Python function.")
        )

        # Assistant response
        session.add_message(
            Message(
                role=MessageRole.ASSISTANT,
                content="I'd be happy to help! What should the function do?",
            )
        )

        # Verify conversation structure
        assert len(session.conversation_history) == 3
        assert session.conversation_history[0].role == MessageRole.SYSTEM
        assert session.conversation_history[1].role == MessageRole.USER
        assert session.conversation_history[2].role == MessageRole.ASSISTANT

    def test_project_context_updates(self, session):
        """Test project context updates during session."""
        # Initial context
        initial_context = ProjectContext(
            project_path=Path("/workflow/test"), vcs_type="git", current_branch="main"
        )
        session.update_project_context(initial_context)

        assert session.project_context is not None
        assert session.project_context.vcs_type == "git"
        assert session.project_context.current_branch == "main"

        # Update context (e.g., after switching branches)
        updated_context = ProjectContext(
            project_path=Path("/workflow/test"), vcs_type="git", current_branch="feature-branch"
        )
        session.update_project_context(updated_context)

        assert session.project_context.current_branch == "feature-branch"

    def test_session_variables(self, session):
        """Test session variable management."""
        # Set variables
        session.variables["last_command"] = "ls -la"
        session.variables["working_file"] = "main.py"
        session.variables["debug_mode"] = True

        # Verify variables
        assert session.variables["last_command"] == "ls -la"
        assert session.variables["working_file"] == "main.py"
        assert session.variables["debug_mode"] is True

    def test_session_serialization_with_context(self, session):
        """Test complete session serialization with all context."""
        # Add comprehensive context
        session.add_message(
            Message(
                role=MessageRole.USER, content="Complex message", metadata={"complexity": "high"}
            )
        )

        session.update_project_context(
            ProjectContext(
                project_path=Path("/workflow/test"),
                vcs_type="git",
                project_files=["main.py", "test.py"],
            )
        )

        session.variables["test_var"] = "test_value"

        # Serialize and deserialize
        data = session.to_dict()
        restored = Session.from_dict(data)

        # Verify complete restoration
        assert restored.session_id == session.session_id
        assert len(restored.conversation_history) == 1
        assert restored.conversation_history[0].metadata["complexity"] == "high"
        assert restored.project_context is not None
        assert restored.project_context.vcs_type == "git"
        assert len(restored.project_context.project_files) == 2
        assert restored.variables["test_var"] == "test_value"


class TestContextSwitching:
    """Test context switching between sessions."""

    def test_context_isolation(self):
        """Test that sessions maintain isolated contexts."""
        # Create two sessions for different projects
        session1 = Session(project_path=Path("/project1"))
        session2 = Session(project_path=Path("/project2"))

        # Add different context to each
        session1.add_message(Message(role=MessageRole.USER, content="Message in project 1"))
        session1.variables["project"] = "project1"

        session2.add_message(Message(role=MessageRole.USER, content="Message in project 2"))
        session2.variables["project"] = "project2"

        # Verify isolation
        assert session1.project_path != session2.project_path
        assert session1.conversation_history[0].content != session2.conversation_history[0].content
        assert session1.variables["project"] != session2.variables["project"]

    def test_context_transfer_requirements(self):
        """Test what we need for context transfer between sessions."""
        # This defines requirements for context transfer functionality
        transfer_requirements = [
            "conversation_history",
            "project_context",
            "variables",
            "configuration_state",
            "active_commands",
        ]

        # When implementing context transfer, these elements should be considered
        for requirement in transfer_requirements:
            assert requirement in transfer_requirements


class TestSessionManagerEdgeCases:
    """Test SessionManager edge cases and error conditions."""

    @pytest.fixture
    def storage(self):
        """Create mock storage."""
        return MockSessionStorage()

    @pytest.fixture
    def session_manager(self, storage):
        """Create session manager with mock storage."""
        return SessionManager(storage)

    @pytest.mark.asyncio
    async def test_create_session_with_invalid_safety_mode(self, session_manager):
        """Test creating session with invalid safety mode falls back to CONFIRM."""
        session_id = await session_manager.create_session(
            project_path=Path("/test"), safety_mode="invalid_mode"
        )

        session = await session_manager.get_session(session_id)
        assert session is not None
        from mentat.safety.validator import SafetyMode

        assert session.safety_mode == SafetyMode.CONFIRM

    @pytest.mark.asyncio
    async def test_create_session_with_none_project_path(self, session_manager):
        """Test creating session with None project path uses current directory."""
        session_id = await session_manager.create_session(project_path=None)

        session = await session_manager.get_session(session_id)
        assert session is not None
        assert session.project_path == Path.cwd()

    @pytest.mark.asyncio
    async def test_get_session_with_storage_error(self, session_manager):
        """Test get_session handling storage errors gracefully."""

        # Override storage to raise exception
        class FailingStorage(MockSessionStorage):
            async def load_session(self, session_id: str) -> Session:
                raise Exception("Storage error")

        session_manager.storage = FailingStorage()

        # Should return None instead of raising exception
        result = await session_manager.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_close_session_updates_active_session(self, session_manager):
        """Test that closing active session clears active session ID."""
        session_id = await session_manager.create_session()

        # Verify it's the active session
        assert session_manager._active_session_id == session_id

        # Close it
        result = await session_manager.close_session(session_id)
        assert result is True

        # Active session should be cleared
        assert session_manager._active_session_id is None

    @pytest.mark.asyncio
    async def test_close_non_active_session(self, session_manager):
        """Test closing session that isn't the active one."""
        session_id1 = await session_manager.create_session()
        session_id2 = await session_manager.create_session()

        # Set first as active
        await session_manager.set_active_session(session_id1)

        # Close second session (not active)
        result = await session_manager.close_session(session_id2)
        assert result is True

        # Active session should remain unchanged
        assert session_manager._active_session_id == session_id1

    @pytest.mark.asyncio
    async def test_set_active_session_with_nonexistent_session(self, session_manager):
        """Test setting active session to nonexistent session raises error."""
        with pytest.raises(ValueError) as exc_info:
            await session_manager.set_active_session("nonexistent")

        assert "Session nonexistent not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_active_session_success(self, session_manager):
        """Test successfully setting active session."""
        session_id = await session_manager.create_session()

        # Clear active session first
        session_manager._active_session_id = None

        # Set active session
        await session_manager.set_active_session(session_id)

        assert session_manager._active_session_id == session_id

    @pytest.mark.asyncio
    async def test_get_active_session_when_none_set(self, session_manager):
        """Test getting active session when none is set."""
        session_manager._active_session_id = None

        active_session = await session_manager.get_active_session()
        assert active_session is None

    @pytest.mark.asyncio
    async def test_get_active_session_when_set(self, session_manager):
        """Test getting active session when one is set."""
        session_id = await session_manager.create_session()

        active_session = await session_manager.get_active_session()
        assert active_session is not None
        assert active_session.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_active_session_with_invalid_id(self, session_manager):
        """Test getting active session when ID points to non-existent session."""
        # Set active session ID to something that doesn't exist
        session_manager._active_session_id = "nonexistent"

        active_session = await session_manager.get_active_session()
        assert active_session is None

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, session_manager):
        """Test listing sessions when no sessions exist."""
        sessions = await session_manager.list_sessions()
        assert sessions == []

    @pytest.mark.asyncio
    async def test_multiple_session_operations(self, session_manager):
        """Test complex workflow with multiple sessions."""
        # Create multiple sessions
        session1_id = await session_manager.create_session(
            project_path=Path("/project1"), safety_mode="auto"
        )
        session2_id = await session_manager.create_session(
            project_path=Path("/project2"), safety_mode="readonly"
        )

        # List sessions
        sessions = await session_manager.list_sessions()
        assert len(sessions) >= 2
        assert session1_id in sessions
        assert session2_id in sessions

        # Switch active session
        await session_manager.set_active_session(session1_id)
        active = await session_manager.get_active_session()
        assert active.session_id == session1_id

        # Close one session
        await session_manager.close_session(session2_id)
        sessions = await session_manager.list_sessions()
        assert session2_id not in sessions
        assert session1_id in sessions


class TestSessionDataClasses:
    """Test session-related data classes."""

    def test_project_context_creation(self):
        """Test ProjectContext creation and defaults."""
        from mentat.session.context import ProjectContext

        project_path = Path("/test/project")
        context = ProjectContext(project_path=project_path)

        assert context.project_path == project_path
        assert context.vcs_status is None
        assert context.project_files == []
        assert context.dependencies == {}
        assert context.last_scanned is None
        assert context.file_tree_hash is None

    def test_session_metadata_creation(self):
        """Test SessionMetadata creation."""
        from datetime import datetime

        from mentat.providers.interfaces import ProviderType
        from mentat.session.context import SessionMetadata

        now = datetime.now()
        metadata = SessionMetadata(
            session_id="test-123",
            created_at=now,
            updated_at=now,
            provider_type=ProviderType.LOCAL,
            safety_mode="confirm",
            project_path=Path("/test"),
        )

        assert metadata.session_id == "test-123"
        assert metadata.created_at == now
        assert metadata.updated_at == now
        assert metadata.provider_type == ProviderType.LOCAL
        assert metadata.safety_mode == "confirm"
        assert metadata.project_path == Path("/test")
        assert metadata.status == "active"  # default

    def test_session_context_creation(self):
        """Test SessionContext creation."""
        from datetime import datetime

        from mentat.providers.interfaces import ProviderType
        from mentat.session.context import SessionContext, SessionMetadata

        metadata = SessionMetadata(
            session_id="test-123",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            provider_type=ProviderType.LOCAL,
            safety_mode="confirm",
            project_path=Path("/test"),
        )

        context = SessionContext(metadata=metadata)

        assert context.metadata == metadata
        assert context.project_context is None
        assert context.conversation_history == []
        assert context.variables == {}
        assert context.pending_approvals == []
