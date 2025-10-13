"""Tests for core data models - matching actual implementation."""

from pathlib import Path

from mentat.core.models import (
    Command,
    CommandStatus,
    Configuration,
    Message,
    ProjectContext,
    Session,
    SessionStatus,
)
from mentat.providers.interfaces import MessageRole, ProviderType
from mentat.safety.validator import SafetyMode
from mentat.vcs.interfaces import VCSStatus


class TestSessionModel:
    """Test Session data model."""

    def test_session_creation_defaults(self):
        """Test session creation with defaults."""
        session = Session()

        assert session.session_id is not None
        assert isinstance(session.session_id, str)
        assert session.project_path == Path.cwd()
        assert session.status == SessionStatus.ACTIVE
        assert session.provider_type == ProviderType.OPENAI
        assert session.safety_mode == SafetyMode.CONFIRM
        assert session.created_at is not None
        assert session.updated_at is not None
        assert len(session.conversation_history) == 0
        assert len(session.pending_commands) == 0
        assert session.project_context is None

    def test_session_creation_with_params(self):
        """Test session creation with parameters."""
        project_path = Path("/test/project")
        session = Session(
            project_path=project_path,
            provider_type=ProviderType.ANTHROPIC,
            safety_mode=SafetyMode.READONLY,
        )

        assert session.project_path == project_path
        assert session.provider_type == ProviderType.ANTHROPIC
        assert session.safety_mode == SafetyMode.READONLY

    def test_add_message(self):
        """Test adding messages to session."""
        session = Session()

        message = Message(role=MessageRole.USER, content="Hello, world!")

        initial_updated = session.updated_at
        session.add_message(message)

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0] == message
        assert session.updated_at > initial_updated
        assert session.context_size > 0

    def test_add_command(self):
        """Test adding commands to session."""
        session = Session()

        command = Command(command_text="ls -la")

        session.add_command(command)

        assert len(session.pending_commands) == 1
        assert session.pending_commands[0] == command
        assert session.pending_commands[0].session_id == session.session_id

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        session = Session()

        # Add multiple messages
        messages = [Message(role=MessageRole.USER, content=f"Message {i}") for i in range(5)]

        for msg in messages:
            session.add_message(msg)

        # Get recent messages
        recent = session.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"  # Last 3 messages
        assert recent[-1].content == "Message 4"

    def test_get_pending_commands(self):
        """Test getting pending commands."""
        session = Session()

        # Add commands with different statuses
        cmd1 = Command(command_text="ls", approval_status=CommandStatus.PENDING)
        cmd2 = Command(command_text="pwd", approval_status=CommandStatus.EXECUTED)
        cmd3 = Command(command_text="date", approval_status=CommandStatus.PENDING)

        session.add_command(cmd1)
        session.add_command(cmd2)
        session.add_command(cmd3)

        pending = session.get_pending_commands()
        assert len(pending) == 2
        assert cmd1 in pending
        assert cmd3 in pending
        assert cmd2 not in pending

    def test_update_project_context(self):
        """Test updating project context."""
        session = Session()
        context = ProjectContext(project_path=Path("/test"))

        session.update_project_context(context)

        assert session.project_context == context

    def test_session_serialization(self):
        """Test session serialization."""
        session = Session(project_path=Path("/test/project"))

        # Add some data
        session.add_message(Message(role=MessageRole.USER, content="Test message"))
        session.add_command(Command(command_text="test command"))

        data = session.to_dict()

        assert isinstance(data, dict)
        assert data["session_id"] == session.session_id
        assert data["project_path"] == "/test/project"
        assert data["status"] == SessionStatus.ACTIVE.value
        assert len(data["conversation_history"]) == 1
        assert len(data["pending_commands"]) == 1

    def test_session_deserialization(self):
        """Test session deserialization."""
        # Create original session
        original = Session(project_path=Path("/original"))
        original.add_message(Message(role=MessageRole.USER, content="Original message"))

        # Serialize and deserialize
        data = original.to_dict()
        restored = Session.from_dict(data)

        assert restored.session_id == original.session_id
        assert restored.project_path == original.project_path
        assert len(restored.conversation_history) == 1
        assert restored.conversation_history[0].content == "Original message"


class TestMessageModel:
    """Test Message data model."""

    def test_message_creation_defaults(self):
        """Test message creation with defaults."""
        message = Message()

        assert message.message_id is not None
        assert isinstance(message.message_id, str)
        assert message.role == MessageRole.USER
        assert message.content == ""
        assert message.timestamp is not None
        assert isinstance(message.metadata, dict)
        assert len(message.metadata) == 0
        assert len(message.command_requests) == 0

    def test_message_creation_with_params(self):
        """Test message creation with parameters."""
        metadata = {"source": "test", "tokens": 50}
        command_requests = ["ls", "pwd"]

        message = Message(
            role=MessageRole.ASSISTANT,
            content="Test response",
            metadata=metadata,
            command_requests=command_requests,
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Test response"
        assert message.metadata == metadata
        assert message.command_requests == command_requests

    def test_message_roles(self):
        """Test different message roles."""
        roles = [MessageRole.SYSTEM, MessageRole.USER, MessageRole.ASSISTANT]

        for role in roles:
            message = Message(role=role, content=f"Content for {role.value}")
            assert message.role == role


class TestCommandModel:
    """Test Command data model."""

    def test_command_creation_defaults(self):
        """Test command creation with defaults."""
        command = Command()

        assert command.command_id is not None
        assert isinstance(command.command_id, str)
        assert command.session_id == ""
        assert command.command_text == ""
        assert command.approval_status == CommandStatus.PENDING
        assert command.risk_level == "low"
        assert len(command.parsed_args) == 0
        assert command.exit_code is None

    def test_command_creation_with_params(self):
        """Test command creation with parameters."""
        command = Command(command_text="ls -la", parsed_args=["ls", "-la"], risk_level="medium")

        assert command.command_text == "ls -la"
        assert command.parsed_args == ["ls", "-la"]
        assert command.risk_level == "medium"

    def test_mark_executed_success(self):
        """Test marking command as successfully executed."""
        command = Command(command_text="echo hello")

        command.mark_executed(0, "hello", "")

        assert command.approval_status == CommandStatus.EXECUTED
        assert command.exit_code == 0
        assert command.output == "hello"
        assert command.error_output == ""
        assert command.executed_at is not None

    def test_mark_executed_failure(self):
        """Test marking command as failed."""
        command = Command(command_text="invalid_command")

        command.mark_executed(127, "", "command not found")

        assert command.approval_status == CommandStatus.FAILED
        assert command.exit_code == 127
        assert command.output == ""
        assert command.error_output == "command not found"

    def test_command_status_transitions(self):
        """Test command status transitions."""
        command = Command()

        # Start pending
        assert command.approval_status == CommandStatus.PENDING

        # Can approve
        command.approval_status = CommandStatus.APPROVED
        assert command.approval_status == CommandStatus.APPROVED

        # Can deny
        command.approval_status = CommandStatus.DENIED
        assert command.approval_status == CommandStatus.DENIED


class TestProjectContextModel:
    """Test ProjectContext data model."""

    def test_project_context_creation(self):
        """Test project context creation."""
        path = Path("/test/project")
        context = ProjectContext(project_path=path)

        assert context.project_path == path
        assert context.vcs_type == "none"
        assert context.current_branch is None
        assert context.uncommitted_changes == 0
        assert context.untracked_files == 0
        assert len(context.project_files) == 0
        assert len(context.dependencies) == 0

    def test_project_context_with_vcs(self):
        """Test project context with VCS information."""
        context = ProjectContext(
            project_path=Path("/git/project"),
            vcs_type="git",
            current_branch="main",
            uncommitted_changes=3,
        )

        assert context.vcs_type == "git"
        assert context.current_branch == "main"
        assert context.uncommitted_changes == 3

    def test_update_from_vcs_status(self):
        """Test updating context from VCS status."""
        context = ProjectContext(project_path=Path("/project"))

        vcs_status = VCSStatus(
            current_branch="feature-branch",
            uncommitted_changes=5,
            untracked_files=2,
            is_clean=False,
        )

        context.update_from_vcs_status(vcs_status)

        assert context.vcs_status == vcs_status
        assert context.current_branch == "feature-branch"
        assert context.uncommitted_changes == 5
        assert context.untracked_files == 2


class TestConfigurationModel:
    """Test Configuration data model."""

    def test_configuration_creation_defaults(self):
        """Test configuration creation with defaults."""
        config = Configuration()

        assert config.config_id is not None
        assert isinstance(config.global_config, dict)
        assert isinstance(config.project_config, dict)
        assert isinstance(config.runtime_overrides, dict)
        assert config.provider_type == ProviderType.OPENAI
        assert config.safety_mode == SafetyMode.CONFIRM

    def test_configuration_with_values(self):
        """Test configuration with custom values."""
        global_config = {"theme": "dark", "max_tokens": 1000}
        project_config = {"max_tokens": 2000, "model": "gpt-4"}
        runtime_overrides = {"temperature": 0.8}

        config = Configuration(
            global_config=global_config,
            project_config=project_config,
            runtime_overrides=runtime_overrides,
            provider_type=ProviderType.ANTHROPIC,
        )

        assert config.global_config == global_config
        assert config.project_config == project_config
        assert config.runtime_overrides == runtime_overrides
        assert config.provider_type == ProviderType.ANTHROPIC

    def test_get_effective_config(self):
        """Test getting effective configuration with precedence."""
        config = Configuration(
            global_config={"theme": "dark", "max_tokens": 1000},
            project_config={"max_tokens": 2000, "model": "gpt-4"},
            runtime_overrides={"temperature": 0.8, "max_tokens": 3000},
        )

        effective = config.get_effective_config()

        # Runtime overrides should win
        assert effective["max_tokens"] == 3000
        assert effective["temperature"] == 0.8

        # Project config should override global
        assert effective["model"] == "gpt-4"

        # Global config should be base
        assert effective["theme"] == "dark"

    def test_get_value_with_precedence(self):
        """Test getting individual values with precedence."""
        config = Configuration(
            global_config={"key1": "global", "key2": "global"},
            project_config={"key1": "project", "key3": "project"},
            runtime_overrides={"key1": "runtime"},
        )

        # Runtime override wins
        assert config.get_value("key1") == "runtime"

        # Project config wins over global
        assert config.get_value("key2") == "global"
        assert config.get_value("key3") == "project"

        # Default value for missing key
        assert config.get_value("missing_key", "default") == "default"


class TestModelIntegration:
    """Test integration between models."""

    def test_session_with_full_context(self):
        """Test session with complete context."""
        # Create session
        session = Session(project_path=Path("/integration/test"))

        # Add project context
        context = ProjectContext(
            project_path=Path("/integration/test"), vcs_type="git", current_branch="main"
        )
        session.update_project_context(context)

        # Add configuration
        config = Configuration(provider_type=ProviderType.ANTHROPIC, safety_mode=SafetyMode.CONFIRM)
        session.configuration = config

        # Add messages and commands
        session.add_message(Message(role=MessageRole.USER, content="Please run ls command"))

        session.add_command(Command(command_text="ls -la", risk_level="low"))

        # Verify relationships
        assert session.project_context is not None
        assert session.project_context.vcs_type == "git"
        assert session.configuration is not None
        assert session.configuration.provider_type == ProviderType.ANTHROPIC
        assert len(session.conversation_history) == 1
        assert len(session.pending_commands) == 1
        assert session.pending_commands[0].session_id == session.session_id

    def test_full_serialization_cycle(self):
        """Test complete serialization and deserialization."""
        # Create complex session
        session = Session(project_path=Path("/complex/test"))

        # Add project context
        context = ProjectContext(
            project_path=Path("/complex/test"), vcs_type="git", current_branch="feature"
        )
        session.update_project_context(context)

        # Add messages
        session.add_message(Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"))
        session.add_message(
            Message(
                role=MessageRole.USER,
                content="Help me with this project",
                metadata={"priority": "high"},
            )
        )

        # Add commands
        cmd = Command(
            command_text="git status", approval_status=CommandStatus.APPROVED, risk_level="low"
        )
        session.add_command(cmd)

        # Serialize and deserialize
        data = session.to_dict()
        restored = Session.from_dict(data)

        # Verify everything is preserved
        assert restored.session_id == session.session_id
        assert restored.project_path == session.project_path
        assert restored.project_context is not None
        assert restored.project_context.vcs_type == "git"
        assert restored.project_context.current_branch == "feature"
        assert len(restored.conversation_history) == 2
        assert restored.conversation_history[1].metadata["priority"] == "high"
        assert len(restored.pending_commands) == 1
        assert restored.pending_commands[0].command_text == "git status"
        assert restored.pending_commands[0].approval_status == CommandStatus.APPROVED

    def test_context_size_calculation(self):
        """Test context size calculation."""
        session = Session()

        # Add messages of known lengths
        session.add_message(Message(content="a" * 100))  # 100 chars
        session.add_message(Message(content="b" * 200))  # 200 chars

        # Context size should be approximately (100 + 200) / 4 = 75 tokens
        expected_size = (100 + 200) // 4
        assert session.context_size == expected_size

    def test_session_status_management(self):
        """Test session status management."""
        session = Session()

        # Start active
        assert session.status == SessionStatus.ACTIVE

        # Can pause
        session.status = SessionStatus.PAUSED
        assert session.status == SessionStatus.PAUSED

        # Can terminate
        session.status = SessionStatus.TERMINATED
        assert session.status == SessionStatus.TERMINATED
