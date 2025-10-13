"""Tests for core data models."""

from datetime import datetime, timezone
from pathlib import Path

from mentat.core.models import (
    Command,
    CommandSource,
    CommandStatus,
    Message,
    ProjectContext,
    Session,
    SessionStatus,
)


class TestSessionModel:
    """Test Session data model."""

    def test_session_creation(self):
        """Test basic session creation."""
        session = Session(id="test_session_123", project_path="/path/to/project")

        assert session.id == "test_session_123"
        assert session.project_path == Path("/path/to/project")
        assert session.status == SessionStatus.ACTIVE
        assert session.created_at is not None
        assert session.updated_at is not None
        assert len(session.messages) == 0
        assert len(session.commands) == 0

    def test_session_with_metadata(self):
        """Test session with metadata."""
        metadata = {
            "user": "test_user",
            "environment": "development",
            "tags": ["feature", "testing"],
        }

        session = Session(id="session_with_meta", project_path="/project", metadata=metadata)

        assert session.metadata == metadata
        assert session.metadata["user"] == "test_user"
        assert "feature" in session.metadata["tags"]

    def test_session_status_transitions(self):
        """Test session status changes."""
        session = Session(id="status_test", project_path="/project")

        # Start active
        assert session.status == SessionStatus.ACTIVE

        # Pause session
        session.status = SessionStatus.PAUSED
        assert session.status == SessionStatus.PAUSED

        # Complete session
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED

    def test_add_message(self):
        """Test adding messages to session."""
        session = Session(id="msg_test", project_path="/project")

        message = Message(role="user", content="Hello, world!", session_id=session.id)

        session.add_message(message)

        assert len(session.messages) == 1
        assert session.messages[0] == message
        assert session.messages[0].session_id == session.id

    def test_add_command(self):
        """Test adding commands to session."""
        session = Session(id="cmd_test", project_path="/project")

        command = Command(text="ls -la", source=CommandSource.USER, session_id=session.id)

        session.add_command(command)

        assert len(session.commands) == 1
        assert session.commands[0] == command
        assert session.commands[0].session_id == session.id

    def test_session_serialization(self):
        """Test session serialization to dict."""
        session = Session(id="serial_test", project_path="/project", metadata={"test": "value"})

        # Add a message
        message = Message(role="user", content="Test message", session_id=session.id)
        session.add_message(message)

        # Serialize
        data = session.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "serial_test"
        assert data["project_path"] == "/project"
        assert data["status"] == SessionStatus.ACTIVE.value
        assert data["metadata"]["test"] == "value"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Test message"

    def test_session_deserialization(self):
        """Test session deserialization from dict."""
        data = {
            "id": "deserial_test",
            "project_path": "/test/project",
            "status": "active",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:30:00Z",
            "metadata": {"source": "test"},
            "messages": [
                {
                    "id": "msg_1",
                    "role": "user",
                    "content": "Test content",
                    "session_id": "deserial_test",
                    "timestamp": "2023-01-01T12:00:00Z",
                }
            ],
            "commands": [],
        }

        session = Session.from_dict(data)

        assert session.id == "deserial_test"
        assert session.project_path == Path("/test/project")
        assert session.status == SessionStatus.ACTIVE
        assert session.metadata["source"] == "test"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Test content"

    def test_get_conversation_history(self):
        """Test getting conversation history."""
        session = Session(id="history_test", project_path="/project")

        # Add messages
        messages = [
            Message(role="system", content="System prompt", session_id=session.id),
            Message(role="user", content="User message 1", session_id=session.id),
            Message(role="assistant", content="Assistant response 1", session_id=session.id),
            Message(role="user", content="User message 2", session_id=session.id),
        ]

        for msg in messages:
            session.add_message(msg)

        # Get history
        history = session.get_conversation_history()

        assert len(history) == 4
        assert history[0].role == "system"
        assert history[-1].content == "User message 2"

    def test_get_conversation_history_limit(self):
        """Test conversation history with limit."""
        session = Session(id="limit_test", project_path="/project")

        # Add many messages
        for i in range(10):
            session.add_message(
                Message(
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i}",
                    session_id=session.id,
                )
            )

        # Get limited history
        history = session.get_conversation_history(limit=3)

        assert len(history) == 3
        # Should get the most recent messages
        assert "Message 7" in history[0].content
        assert "Message 9" in history[-1].content

    def test_session_statistics(self):
        """Test session statistics."""
        session = Session(id="stats_test", project_path="/project")

        # Add various messages and commands
        session.add_message(Message(role="user", content="User msg", session_id=session.id))
        session.add_message(
            Message(role="assistant", content="Assistant msg", session_id=session.id)
        )
        session.add_command(Command(text="ls", source=CommandSource.USER, session_id=session.id))

        stats = session.get_statistics()

        assert stats["message_count"] == 2
        assert stats["command_count"] == 1
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1


class TestMessageModel:
    """Test Message data model."""

    def test_message_creation(self):
        """Test basic message creation."""
        message = Message(role="user", content="Hello, AI!", session_id="session_123")

        assert message.role == "user"
        assert message.content == "Hello, AI!"
        assert message.session_id == "session_123"
        assert message.timestamp is not None
        assert message.id is not None

    def test_message_with_metadata(self):
        """Test message with metadata."""
        metadata = {"source": "cli", "command_context": True, "tokens": 50}

        message = Message(
            role="assistant",
            content="Response from AI",
            session_id="session_123",
            metadata=metadata,
        )

        assert message.metadata == metadata
        assert message.metadata["source"] == "cli"
        assert message.metadata["tokens"] == 50

    def test_message_serialization(self):
        """Test message serialization."""
        message = Message(
            role="user", content="Serialize me", session_id="session_test", metadata={"test": True}
        )

        data = message.to_dict()

        assert isinstance(data, dict)
        assert data["role"] == "user"
        assert data["content"] == "Serialize me"
        assert data["session_id"] == "session_test"
        assert data["metadata"]["test"] is True
        assert "timestamp" in data
        assert "id" in data

    def test_message_deserialization(self):
        """Test message deserialization."""
        data = {
            "id": "msg_123",
            "role": "assistant",
            "content": "Deserialized message",
            "session_id": "session_456",
            "timestamp": "2023-01-01T12:00:00Z",
            "metadata": {"source": "test"},
        }

        message = Message.from_dict(data)

        assert message.id == "msg_123"
        assert message.role == "assistant"
        assert message.content == "Deserialized message"
        assert message.session_id == "session_456"
        assert message.metadata["source"] == "test"

    def test_message_token_estimation(self):
        """Test message token count estimation."""
        message = Message(
            role="user",
            content="This is a message with several words for token counting",
            session_id="token_test",
        )

        # Should have method to estimate tokens
        if hasattr(message, "estimate_tokens"):
            tokens = message.estimate_tokens()
            assert isinstance(tokens, int)
            assert tokens > 0

    def test_message_role_validation(self):
        """Test message role validation."""
        valid_roles = ["system", "user", "assistant"]

        for role in valid_roles:
            message = Message(role=role, content="Test content", session_id="role_test")
            assert message.role == role

    def test_message_content_types(self):
        """Test different message content types."""
        # Text content
        text_message = Message(role="user", content="Text message", session_id="content_test")
        assert isinstance(text_message.content, str)

        # Long content
        long_content = "x" * 10000
        long_message = Message(role="assistant", content=long_content, session_id="content_test")
        assert len(long_message.content) == 10000


class TestCommandModel:
    """Test Command data model."""

    def test_command_creation(self):
        """Test basic command creation."""
        command = Command(text="ls -la", source=CommandSource.USER, session_id="cmd_session")

        assert command.text == "ls -la"
        assert command.source == CommandSource.USER
        assert command.session_id == "cmd_session"
        assert command.status == CommandStatus.PENDING
        assert command.timestamp is not None
        assert command.id is not None

    def test_command_execution_flow(self):
        """Test command execution status flow."""
        command = Command(text="echo 'hello'", source=CommandSource.AI, session_id="exec_test")

        # Start pending
        assert command.status == CommandStatus.PENDING

        # Mark as running
        command.status = CommandStatus.RUNNING
        assert command.status == CommandStatus.RUNNING

        # Complete successfully
        command.status = CommandStatus.COMPLETED
        command.output = "hello"
        command.exit_code = 0

        assert command.status == CommandStatus.COMPLETED
        assert command.output == "hello"
        assert command.exit_code == 0

    def test_command_with_error(self):
        """Test command with execution error."""
        command = Command(
            text="invalid_command", source=CommandSource.USER, session_id="error_test"
        )

        command.status = CommandStatus.FAILED
        command.error = "Command not found"
        command.exit_code = 127

        assert command.status == CommandStatus.FAILED
        assert command.error == "Command not found"
        assert command.exit_code == 127

    def test_command_serialization(self):
        """Test command serialization."""
        command = Command(
            text="git status",
            source=CommandSource.AI,
            session_id="serialize_test",
            metadata={"suggested_by": "assistant"},
        )
        command.output = "On branch main"
        command.exit_code = 0

        data = command.to_dict()

        assert isinstance(data, dict)
        assert data["text"] == "git status"
        assert data["source"] == CommandSource.AI.value
        assert data["output"] == "On branch main"
        assert data["exit_code"] == 0
        assert data["metadata"]["suggested_by"] == "assistant"

    def test_command_deserialization(self):
        """Test command deserialization."""
        data = {
            "id": "cmd_123",
            "text": "ls -la",
            "source": "user",
            "status": "completed",
            "session_id": "session_789",
            "timestamp": "2023-01-01T12:00:00Z",
            "output": "total 8\ndrwxr-xr-x 2 user user 4096 Jan  1 12:00 .",
            "exit_code": 0,
            "metadata": {},
        }

        command = Command.from_dict(data)

        assert command.id == "cmd_123"
        assert command.text == "ls -la"
        assert command.source == CommandSource.USER
        assert command.status == CommandStatus.COMPLETED
        assert command.exit_code == 0

    def test_command_duration_tracking(self):
        """Test command execution duration tracking."""
        command = Command(text="sleep 1", source=CommandSource.USER, session_id="duration_test")

        # Should have start/end time tracking
        if hasattr(command, "started_at") and hasattr(command, "completed_at"):
            command.started_at = datetime.now(timezone.utc)
            # Simulate execution time
            command.completed_at = datetime.now(timezone.utc)

            duration = command.get_duration()
            assert isinstance(duration, (int, float))
            assert duration >= 0


class TestProjectContextModel:
    """Test ProjectContext data model."""

    def test_project_context_creation(self):
        """Test basic project context creation."""
        context = ProjectContext(path="/path/to/project", name="test_project")

        assert context.path == Path("/path/to/project")
        assert context.name == "test_project"
        assert context.created_at is not None
        assert context.updated_at is not None
        assert len(context.files) == 0
        assert context.metadata == {}

    def test_project_context_with_files(self):
        """Test project context with tracked files."""
        context = ProjectContext(path="/project", name="file_test")

        files = [
            {"path": "src/main.py", "size": 1024, "modified": "2023-01-01T12:00:00Z"},
            {"path": "README.md", "size": 512, "modified": "2023-01-01T11:00:00Z"},
        ]

        context.files = files

        assert len(context.files) == 2
        assert context.files[0]["path"] == "src/main.py"
        assert context.files[1]["size"] == 512

    def test_project_context_git_info(self):
        """Test project context with Git information."""
        git_info = {
            "current_branch": "feature/new-feature",
            "uncommitted_changes": 3,
            "last_commit": "abc123",
            "remote_url": "https://github.com/user/repo.git",
        }

        context = ProjectContext(path="/git/project", name="git_test", git_info=git_info)

        assert context.git_info == git_info
        assert context.git_info["current_branch"] == "feature/new-feature"
        assert context.git_info["uncommitted_changes"] == 3

    def test_project_context_serialization(self):
        """Test project context serialization."""
        context = ProjectContext(
            path="/serialize/project",
            name="serialize_test",
            description="Test project for serialization",
            metadata={"language": "python", "version": "3.12"},
        )

        data = context.to_dict()

        assert isinstance(data, dict)
        assert data["path"] == "/serialize/project"
        assert data["name"] == "serialize_test"
        assert data["description"] == "Test project for serialization"
        assert data["metadata"]["language"] == "python"

    def test_project_context_deserialization(self):
        """Test project context deserialization."""
        data = {
            "path": "/deserialize/project",
            "name": "deserialize_test",
            "description": "Deserialized project",
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "files": [{"path": "main.py", "size": 2048}],
            "git_info": {"current_branch": "main"},
            "metadata": {"type": "library"},
        }

        context = ProjectContext.from_dict(data)

        assert context.path == Path("/deserialize/project")
        assert context.name == "deserialize_test"
        assert context.description == "Deserialized project"
        assert len(context.files) == 1
        assert context.git_info["current_branch"] == "main"
        assert context.metadata["type"] == "library"


class TestModelRelationships:
    """Test relationships between models."""

    def test_session_message_relationship(self):
        """Test session-message relationship."""
        session = Session(id="relationship_test", project_path="/project")

        messages = [
            Message(role="user", content="Message 1", session_id=session.id),
            Message(role="assistant", content="Response 1", session_id=session.id),
            Message(role="user", content="Message 2", session_id=session.id),
        ]

        for msg in messages:
            session.add_message(msg)

        # All messages should belong to session
        for msg in session.messages:
            assert msg.session_id == session.id

        # Session should contain all messages
        assert len(session.messages) == 3

    def test_session_command_relationship(self):
        """Test session-command relationship."""
        session = Session(id="cmd_relationship", project_path="/project")

        commands = [
            Command(text="ls", source=CommandSource.USER, session_id=session.id),
            Command(text="pwd", source=CommandSource.AI, session_id=session.id),
        ]

        for cmd in commands:
            session.add_command(cmd)

        # All commands should belong to session
        for cmd in session.commands:
            assert cmd.session_id == session.id

        # Session should contain all commands
        assert len(session.commands) == 2

    def test_cross_model_serialization(self):
        """Test serialization of models with relationships."""
        session = Session(id="cross_serial", project_path="/project")

        # Add message and command
        session.add_message(Message(role="user", content="Run ls command", session_id=session.id))
        session.add_command(
            Command(text="ls -la", source=CommandSource.USER, session_id=session.id)
        )

        # Serialize entire session
        data = session.to_dict()

        # Verify all relationships are preserved
        assert len(data["messages"]) == 1
        assert len(data["commands"]) == 1
        assert data["messages"][0]["session_id"] == session.id
        assert data["commands"][0]["session_id"] == session.id

        # Deserialize and verify
        restored_session = Session.from_dict(data)
        assert len(restored_session.messages) == 1
        assert len(restored_session.commands) == 1
        assert restored_session.messages[0].session_id == session.id
