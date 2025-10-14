"""Additional tests for refactored core model methods to improve coverage."""

from datetime import datetime
from pathlib import Path

from mentat.core.models import (
    Command,
    CommandSource,
    CommandStatus,
    Message,
    Session,
    SessionStatus,
)
from mentat.providers.interfaces import MessageRole, ProviderType
from mentat.safety.validator import SafetyMode


class TestRefactoredModelMethods:
    """Test the new helper methods created during complexity refactoring."""

    def test_message_convert_role_to_enum_with_invalid_string(self):
        """Test _convert_role_to_enum with invalid string role."""
        message = Message()

        # Test with invalid role string - should default to USER
        result = message._convert_role_to_enum("invalid_role")
        assert result == MessageRole.USER

    def test_message_convert_role_to_enum_with_enum(self):
        """Test _convert_role_to_enum with MessageRole enum input."""
        message = Message()

        # Test with enum input - should return as-is
        result = message._convert_role_to_enum(MessageRole.ASSISTANT)
        assert result == MessageRole.ASSISTANT

    def test_message_apply_defaults_partial_kwargs(self):
        """Test _apply_message_defaults with some fields already provided."""
        message = Message()

        # Provide some fields, let others default
        kwargs = {"message_id": "test123", "content": "test message"}

        result = message._apply_message_defaults(kwargs)

        # Should preserve provided fields
        assert result["message_id"] == "test123"
        assert result["content"] == "test message"

        # Should add default fields
        assert result["role"] == MessageRole.USER
        assert result["metadata"] == {}
        assert result["command_requests"] == []

    def test_command_apply_default_values_partial_kwargs(self):
        """Test _apply_default_values with some fields already provided."""
        command = Command()

        # Provide some fields, let others default
        kwargs = {"command_text": "ls -la", "risk_level": "high"}

        result = command._apply_default_values(kwargs)

        # Should preserve provided fields
        assert result["command_text"] == "ls -la"
        assert result["risk_level"] == "high"

        # Should add default fields
        assert result["source"] == CommandSource.USER
        assert result["approval_status"] == CommandStatus.PENDING
        assert result["parsed_args"] == []

    def test_session_normalize_session_types_path_conversion(self):
        """Test _normalize_session_types converts string path to Path object."""
        session = Session()

        kwargs = {"project_path": "home/user/project"}

        result = session._normalize_session_types(kwargs)

        assert isinstance(result["project_path"], Path)
        assert "project" in str(result["project_path"])

    def test_session_normalize_session_types_path_already_path(self):
        """Test _normalize_session_types with Path object already provided."""
        session = Session()

        original_path = Path("/home/user/project")
        kwargs = {"project_path": original_path}

        result = session._normalize_session_types(kwargs)

        # Should not modify if already Path object
        assert result["project_path"] is original_path

    def test_session_serialize_message_with_session_id(self):
        """Test _serialize_message_with_session_id includes session_id."""
        session = Session()
        message = Message(
            message_id="msg123", role=MessageRole.USER, content="test", session_id="sess456"
        )

        result = session._serialize_message_with_session_id(message)

        # Should include session_id and id alias
        assert result["session_id"] == "sess456"
        assert result["id"] == "msg123"
        assert result["message_id"] == "msg123"

    def test_session_serialize_command_detailed_vs_basic(self):
        """Test difference between detailed and basic command serialization."""
        session = Session()
        command = Command(command_text="ls -la", command_id="cmd123", session_id="sess456")

        detailed = session._serialize_command_detailed(command)
        basic = session._serialize_command_basic(command)

        # Detailed should have extra fields
        assert "id" in detailed  # alias
        assert "text" in detailed  # alias
        assert "status" in detailed  # alias
        assert "session_id" in detailed
        assert "source" in detailed
        assert "timestamp" in detailed

        # Basic should not have these fields
        assert "id" not in basic
        assert "text" not in basic
        assert "status" not in basic
        assert "session_id" not in basic
        assert "source" not in basic
        assert "timestamp" not in basic

        # Both should have core fields
        assert detailed["command_id"] == "cmd123"
        assert basic["command_id"] == "cmd123"

    def test_session_serialize_core_fields_formatting(self):
        """Test _serialize_core_fields with various data types."""
        session = Session(
            session_id="test123",
            project_path=Path("/home/user/project"),
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            provider_type=ProviderType.OPENAI,
            safety_mode=SafetyMode.CONFIRM,
            status=SessionStatus.ACTIVE,
        )

        result = session._serialize_core_fields()

        # Check proper formatting
        assert result["session_id"] == "test123"
        assert result["id"] == "test123"  # alias
        assert "/" in result["project_path"]  # normalized path separators
        assert result["created_at"] == "2023-01-01T12:00:00"  # ISO format
        assert result["provider_type"] == "openai"  # enum value
        assert result["safety_mode"] == "confirm"  # enum value
        assert result["status"] == "active"  # enum value

    def test_session_serialize_project_context_none(self):
        """Test _serialize_project_context when project_context is None."""
        session = Session()
        session.project_context = None

        result = session._serialize_project_context()

        assert result == {"project_context": None}

    def test_session_serialize_messages_empty_conversation(self):
        """Test _serialize_messages with empty conversation history."""
        session = Session()
        session.conversation_history = []

        result = session._serialize_messages()

        assert result["messages"] == []
        assert result["conversation_history"] == []

    def test_session_serialize_commands_empty_pending(self):
        """Test _serialize_commands with empty pending commands."""
        session = Session()
        session.pending_commands = []

        result = session._serialize_commands()

        assert result["commands"] == []
        assert result["pending_commands"] == []
