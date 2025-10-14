"""Core data models for Mentat CLI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..providers.interfaces import MessageRole, ProviderType
from ..safety.validator import ApprovalScope, SafetyMode
from ..vcs.interfaces import VCSStatus


class SessionStatus(Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"
    COMPLETED = "completed"


class CommandStatus(Enum):
    """Command execution status."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"
    FAILED = "failed"
    RUNNING = "running"
    COMPLETED = "completed"


class CommandSource(Enum):
    """Source of command execution."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class Message:
    """Represents a message in conversation history."""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    role: MessageRole = field(default_factory=lambda: MessageRole.USER)
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    command_requests: List[str] = field(default_factory=list)
    approval_status: Optional[str] = None
    session_id: Optional[str] = ""

    def __init__(self, id: Optional[str] = None, role: Optional[Any] = None, **kwargs: Any) -> None:
        """Initialize message with id alias support."""
        # Process input parameters and apply defaults
        kwargs = self._process_message_input(id, role, kwargs)
        kwargs = self._apply_message_defaults(kwargs)

        # Set all attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _process_message_input(
        self, id: Optional[str], role: Optional[Any], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process message input parameters and handle aliases."""
        # Handle id parameter as alias for message_id
        if id is not None:
            kwargs["message_id"] = id

        # Handle string role parameter conversion
        if role is not None:
            kwargs["role"] = self._convert_role_to_enum(role)

        return kwargs

    def _convert_role_to_enum(self, role: Any) -> MessageRole:
        """Convert role parameter to MessageRole enum."""
        if isinstance(role, str):
            role_mapping = {
                "system": MessageRole.SYSTEM,
                "user": MessageRole.USER,
                "assistant": MessageRole.ASSISTANT,
            }
            return role_mapping.get(role, MessageRole.USER)
        return role

    def _apply_message_defaults(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for message fields not provided."""
        defaults = {
            "message_id": str(uuid4()),
            "role": MessageRole.USER,
            "content": "",
            "timestamp": datetime.now(),
            "metadata": {},
            "command_requests": [],
            "approval_status": None,
            "session_id": "",
        }

        # Apply defaults for missing keys
        for key, default_value in defaults.items():
            if key not in kwargs:
                kwargs[key] = default_value

        return kwargs

    @property
    def id(self) -> str:
        """Alias for message_id for backward compatibility."""
        return self.message_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "id": self.message_id,  # Alias for backward compatibility
            "role": self.role.value if isinstance(self.role, MessageRole) else str(self.role),
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "command_requests": self.command_requests,
            "approval_status": self.approval_status,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        message_id = data.get("message_id") or data.get("id")
        role = data.get("role", "user")
        return cls(
            id=message_id,
            role=role,
            content=data.get("content", ""),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else datetime.now()
            ),
            metadata=data.get("metadata", {}),
            command_requests=data.get("command_requests", []),
            approval_status=data.get("approval_status"),
            session_id=data.get("session_id"),
        )


@dataclass
class Command:
    """A command to be executed by the system."""

    command_text: str = ""
    command_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: Optional[str] = None
    source: CommandSource = CommandSource.USER
    parsed_args: List[str] = field(default_factory=list)
    safety_pattern: Optional[str] = None
    approval_status: CommandStatus = CommandStatus.PENDING
    approval_scope: Optional[ApprovalScope] = None
    risk_level: str = "low"
    timestamp: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: str = ""
    error_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, text: Optional[str] = None, id: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize command with text/id alias support."""
        # Process input parameters and apply defaults
        kwargs = self._process_input_parameters(text, id, kwargs)
        kwargs = self._apply_default_values(kwargs)

        # Set all attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _process_input_parameters(
        self, text: Optional[str], id: Optional[str], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process input parameters and handle aliases."""
        # Handle text parameter as alias for command_text
        if text is not None:
            kwargs["command_text"] = text

        # Handle id parameter as alias for command_id
        if id is not None:
            kwargs["command_id"] = id

        return kwargs

    def _apply_default_values(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for fields not provided."""
        defaults = {
            "command_text": "",
            "command_id": str(uuid4()),
            "session_id": "",  # Default to empty string per tests expecting ""
            "source": CommandSource.USER,
            "parsed_args": [],
            "safety_pattern": None,
            "approval_status": CommandStatus.PENDING,
            "approval_scope": None,
            "risk_level": "low",
            "timestamp": datetime.now(),
            "executed_at": None,
            "exit_code": None,
            "output": "",
            "error_output": "",
            "metadata": {},
        }

        # Apply defaults for missing keys
        for key, default_value in defaults.items():
            if key not in kwargs:
                kwargs[key] = default_value

        return kwargs

    @property
    def id(self) -> str:
        """Alias for command_id for backward compatibility."""
        return self.command_id

    @property
    def text(self) -> str:
        """Alias for command_text for backward compatibility."""
        return self.command_text

    @property
    def status(self) -> CommandStatus:
        """Alias for approval_status for backward compatibility."""
        return self.approval_status

    @status.setter
    def status(self, value: CommandStatus) -> None:
        """Set status via approval_status for backward compatibility."""
        self.approval_status = value

    def mark_executed(self, exit_code: int, output: str = "", error_output: str = "") -> None:
        """Mark command as executed with results."""
        # Tests expect successful execution to map to EXECUTED, otherwise FAILED
        self.approval_status = CommandStatus.EXECUTED if exit_code == 0 else CommandStatus.FAILED
        self.executed_at = datetime.now()
        self.exit_code = exit_code
        self.output = output
        self.error_output = error_output

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for serialization."""
        return {
            "command_id": self.command_id,
            "id": self.command_id,  # Alias for backward compatibility
            "text": self.command_text,
            "command_text": self.command_text,
            "source": self.source.value
            if isinstance(self.source, CommandSource)
            else str(self.source),
            "status": self.approval_status.value,
            "approval_status": self.approval_status.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "exit_code": self.exit_code,
            "output": self.output,
            "error_output": self.error_output,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        """Create command from dictionary."""
        return cls(
            text=cls._extract_command_text(data),
            id=cls._extract_command_id(data),
            source=CommandSource(data.get("source", CommandSource.USER.value)),
            session_id=data.get("session_id"),
            timestamp=cls._parse_creation_timestamp(data.get("timestamp")),
            executed_at=cls._parse_optional_timestamp(data.get("executed_at")),
            exit_code=data.get("exit_code"),
            output=data.get("output", ""),
            error_output=data.get("error_output", ""),
            metadata=data.get("metadata", {}),
            approval_status=CommandStatus(cls._extract_approval_status(data)),
        )

    @classmethod
    def _extract_command_id(cls, data: Dict[str, Any]) -> Optional[str]:
        """Extract command ID from data with fallback."""
        return data.get("command_id") or data.get("id")

    @classmethod
    def _extract_command_text(cls, data: Dict[str, Any]) -> str:
        """Extract command text from data with fallback."""
        return data.get("text") or data.get("command_text", "")

    @classmethod
    def _extract_approval_status(cls, data: Dict[str, Any]) -> str:
        """Extract approval status from data with fallback."""
        return data.get("approval_status") or data.get("status", CommandStatus.PENDING.value)

    @classmethod
    def _parse_creation_timestamp(cls, timestamp_str: Optional[str]) -> datetime:
        """Parse creation timestamp, defaulting to now if not provided."""
        return datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

    @classmethod
    def _parse_optional_timestamp(cls, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse optional timestamp, returning None if not provided."""
        return datetime.fromisoformat(timestamp_str) if timestamp_str else None


@dataclass
class ProjectContext:
    """Represents current state of project being worked on."""

    project_path: Path
    vcs_type: str = "none"
    current_branch: Optional[str] = None
    uncommitted_changes: int = 0
    untracked_files: int = 0
    project_files: List[str] = field(default_factory=list)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    last_scanned: Optional[datetime] = None
    file_tree_hash: Optional[str] = None
    vcs_status: Optional[VCSStatus] = None
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    git_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, path: Optional[Any] = None, **kwargs: Any) -> None:
        """Initialize project context with path alias support."""
        # Handle path parameter as alias for project_path
        if path is not None:
            if isinstance(path, str):
                kwargs["project_path"] = Path(path)
            else:
                kwargs["project_path"] = path

        # Set defaults for required fields
        if "project_path" not in kwargs:
            kwargs["project_path"] = Path.cwd()

        # Set defaults for optional fields
        field_defaults: List[Tuple[str, Any]] = [
            ("vcs_type", "none"),
            ("current_branch", None),
            ("uncommitted_changes", 0),
            ("untracked_files", 0),
            ("project_files", []),
            ("dependencies", {}),
            ("last_scanned", None),
            ("file_tree_hash", None),
            ("vcs_status", None),
            ("name", None),
            ("description", None),
            ("created_at", datetime.now()),
            ("updated_at", datetime.now()),
            ("files", []),
            ("git_info", None),
            ("metadata", {}),
        ]

        for field_name, default_value in field_defaults:
            if field_name not in kwargs:
                if isinstance(default_value, (list, dict)):
                    kwargs[field_name] = default_value.copy()
                else:
                    kwargs[field_name] = default_value

        # Set all attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def path(self) -> Path:
        """Alias for project_path for backward compatibility."""
        return self.project_path

    def update_from_vcs_status(self, vcs_status: VCSStatus) -> None:
        """Update context from VCS status information."""
        self.vcs_status = vcs_status
        self.current_branch = vcs_status.current_branch
        self.uncommitted_changes = vcs_status.uncommitted_changes
        # VCSStatus.untracked_files may be a list in newer API
        try:
            self.untracked_files = len(vcs_status.untracked_files)  # type: ignore[arg-type]
        except Exception:
            self.untracked_files = int(vcs_status.untracked_files)  # type: ignore[arg-type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert project context to dictionary for serialization."""
        return {
            "project_path": str(self.project_path).replace(
                "\\", "/"
            ),  # Always use Unix-style paths
            "path": str(self.project_path).replace("\\", "/"),  # Alias for backward compatibility
            "vcs_type": self.vcs_type,
            "current_branch": self.current_branch,
            "uncommitted_changes": self.uncommitted_changes,
            "untracked_files": self.untracked_files,
            "project_files": self.project_files,
            "dependencies": self.dependencies,
            "last_scanned": self.last_scanned.isoformat() if self.last_scanned else None,
            "file_tree_hash": self.file_tree_hash,
            "vcs_status": (self.vcs_status.__dict__ if self.vcs_status else None),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "files": self.files,
            "git_info": self.git_info,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectContext":
        """Create project context from dictionary."""
        path = data.get("project_path") or data.get("path") or "."
        return cls(
            path=Path(path),
            vcs_type=data.get("vcs_type", "none"),
            current_branch=data.get("current_branch"),
            uncommitted_changes=data.get("uncommitted_changes", 0),
            untracked_files=data.get("untracked_files", 0),
            project_files=data.get("project_files", []),
            dependencies=data.get("dependencies", {}),
            last_scanned=(
                datetime.fromisoformat(data["last_scanned"]) if data.get("last_scanned") else None
            ),
            file_tree_hash=data.get("file_tree_hash"),
            vcs_status=None,  # VCSStatus.from_dict not implemented yet
            name=data.get("name"),
            description=data.get("description"),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            ),
            files=data.get("files", []),
            git_info=data.get("git_info"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Configuration:
    """Represents merged configuration from global/project/runtime sources."""

    config_id: str = field(default_factory=lambda: str(uuid4()))
    global_config: Dict[str, Any] = field(default_factory=dict)
    project_config: Dict[str, Any] = field(default_factory=dict)
    runtime_overrides: Dict[str, Any] = field(default_factory=dict)

    # Core configuration values
    provider_type: ProviderType = ProviderType.OPENAI
    safety_mode: SafetyMode = SafetyMode.CONFIRM
    max_conversation_length: int = 100
    context_window_size: int = 4096

    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with proper precedence."""
        config = {}
        config.update(self.global_config)
        config.update(self.project_config)
        config.update(self.runtime_overrides)
        return config

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback chain."""
        if key in self.runtime_overrides:
            return self.runtime_overrides[key]
        elif key in self.project_config:
            return self.project_config[key]
        elif key in self.global_config:
            return self.global_config[key]
        else:
            return default


@dataclass
class Session:
    """Represents an active conversation session with AI assistant."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    project_path: Path = field(default_factory=lambda: Path.cwd())
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    provider_type: ProviderType = ProviderType.OPENAI
    safety_mode: SafetyMode = SafetyMode.CONFIRM
    status: SessionStatus = SessionStatus.ACTIVE
    context_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    conversation_history: List[Message] = field(default_factory=list)
    project_context: Optional[ProjectContext] = None
    configuration: Optional[Configuration] = None
    pending_commands: List[Command] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, id: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize session with id alias support."""
        # Process input parameters and apply defaults
        kwargs = self._process_session_input(id, kwargs)
        kwargs = self._apply_session_defaults(kwargs)
        kwargs = self._normalize_session_types(kwargs)

        # Set all attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _process_session_input(self, id: Optional[str], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Process session input parameters."""
        # Handle id parameter as alias for session_id
        if id is not None:
            kwargs["session_id"] = id
        return kwargs

    def _apply_session_defaults(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for session fields not provided."""
        defaults = {
            "session_id": str(uuid4()),
            "project_path": Path.cwd(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "provider_type": ProviderType.OPENAI,
            "safety_mode": SafetyMode.CONFIRM,
            "status": SessionStatus.ACTIVE,
            "context_size": 0,
            "metadata": {},
            "conversation_history": [],
            "project_context": None,
            "configuration": None,
            "pending_commands": [],
            "variables": {},
        }

        # Apply defaults for missing keys
        for key, default_value in defaults.items():
            if key not in kwargs:
                kwargs[key] = default_value

        return kwargs

    def _normalize_session_types(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data types for session fields."""
        # Convert project_path to Path if it's a string
        if isinstance(kwargs.get("project_path"), str):
            kwargs["project_path"] = Path(kwargs["project_path"])

        return kwargs

    @property
    def id(self) -> str:
        """Alias for session_id for backward compatibility."""
        return self.session_id

    @property
    def messages(self) -> List[Message]:
        """Alias for conversation_history."""
        return self.conversation_history

    @property
    def commands(self) -> List[Command]:
        """Alias for pending_commands."""
        return self.pending_commands

    def add_message(self, message: Message) -> None:
        """Add message to conversation history."""
        self.conversation_history.append(message)
        self.updated_at = datetime.now()
        self._update_context_size()

    def add_command(self, command: Command) -> None:
        """Add command to pending commands."""
        command.session_id = self.session_id
        self.pending_commands.append(command)
        self.updated_at = datetime.now()

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get recent messages from conversation history."""
        return self.conversation_history[-count:] if count > 0 else self.conversation_history

    def get_pending_commands(self) -> List[Command]:
        """Get commands pending approval or execution."""
        return [
            cmd for cmd in self.pending_commands if cmd.approval_status == CommandStatus.PENDING
        ]

    def update_project_context(self, context: ProjectContext) -> None:
        """Update project context."""
        self.project_context = context
        self.updated_at = datetime.now()

    def _update_context_size(self) -> None:
        """Update approximate context size in tokens."""
        # Simple estimation: ~4 characters per token
        total_chars = sum(len(msg.content) for msg in self.conversation_history)
        self.context_size = total_chars // 4

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history with optional limit."""
        if limit is None:
            return self.conversation_history.copy()
        return self.conversation_history[-limit:] if limit > 0 else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        user_messages = sum(1 for msg in self.conversation_history if msg.role == MessageRole.USER)
        assistant_messages = sum(
            1 for msg in self.conversation_history if msg.role == MessageRole.ASSISTANT
        )
        return {
            "message_count": len(self.conversation_history),
            "command_count": len(self.pending_commands),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "context_size": self.context_size,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        result = self._serialize_core_fields()
        result.update(self._serialize_messages())
        result.update(self._serialize_project_context())
        result.update(self._serialize_commands())
        return result

    def _serialize_core_fields(self) -> Dict[str, Any]:
        """Serialize core session fields."""
        return {
            "session_id": self.session_id,
            "id": self.session_id,  # Alias for backward compatibility
            "project_path": str(self.project_path).replace("\\", "/"),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "provider_type": self.provider_type.value,
            "safety_mode": self.safety_mode.value,
            "status": self.status.value,
            "context_size": self.context_size,
            "metadata": self.metadata,
            "variables": self.variables,
        }

    def _serialize_messages(self) -> Dict[str, Any]:
        """Serialize conversation history and messages."""
        return {
            "messages": [
                self._serialize_message_with_session_id(msg) for msg in self.conversation_history
            ],
            "conversation_history": [
                self._serialize_message_basic(msg) for msg in self.conversation_history
            ],
        }

    def _serialize_message_with_session_id(self, msg: "Message") -> Dict[str, Any]:
        """Serialize message with session ID for messages array."""
        result = self._serialize_message_basic(msg)
        result.update(
            {
                "id": msg.message_id,  # Alias for backward compatibility
                "session_id": msg.session_id,
            }
        )
        return result

    def _serialize_message_basic(self, msg: "Message") -> Dict[str, Any]:
        """Serialize basic message fields."""
        return {
            "message_id": msg.message_id,
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "metadata": msg.metadata,
            "command_requests": msg.command_requests,
            "approval_status": msg.approval_status,
        }

    def _serialize_project_context(self) -> Dict[str, Any]:
        """Serialize project context if available."""
        if not self.project_context:
            return {"project_context": None}

        return {
            "project_context": {
                "project_path": str(self.project_context.project_path).replace("\\", "/"),
                "vcs_type": self.project_context.vcs_type,
                "current_branch": self.project_context.current_branch,
                "uncommitted_changes": self.project_context.uncommitted_changes,
                "untracked_files": self.project_context.untracked_files,
                "project_files": self.project_context.project_files,
                "dependencies": self.project_context.dependencies,
                "last_scanned": (
                    self.project_context.last_scanned.isoformat()
                    if self.project_context.last_scanned
                    else None
                ),
                "file_tree_hash": self.project_context.file_tree_hash,
                "name": self.project_context.name,
                "description": self.project_context.description,
                "created_at": self.project_context.created_at.isoformat()
                if self.project_context.created_at
                else None,
                "updated_at": self.project_context.updated_at.isoformat()
                if self.project_context.updated_at
                else None,
                "files": self.project_context.files,
                "git_info": self.project_context.git_info,
                "metadata": self.project_context.metadata,
                "vcs_status": (
                    vars(self.project_context.vcs_status)
                    if self.project_context.vcs_status
                    else None
                ),
            }
        }

    def _serialize_commands(self) -> Dict[str, Any]:
        """Serialize pending commands in both formats."""
        return {
            "commands": [self._serialize_command_detailed(cmd) for cmd in self.pending_commands],
            "pending_commands": [
                self._serialize_command_basic(cmd) for cmd in self.pending_commands
            ],
        }

    def _serialize_command_detailed(self, cmd: "Command") -> Dict[str, Any]:
        """Serialize command with all details and aliases."""
        result = self._serialize_command_basic(cmd)
        result.update(
            {
                "id": cmd.command_id,  # Alias for backward compatibility
                "text": cmd.command_text,  # Alias for backward compatibility
                "status": cmd.approval_status.value,  # Alias for backward compatibility
                "session_id": cmd.session_id,
                "source": cmd.source.value,
                "timestamp": cmd.timestamp.isoformat(),
                "metadata": cmd.metadata,
            }
        )
        return result

    def _serialize_command_basic(self, cmd: "Command") -> Dict[str, Any]:
        """Serialize basic command fields."""
        return {
            "command_id": cmd.command_id,
            "command_text": cmd.command_text,
            "parsed_args": cmd.parsed_args,
            "safety_pattern": cmd.safety_pattern,
            "approval_status": cmd.approval_status.value,
            "approval_scope": cmd.approval_scope.value if cmd.approval_scope else None,
            "risk_level": cmd.risk_level,
            "executed_at": cmd.executed_at.isoformat() if cmd.executed_at else None,
            "exit_code": cmd.exit_code,
            "output": cmd.output,
            "error_output": cmd.error_output,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        # Create base session with core attributes
        session = cls._create_base_session(data)

        # Restore complex nested data
        cls._restore_conversation_history(session, data)
        cls._restore_project_context(session, data)
        cls._restore_pending_commands(session, data)

        return session

    @classmethod
    def _create_base_session(cls, data: Dict[str, Any]) -> "Session":
        """Create session with core attributes from dictionary data."""
        session_id = data.get("session_id") or data.get("id") or str(uuid4())

        return cls(
            session_id=session_id,
            project_path=Path(data.get("project_path") or "."),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            provider_type=ProviderType(data.get("provider_type", ProviderType.OPENAI.value)),
            safety_mode=SafetyMode(data.get("safety_mode", SafetyMode.CONFIRM.value)),
            status=SessionStatus(data.get("status", SessionStatus.ACTIVE.value)),
            context_size=data.get("context_size", 0),
            variables=data.get("variables", {}),
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def _parse_datetime(datetime_str: Optional[str]) -> datetime:
        """Parse datetime string with fallback to current time."""
        if not datetime_str:
            return datetime.now()

        try:
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return datetime.now()

    @staticmethod
    def _parse_datetime_with_z_handling(datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string with Z timezone handling and return None if invalid."""
        if not datetime_str:
            return None

        try:
            # Handle timezone 'Z' format
            normalized_str = datetime_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized_str)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _restore_conversation_history(cls, session: "Session", data: Dict[str, Any]) -> None:
        """Restore conversation history from dictionary data."""
        # Handle both 'messages' and 'conversation_history' keys for backward compatibility
        msg_list = data.get("conversation_history") or data.get("messages", [])

        for msg_data in msg_list:
            message = cls._create_message_from_data(msg_data, session.session_id)
            session.conversation_history.append(message)

    @classmethod
    def _create_message_from_data(cls, msg_data: Dict[str, Any], session_id: str) -> Message:
        """Create Message instance from dictionary data."""
        # Handle message id alias for backward compatibility
        msg_id = msg_data.get("message_id") or msg_data.get("id") or str(uuid4())

        # Parse timestamp with special Z handling
        timestamp = cls._parse_datetime_with_z_handling(msg_data.get("timestamp"))

        return Message(
            id=msg_id,
            role=msg_data.get("role", MessageRole.USER.value),
            content=msg_data.get("content", ""),
            timestamp=timestamp or datetime.now(),
            metadata=msg_data.get("metadata", {}),
            command_requests=msg_data.get("command_requests", []),
            approval_status=msg_data.get("approval_status"),
            session_id=session_id,
        )

    @classmethod
    def _restore_project_context(cls, session: "Session", data: Dict[str, Any]) -> None:
        """Restore project context from dictionary data."""
        ctx_data = data.get("project_context")
        if not ctx_data:
            return

        session.project_context = ProjectContext(
            project_path=Path(ctx_data.get("project_path") or "."),
            vcs_type=ctx_data.get("vcs_type", "none"),
            current_branch=ctx_data.get("current_branch"),
            uncommitted_changes=ctx_data.get("uncommitted_changes", 0),
            untracked_files=ctx_data.get("untracked_files", 0),
            project_files=ctx_data.get("project_files", []),
            dependencies=ctx_data.get("dependencies", {}),
            last_scanned=cls._parse_datetime_with_z_handling(ctx_data.get("last_scanned")),
            file_tree_hash=ctx_data.get("file_tree_hash"),
            name=ctx_data.get("name"),
            description=ctx_data.get("description"),
            created_at=cls._parse_datetime_with_z_handling(ctx_data.get("created_at")),
            updated_at=cls._parse_datetime_with_z_handling(ctx_data.get("updated_at")),
            files=ctx_data.get("files", []),
            git_info=ctx_data.get("git_info"),
            metadata=ctx_data.get("metadata", {}),
        )

    @classmethod
    def _restore_pending_commands(cls, session: "Session", data: Dict[str, Any]) -> None:
        """Restore pending commands from dictionary data."""
        # Handle both 'commands' and 'pending_commands' keys for backward compatibility
        cmd_list = data.get("pending_commands") or data.get("commands", [])

        for cmd_data in cmd_list:
            command = cls._create_command_from_data(cmd_data, session.session_id)
            session.pending_commands.append(command)

    @classmethod
    def _create_command_from_data(cls, cmd_data: Dict[str, Any], session_id: str) -> Command:
        """Create Command instance from dictionary data."""
        # Handle command id alias for backward compatibility
        command_id = cmd_data.get("command_id") or cmd_data.get("id", str(uuid4()))
        command_text = cmd_data.get("command_text") or cmd_data.get("text", "")

        # Handle status alias for backward compatibility
        status_value = cmd_data.get("approval_status") or cmd_data.get(
            "status", CommandStatus.PENDING.value
        )

        return Command(
            command_id=command_id,
            session_id=session_id,
            command_text=command_text,
            parsed_args=cmd_data.get("parsed_args", []),
            safety_pattern=cmd_data.get("safety_pattern"),
            approval_status=CommandStatus(status_value),
            approval_scope=(
                ApprovalScope(cmd_data["approval_scope"])
                if cmd_data.get("approval_scope")
                else None
            ),
            risk_level=cmd_data.get("risk_level", "low"),
            executed_at=cls._parse_datetime_with_z_handling(cmd_data.get("executed_at")),
            exit_code=cmd_data.get("exit_code"),
            output=cmd_data.get("output", ""),
            error_output=cmd_data.get("error_output", ""),
            source=CommandSource(cmd_data.get("source", CommandSource.USER.value)),
            timestamp=cls._parse_datetime_with_z_handling(cmd_data.get("timestamp"))
            or datetime.now(),
            metadata=cmd_data.get("metadata", {}),
        )
