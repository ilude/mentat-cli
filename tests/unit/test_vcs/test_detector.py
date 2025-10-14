"""Tests for VCS detector functionality."""

import tempfile
from pathlib import Path

import pytest

from mentat.vcs.detector import VCSDetector
from mentat.vcs.interfaces import VCSType


class TestVCSDetector:
    """Test VCS detection functionality."""

    @pytest.fixture
    def detector(self):
        """Create VCS detector instance."""
        return VCSDetector()

    def test_detector_initialization(self, detector):
        """Test VCS detector initialization."""
        assert isinstance(detector, VCSDetector)

    def test_detect_no_vcs(self, detector):
        """Test detection when no VCS is present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            vcs_type = detector.detect_vcs_type(path)
            assert vcs_type == VCSType.NONE

    def test_find_repository_root_no_vcs(self, detector):
        """Test finding repository root when no VCS is present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            root = detector.find_repository_root(path)
            assert root is None

    def test_get_vcs_backend_none(self, detector):
        """Test getting VCS backend for non-VCS directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            backend = detector.get_vcs_backend(path)
            assert backend is None

    def test_is_vcs_repository_false(self, detector):
        """Test VCS repository detection for non-VCS directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            is_repo = detector.is_vcs_repository(path)
            assert is_repo is False

    # Note: Git-specific tests would require git to be available
    # and would create actual git repositories for testing.
    # These are basic interface tests without external dependencies.

    def test_supported_vcs_types(self, detector):
        """Test that detector knows about supported VCS types."""
        # This assumes the detector has some way to list supported types
        if hasattr(detector, "supported_types"):
            supported = detector.supported_types
            assert VCSType.GIT in supported
            assert VCSType.NONE in supported

    def test_detector_with_nonexistent_path(self, detector):
        """Test detector behavior with non-existent paths."""
        nonexistent = Path("/path/that/does/not/exist")

        # Should handle gracefully without crashing
        vcs_type = detector.detect_vcs_type(nonexistent)
        assert vcs_type == VCSType.NONE

        root = detector.find_repository_root(nonexistent)
        assert root is None

        backend = detector.get_vcs_backend(nonexistent)
        assert backend is None

        is_repo = detector.is_vcs_repository(nonexistent)
        assert is_repo is False

    def test_detector_with_file_path(self, detector):
        """Test detector behavior when given a file path instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)

            # Should handle file paths gracefully
            vcs_type = detector.detect_vcs_type(file_path)
            assert vcs_type == VCSType.NONE

            is_repo = detector.is_vcs_repository(file_path)
            assert is_repo is False

    def test_search_parent_directories(self, detector):
        """Test searching parent directories for VCS root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            nested_path = Path(temp_dir) / "level1" / "level2" / "level3"
            nested_path.mkdir(parents=True)

            # Should search up to find no VCS
            root = detector.find_repository_root(nested_path)
            assert root is None

            vcs_type = detector.detect_vcs_type(nested_path)
            assert vcs_type == VCSType.NONE

    def test_detector_caching_behavior(self, detector):
        """Test if detector caches results appropriately."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)

            # Multiple calls should return consistent results
            result1 = detector.detect_vcs_type(path)
            result2 = detector.detect_vcs_type(path)
            assert result1 == result2

            repo1 = detector.is_vcs_repository(path)
            repo2 = detector.is_vcs_repository(path)
            assert repo1 == repo2

    def test_detector_error_handling(self, detector):
        """Test detector error handling with invalid inputs."""
        # Test with None path
        try:
            detector.detect_vcs_type(None)
            # Should either handle gracefully or raise appropriate error
        except (TypeError, AttributeError):
            # Expected for None input
            pass

    def test_backend_factory_pattern(self, detector):
        """Test that detector acts as factory for VCS backends."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)

            # Should return appropriate backend or None
            backend = detector.get_vcs_backend(path)

            if backend is not None:
                # If backend is returned, it should have the correct interface
                assert hasattr(backend, "get_type")
                assert hasattr(backend, "is_repository")
                assert hasattr(backend, "get_status")
                assert hasattr(backend, "get_current_branch")
            else:
                # None is acceptable for non-VCS directories
                assert backend is None


class TestVCSDetectorAdvanced:
    """Advanced tests for VCS detector functionality."""

    @pytest.fixture
    def detector(self):
        """Create VCS detector instance."""
        return VCSDetector()

    @pytest.fixture
    def git_repo_dir(self):
        """Create a temporary directory with .git folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()
            yield Path(temp_dir)

    def test_detect_git_repository(self, detector, git_repo_dir):
        """Test detection of Git repository."""
        vcs_type = detector.detect_vcs_type(git_repo_dir)
        assert vcs_type == VCSType.GIT

    def test_detect_git_in_subdirectory(self, detector, git_repo_dir):
        """Test Git detection from subdirectory."""
        subdir = git_repo_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)

        vcs_type = detector.detect_vcs_type(subdir)
        assert vcs_type == VCSType.GIT

    def test_detect_git_from_file_in_repo(self, detector, git_repo_dir):
        """Test Git detection when given a file path in repository."""
        test_file = git_repo_dir / "test.txt"
        test_file.write_text("test content")

        vcs_type = detector.detect_vcs_type(test_file)
        assert vcs_type == VCSType.GIT

    def test_get_backend_returns_git_backend(self, detector, git_repo_dir):
        """Test getting Git backend for Git repository."""
        backend = detector.get_backend(git_repo_dir)
        assert backend is not None
        assert backend.get_type() == VCSType.GIT

    def test_get_backend_alias_method(self, detector, git_repo_dir):
        """Test backward-compatible get_vcs_backend alias."""
        backend = detector.get_vcs_backend(git_repo_dir)
        assert backend is not None
        assert backend.get_type() == VCSType.GIT

    def test_is_vcs_repository_true_for_git(self, detector, git_repo_dir):
        """Test is_vcs_repository returns True for Git repo."""
        is_repo = detector.is_vcs_repository(git_repo_dir)
        assert is_repo is True

    def test_find_repository_root_finds_git_root(self, detector, git_repo_dir):
        """Test finding Git repository root."""
        subdir = git_repo_dir / "deep" / "nested" / "path"
        subdir.mkdir(parents=True)

        root = detector.find_repository_root(subdir)
        assert root == git_repo_dir

    def test_find_repository_root_from_file(self, detector, git_repo_dir):
        """Test finding repository root from file path."""
        test_file = git_repo_dir / "subdir" / "test.txt"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("test")

        root = detector.find_repository_root(test_file)
        assert root == git_repo_dir

    def test_get_backend_by_type_git(self, detector):
        """Test getting backend by VCS type."""
        backend = detector.get_backend_by_type(VCSType.GIT)
        assert backend is not None
        assert backend.get_type() == VCSType.GIT

    def test_get_backend_by_type_none(self, detector):
        """Test getting backend for NONE type returns None."""
        backend = detector.get_backend_by_type(VCSType.NONE)
        assert backend is None

    def test_get_supported_types(self, detector):
        """Test getting list of supported VCS types."""
        supported = detector.get_supported_types()
        assert VCSType.GIT in supported
        assert isinstance(supported, list)

    def test_register_backend_adds_new_type(self, detector):
        """Test registering a new VCS backend type."""
        from mentat.vcs.interfaces import BaseVCSBackend

        class MockVCSBackend(BaseVCSBackend):
            def get_type(self):
                return VCSType.GIT

            def is_repository(self, path=None):
                return False

            def get_status(self, path=None):
                from mentat.vcs.interfaces import VCSStatus

                return VCSStatus()

            def get_current_branch(self, path=None):
                return "mock"

            def get_branches(self, path=None):
                return []

            def get_uncommitted_changes(self, path=None):
                return []

            def get_recent_commits(self, path=None, count=10):
                return []

            def get_file_history(self, path=None, file_path=None):
                return []

            def get_diff(self, path=None, file_path=None):
                return ""

        # Create a custom VCS type for testing (since we can't create new enum values)
        # We'll use GIT for the mock but register under a different backend
        original_backends = detector._backends.copy()

        # Register mock backend
        detector.register_backend(VCSType.GIT, MockVCSBackend)

        # Verify registration worked
        assert detector._backends[VCSType.GIT] == MockVCSBackend

        # Restore original backends
        detector._backends = original_backends

    def test_check_git_repository_error_handling(self, detector):
        """Test _check_git_repository error handling."""
        # Create path that might cause GitVCSBackend to fail
        nonexistent_path = Path("/definitely/does/not/exist/nowhere")

        # Should handle gracefully and return False
        result = detector._check_git_repository(nonexistent_path)
        assert result is False

    def test_parent_directory_search_stops_at_root(self, detector):
        """Test that parent directory search stops at filesystem root."""
        # Use a path that goes deep enough to test root detection
        deep_path = Path("/").resolve()  # Start from root
        if deep_path.name:  # On Windows, might be C:\ or similar
            # Create a path that we know doesn't have .git
            test_path = deep_path / "nonexistent" / "deep" / "path"
        else:
            # Unix-like system
            test_path = Path("/tmp/nonexistent/deep/path")

        # Should not find any VCS and not infinite loop
        vcs_type = detector.detect_vcs_type(test_path)
        assert vcs_type == VCSType.NONE

        root = detector.find_repository_root(test_path)
        assert root is None

    def test_file_path_handling_in_find_repository_root(self, detector, git_repo_dir):
        """Test that find_repository_root handles file paths correctly."""
        # Create a nested file
        nested_file = git_repo_dir / "dir1" / "dir2" / "file.txt"
        nested_file.parent.mkdir(parents=True)
        nested_file.write_text("content")

        # Should find root from the file path
        root = detector.find_repository_root(nested_file)
        assert root == git_repo_dir

    def test_resolve_path_in_find_repository_root(self, detector, git_repo_dir):
        """Test that find_repository_root resolves paths correctly."""
        # Create a symlink or relative path
        subdir = git_repo_dir / "subdir"
        subdir.mkdir()

        # Use relative path with ..
        relative_path = subdir / ".." / "subdir"

        root = detector.find_repository_root(relative_path)
        assert root == git_repo_dir


class TestVCSDetectorModuleFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture
    def git_repo_dir(self):
        """Create a temporary directory with .git folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()
            yield Path(temp_dir)

    def test_detect_vcs_type_function(self, git_repo_dir):
        """Test module-level detect_vcs_type function."""
        from mentat.vcs.detector import detect_vcs_type

        vcs_type = detect_vcs_type(git_repo_dir)
        assert vcs_type == VCSType.GIT

    def test_get_vcs_backend_function(self, git_repo_dir):
        """Test module-level get_vcs_backend function."""
        from mentat.vcs.detector import get_vcs_backend

        backend = get_vcs_backend(git_repo_dir)
        assert backend is not None
        assert backend.get_type() == VCSType.GIT

    def test_find_repository_root_function(self, git_repo_dir):
        """Test module-level find_repository_root function."""
        from mentat.vcs.detector import find_repository_root

        subdir = git_repo_dir / "nested"
        subdir.mkdir()

        root = find_repository_root(subdir)
        assert root == git_repo_dir

    def test_module_functions_with_no_vcs(self):
        """Test module functions with non-VCS directories."""
        from mentat.vcs.detector import detect_vcs_type, find_repository_root, get_vcs_backend

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)

            assert detect_vcs_type(path) == VCSType.NONE
            assert get_vcs_backend(path) is None
            assert find_repository_root(path) is None
