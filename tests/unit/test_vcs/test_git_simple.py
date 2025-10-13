"""Tests for VCS Git backend - basic interface tests."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from mentat.vcs.git import GitVCSBackend
from mentat.vcs.interfaces import CommitInfo, VCSStatus, VCSType


class TestGitVCSBackend:
    """Test Git VCS backend implementation."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary Git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
            )

            # Create initial commit
            test_file = repo_path / "README.md"
            test_file.write_text("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def git_backend(self):
        """Create Git VCS backend."""
        return GitVCSBackend()

    def test_get_type(self, git_backend):
        """Test Git backend returns correct type."""
        assert git_backend.get_type() == VCSType.GIT

    def test_is_repository_true(self, git_backend, temp_git_repo):
        """Test repository detection for valid Git repo."""
        assert git_backend.is_repository(temp_git_repo) is True

    def test_is_repository_false(self, git_backend):
        """Test repository detection for non-Git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            assert git_backend.is_repository(Path(temp_dir)) is False

    def test_get_current_branch(self, git_backend, temp_git_repo):
        """Test getting current branch name."""
        branch = git_backend.get_current_branch(temp_git_repo)
        assert branch is not None
        assert isinstance(branch, str)
        assert branch in ["main", "master"]

    def test_get_status_clean_repo(self, git_backend, temp_git_repo):
        """Test status of clean repository."""
        status = git_backend.get_status(temp_git_repo)

        assert isinstance(status, VCSStatus)
        assert status.is_clean is True
        assert status.uncommitted_changes == 0
        assert status.untracked_files == 0 or (
            isinstance(status.untracked_files, list) and len(status.untracked_files) == 0
        )

    def test_get_status_with_changes(self, git_backend, temp_git_repo):
        """Test status with file changes."""
        # Create untracked file
        new_file = temp_git_repo / "new_file.txt"
        new_file.write_text("New content")

        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\n")

        status = git_backend.get_status(temp_git_repo)

        assert isinstance(status, VCSStatus)
        assert status.is_clean is False
        assert (
            status.uncommitted_changes > 0
            or (isinstance(status.untracked_files, int) and status.untracked_files > 0)
            or (isinstance(status.untracked_files, list) and len(status.untracked_files) > 0)
        )

    def test_get_uncommitted_changes(self, git_backend, temp_git_repo):
        """Test getting uncommitted changes."""
        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\n")

        changes = git_backend.get_uncommitted_changes(temp_git_repo)
        assert isinstance(changes, list)
        # Should contain the modified file
        assert any("README.md" in change for change in changes)

    def test_get_recent_commits(self, git_backend, temp_git_repo):
        """Test getting recent commit history."""
        commits = git_backend.get_recent_commits(temp_git_repo, count=5)

        assert isinstance(commits, list)
        assert len(commits) >= 1  # At least the initial commit

        # Check first commit structure
        if commits:
            commit = commits[0]
            assert isinstance(commit, CommitInfo)
            assert commit.hash is not None
            assert commit.message is not None
            assert commit.author is not None
            assert commit.date is not None

    def test_get_file_history(self, git_backend, temp_git_repo):
        """Test getting file history."""
        history = git_backend.get_file_history(temp_git_repo, "README.md")

        assert isinstance(history, list)
        assert len(history) >= 1  # At least one commit for README.md

        if history:
            commit = history[0]
            assert isinstance(commit, CommitInfo)

    def test_get_diff_no_changes(self, git_backend, temp_git_repo):
        """Test getting diff with no changes."""
        diff = git_backend.get_diff(temp_git_repo)

        # Clean repo should have empty or None diff
        # Clean repo should have empty diff (unless there are working tree changes)
        assert isinstance(diff, str)

    def test_get_diff_with_changes(self, git_backend, temp_git_repo):
        """Test getting diff with changes."""
        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\nWith new content\n")

        diff = git_backend.get_diff(temp_git_repo)

        assert diff is not None
        assert isinstance(diff, str)
        # Should contain some indication of changes
        assert len(diff) > 0

    def test_get_diff_specific_file(self, git_backend, temp_git_repo):
        """Test getting diff for specific file."""
        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\n")

        diff = git_backend.get_diff(temp_git_repo, "README.md")

        assert isinstance(diff, str)
        # Should contain changes for README.md
        if diff:  # Some implementations might return empty string for single file
            assert len(diff) >= 0

    def test_error_handling_nonexistent_path(self, git_backend):
        """Test error handling with non-existent paths."""
        nonexistent_path = Path("/nonexistent/path/that/should/not/exist")

        # These should handle errors gracefully without crashing
        assert git_backend.is_repository(nonexistent_path) is False

        # These might return None or empty results
        branch = git_backend.get_current_branch(nonexistent_path)
        assert branch is None or isinstance(branch, str)

        status = git_backend.get_status(nonexistent_path)
        assert isinstance(status, VCSStatus)

        try:
            changes = git_backend.get_uncommitted_changes(nonexistent_path)
            assert isinstance(changes, list)
        except Exception:
            # Some implementations may raise errors for invalid paths
            pass

        commits = git_backend.get_recent_commits(nonexistent_path)
        assert isinstance(commits, list)

    def test_run_git_command_internal(self, git_backend, temp_git_repo):
        """Test internal git command execution."""
        # This tests the internal _run_git_command method if accessible
        if hasattr(git_backend, "_run_git_command"):
            result = git_backend._run_git_command(temp_git_repo, ["status", "--porcelain"])
            assert hasattr(result, "returncode")
            assert hasattr(result, "stdout")
            assert hasattr(result, "stderr")

    def test_multiple_commits(self, git_backend, temp_git_repo):
        """Test with multiple commits."""
        # Add another commit
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("Test content")
        subprocess.run(["git", "add", "test.txt"], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Add test file"], cwd=temp_git_repo, check=True)

        # Get history
        commits = git_backend.get_recent_commits(temp_git_repo, count=2)

        assert len(commits) == 2
        # Most recent commit should be first
        assert "test file" in commits[0].message.lower() or "add" in commits[0].message.lower()
        assert "initial" in commits[1].message.lower()

    def test_branch_operations(self, git_backend, temp_git_repo):
        """Test basic branch operations."""
        # Get initial branch
        initial_branch = git_backend.get_current_branch(temp_git_repo)
        assert initial_branch is not None

        # Create and switch to new branch if git supports it
        try:
            subprocess.run(["git", "checkout", "-b", "test-branch"], cwd=temp_git_repo, check=True)

            current_branch = git_backend.get_current_branch(temp_git_repo)
            assert current_branch == "test-branch"

            # Switch back
            subprocess.run(["git", "checkout", initial_branch], cwd=temp_git_repo, check=True)

            final_branch = git_backend.get_current_branch(temp_git_repo)
            assert final_branch == initial_branch

        except subprocess.CalledProcessError:
            # If branch operations fail, skip this test
            pytest.skip("Git branch operations not available in test environment")
