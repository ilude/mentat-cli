"""VCS detection and selection logic."""

from pathlib import Path
from typing import Dict, Optional, Type

from .git import GitVCSBackend
from .interfaces import BaseVCSBackend, VCSType


class VCSDetector:
    """Detects and provides appropriate VCS backend for a path."""

    def __init__(self) -> None:
        """Initialize VCS detector with available backends."""
        self._backends: Dict[VCSType, Type[BaseVCSBackend]] = {
            VCSType.GIT: GitVCSBackend,
        }

    def detect_vcs_type(self, path: Path) -> VCSType:
        """Detect the VCS type for a given path."""
        # Make sure path is a directory
        if path.is_file():
            path = path.parent

        # Check for Git repository
        if (path / ".git").exists() or self._check_git_repository(path):
            return VCSType.GIT

        # Check parent directories up to root
        parent = path.parent
        while parent != path:  # Stop when we reach the root
            if (parent / ".git").exists() or self._check_git_repository(parent):
                return VCSType.GIT
            path = parent
            parent = path.parent

        return VCSType.NONE

    def _check_git_repository(self, path: Path) -> bool:
        """Check if path is inside a Git repository."""
        try:
            git_backend = GitVCSBackend()
            return git_backend.is_repository(path)
        except Exception:
            return False

    def get_backend(self, path: Path) -> Optional[BaseVCSBackend]:
        """Get the appropriate VCS backend for a path."""
        vcs_type = self.detect_vcs_type(path)

        if vcs_type == VCSType.NONE:
            return None

        backend_class = self._backends.get(vcs_type)
        if backend_class:
            return backend_class()

        return None

    # Backward-compatible aliases used in tests
    def get_vcs_backend(self, path: Path) -> Optional[BaseVCSBackend]:
        """Alias for get_backend."""
        return self.get_backend(path)

    def is_vcs_repository(self, path: Path) -> bool:
        """Return True if a VCS repository is detected for path."""
        return self.detect_vcs_type(path) != VCSType.NONE

    def get_backend_by_type(self, vcs_type: VCSType) -> Optional[BaseVCSBackend]:
        """Get VCS backend by type."""
        backend_class = self._backends.get(vcs_type)
        if backend_class:
            return backend_class()
        return None

    def find_repository_root(self, path: Path) -> Optional[Path]:
        """Find the root directory of the repository containing the given path."""
        # Make sure path is a directory
        if path.is_file():
            path = path.parent

        # Check current directory and parents
        current = path.resolve()
        while True:
            if (current / ".git").exists():
                return current

            parent = current.parent
            if parent == current:  # Reached the root
                break
            current = parent

        return None

    def register_backend(self, vcs_type: VCSType, backend_class: Type[BaseVCSBackend]) -> None:
        """Register a new VCS backend."""
        self._backends[vcs_type] = backend_class

    def get_supported_types(self) -> list[VCSType]:
        """Get list of supported VCS types."""
        return list(self._backends.keys())


# Default detector instance
_default_detector = VCSDetector()


def detect_vcs_type(path: Path) -> VCSType:
    """Detect VCS type for a path using the default detector."""
    return _default_detector.detect_vcs_type(path)


def get_vcs_backend(path: Path) -> Optional[BaseVCSBackend]:
    """Get VCS backend for a path using the default detector."""
    return _default_detector.get_backend(path)


def find_repository_root(path: Path) -> Optional[Path]:
    """Find repository root using the default detector."""
    return _default_detector.find_repository_root(path)
