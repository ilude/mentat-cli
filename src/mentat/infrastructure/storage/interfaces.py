"""Storage backend interfaces for Mentat CLI."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class StorageBackend(Protocol):
    """Protocol for storage backend implementations."""

    async def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data."""
        ...

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID."""
        ...

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""
        ...

    async def delete_session(self, session_id: str) -> bool:
        """Delete session data. Returns True if successful."""
        ...

    async def store_conversation(
        self, session_id: str, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> None:
        """Store conversation messages."""
        ...

    async def load_conversation(
        self, session_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Load conversation messages."""
        ...

    async def store_project_context(self, project_path: str, context: Dict[str, Any]) -> None:
        """Store project context data."""
        ...

    async def load_project_context(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load project context data."""
        ...

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions. Returns count of deleted sessions."""
        ...


class BaseStorageBackend(ABC):
    """Base class for storage backend implementations."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize storage backend with optional base path."""
        self.base_path = base_path or Path.home() / ".mentat"
        self.base_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data."""
        pass

    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID."""
        pass

    @abstractmethod
    async def list_sessions(self) -> List[str]:
        """List all session IDs."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        pass

    @abstractmethod
    async def store_conversation(
        self, session_id: str, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> None:
        """Store conversation messages."""
        pass

    @abstractmethod
    async def load_conversation(
        self, session_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Load conversation messages."""
        pass

    @abstractmethod
    async def store_project_context(self, project_path: str, context: Dict[str, Any]) -> None:
        """Store project context data."""
        pass

    @abstractmethod
    async def load_project_context(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load project context data."""
        pass

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions. Default implementation."""
        # Base implementation - can be overridden by specific backends
        return 0


class StorageError(Exception):
    """Base exception for storage-related errors."""

    pass


class SessionNotFoundError(StorageError):
    """Raised when a session is not found."""

    pass


class ConversationNotFoundError(StorageError):
    """Raised when a conversation is not found."""

    pass
