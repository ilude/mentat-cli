"""Session management and context interfaces for Mentat CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from ..core.models import Session
from ..providers.interfaces import Message, ProviderType
from ..vcs.interfaces import VCSStatus


@dataclass
class ProjectContext:
    """Project context information."""

    project_path: Path
    vcs_status: Optional[VCSStatus] = None
    project_files: List[str] = field(default_factory=list)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    last_scanned: Optional[datetime] = None
    file_tree_hash: Optional[str] = None


@dataclass
class SessionMetadata:
    """Session metadata."""

    session_id: str
    created_at: datetime
    updated_at: datetime
    provider_type: ProviderType
    safety_mode: str
    project_path: Path
    status: str = "active"  # active, paused, terminated


@dataclass
class SessionContext:
    """Complete session context."""

    metadata: SessionMetadata
    project_context: Optional[ProjectContext] = None
    conversation_history: List[Message] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    pending_approvals: List[str] = field(default_factory=list)


class SessionStorage(Protocol):
    """Protocol for session storage."""

    async def save_session(self, session: Session) -> None:
        """Save a session."""
        ...

    async def load_session(self, session_id: str) -> Session:
        """Load a session by ID."""
        ...

    async def delete_session(self, session_id: str) -> None:
        """Delete a session by ID."""
        ...

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""
        ...


class SessionManager:
    """Concrete session manager for tests."""

    def __init__(self, storage: "SessionStorage") -> None:
        self.storage = storage
        self._active_session_id: Optional[str] = None

    async def create_session(
        self,
        project_path: Optional[Path] = None,
        provider_type: ProviderType = ProviderType.LOCAL,
        safety_mode: str = "confirm",
    ) -> str:
        """Create a new session and return its ID (test expectation)."""
        project_path = project_path or Path.cwd()
        from ..safety.validator import SafetyMode as _SafetyMode

        try:
            mode = _SafetyMode(safety_mode)
        except ValueError:
            mode = _SafetyMode.CONFIRM

        session = Session(
            project_path=project_path,
            provider_type=provider_type,
            safety_mode=mode,
        )
        await self.storage.save_session(session)
        self._active_session_id = session.session_id
        return session.session_id

    async def get_session(self, session_id: str) -> Optional[Session]:
        try:
            return await self.storage.load_session(session_id)
        except Exception:
            return None

    async def close_session(self, session_id: str) -> bool:
        await self.storage.delete_session(session_id)
        if self._active_session_id == session_id:
            self._active_session_id = None
        return True

    async def list_sessions(self) -> List[str]:
        return await self.storage.list_sessions()

    async def set_active_session(self, session_id: str) -> None:
        if await self.get_session(session_id):
            self._active_session_id = session_id
        else:
            raise ValueError(f"Session {session_id} not found")

    async def get_active_session(self) -> Optional[Session]:
        if not self._active_session_id:
            return None
        return await self.get_session(self._active_session_id)


class ContextBuilder(Protocol):
    """Protocol for building session context."""

    async def build_project_context(self, project_path: Path) -> ProjectContext:
        """Build project context for a path."""
        ...

    async def refresh_project_context(self, context: ProjectContext) -> ProjectContext:
        """Refresh existing project context."""
        ...

    async def scan_project_files(self, project_path: Path) -> List[str]:
        """Scan and list relevant project files."""
        ...

    async def detect_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Detect project dependencies."""
        ...

    async def compute_file_tree_hash(self, project_path: Path) -> str:
        """Compute hash of file tree structure."""
        ...


class ConversationManager(Protocol):
    """Protocol for managing conversation history."""

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add message to conversation history."""
        ...

    async def get_conversation(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history for a session."""
        ...

    async def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        ...

    async def get_context_summary(self, session_id: str, max_tokens: int = 1000) -> str:
        """Get summarized conversation context."""
        ...

    async def prune_conversation(self, session_id: str, max_messages: int = 100) -> None:
        """Prune old messages to keep conversation manageable."""
        ...


class BaseSessionManager(ABC):
    """Base class for session manager implementations."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._active_session_id: Optional[str] = None

    @abstractmethod
    async def create_session(
        self, project_path: Path, provider_type: ProviderType, safety_mode: str = "confirm"
    ) -> SessionContext:
        """Create a new session."""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get session by ID."""
        pass

    @abstractmethod
    async def update_session(self, session: SessionContext) -> None:
        """Update session state."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    async def list_sessions(self) -> List[SessionMetadata]:
        """List all sessions."""
        pass

    async def get_active_session(self) -> Optional[SessionContext]:
        """Get currently active session."""
        if self._active_session_id:
            return await self.get_session(self._active_session_id)
        return None

    async def set_active_session(self, session_id: str) -> None:
        """Set active session."""
        session = await self.get_session(session_id)
        if session:
            self._active_session_id = session_id
        else:
            raise ValueError(f"Session {session_id} not found")

    @abstractmethod
    async def pause_session(self, session_id: str) -> None:
        """Pause a session."""
        pass

    @abstractmethod
    async def resume_session(self, session_id: str) -> None:
        """Resume a paused session."""
        pass

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions. Default implementation."""
        return 0


class SessionError(Exception):
    """Base exception for session-related errors."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when session is not found."""

    pass


class SessionStateError(SessionError):
    """Raised when session is in invalid state for operation."""

    pass
