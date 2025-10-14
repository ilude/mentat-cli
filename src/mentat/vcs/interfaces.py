"""Version control system interfaces for Mentat CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Protocol, Union


class VCSType(Enum):
    """Supported version control systems."""

    GIT = "git"
    SVN = "svn"
    NONE = "none"


@dataclass
class VCSStatus:
    """VCS status information."""

    current_branch: Optional[str] = None
    uncommitted_changes: int = 0
    untracked_files: Union[int, List[str]] = field(default_factory=list)
    staged_files: List[Any] = field(default_factory=list)
    ahead_commits: int = 0
    behind_commits: int = 0
    is_clean: bool = True


@dataclass
class CommitInfo:
    """Information about a commit."""

    hash: str
    message: str
    author: str
    date: str
    files_changed: List[str]
    # Extended fields expected by tests
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class VCSBackend(Protocol):
    """Protocol for version control system implementations."""

    def get_type(self) -> VCSType:
        """Get the VCS type."""
        ...

    def is_repository(self, path: Optional[Path] = None) -> bool:
        """Check if path is a VCS repository; if None, use bound path."""
        ...

    def get_status(self, path: Optional[Path] = None) -> VCSStatus:
        """Get current VCS status for given or bound path."""
        ...

    def get_current_branch(self, path: Optional[Path] = None) -> Optional[str]:
        """Get current branch name."""
        ...

    def get_uncommitted_changes(self, path: Optional[Path] = None) -> List[str]:
        """Get list of files with uncommitted changes."""
        ...

    def get_recent_commits(self, path: Optional[Path] = None, count: int = 10) -> List[CommitInfo]:
        """Get recent commit history."""
        ...

    def get_file_history(
        self, path: Optional[Path] = None, file_path: Optional[str] = None
    ) -> List[CommitInfo]:
        """Get commit history for a specific file."""
        ...

    def get_diff(self, path: Optional[Path] = None, file_path: Optional[str] = None) -> str:
        """Get diff of uncommitted changes."""
        ...


class BaseVCSBackend(ABC):
    """Base class for VCS backend implementations."""

    @abstractmethod
    def get_type(self) -> VCSType:
        """Get the VCS type."""
        pass

    @abstractmethod
    def is_repository(self, path: Optional[Path] = None) -> bool:
        """Check if path is a VCS repository; if None, use bound path."""
        pass

    @abstractmethod
    def get_status(self, path: Optional[Path] = None) -> VCSStatus:
        """Get current VCS status."""
        pass

    @abstractmethod
    def get_current_branch(self, path: Optional[Path] = None) -> Optional[str]:
        """Get current branch name."""
        pass

    @abstractmethod
    def get_uncommitted_changes(self, path: Optional[Path] = None) -> List[str]:
        """Get list of files with uncommitted changes."""
        pass

    @abstractmethod
    def get_recent_commits(self, path: Optional[Path] = None, count: int = 10) -> List[CommitInfo]:
        """Get recent commit history."""
        pass

    @abstractmethod
    def get_file_history(
        self, path: Optional[Path] = None, file_path: Optional[str] = None
    ) -> List[CommitInfo]:
        """Get commit history for a specific file."""
        pass

    @abstractmethod
    def get_diff(self, path: Optional[Path] = None, file_path: Optional[str] = None) -> str:
        """Get diff of uncommitted changes."""
        pass


class VCSError(Exception):
    """Base exception for VCS-related errors."""

    pass


class RepositoryNotFoundError(VCSError):
    """Raised when no VCS repository is found."""

    pass


class VCSOperationError(VCSError):
    """Raised when a VCS operation fails."""

    pass
