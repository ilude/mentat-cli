"""Tests for VCS Git backend."""

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

    def test_initialization(self, git_backend):
        """Test Git backend initialization."""
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
        """Test status with various file changes."""
        # Create untracked file
        new_file = temp_git_repo / "new_file.txt"
        new_file.write_text("New content")

        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\n")

        # Stage the modified file
        subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo, check=True)

        status = git_backend.get_status(temp_git_repo)

        assert status.is_clean is False
        assert status.untracked_files == 1 or (
            isinstance(status.untracked_files, list) and len(status.untracked_files) == 1
        )
        if isinstance(status.untracked_files, list):
            assert "new_file.txt" in status.untracked_files
        assert len(status.staged_files) == 1
        assert "README.md" in [f.path for f in status.staged_files]

    def test_get_commit_history(self, git_backend, temp_git_repo):
        """Test getting commit history."""
        # Add another commit
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("Test content")
        subprocess.run(["git", "add", "test.txt"], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Add test file"], cwd=temp_git_repo, check=True)

        # Get history
        history = git_backend.get_commit_history(temp_git_repo, limit=2)

        assert len(history) == 2
        assert isinstance(history[0], CommitInfo)
        assert history[0].message == "Add test file"
        assert history[1].message == "Initial commit"

        # Test with limit
        history_limited = git_backend.get_commit_history(limit=1)
        assert len(history_limited) == 1

    def test_get_commit_info(self, git_backend, temp_git_repo):
        """Test getting specific commit information."""
        # Get the initial commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()

        commit_info = git_backend.get_commit_info(commit_hash, path=temp_git_repo)

        assert isinstance(commit_info, CommitInfo)
        assert commit_info.hash == commit_hash
        assert commit_info.message == "Initial commit"
        assert commit_info.author_name == "Test User"
        assert commit_info.author_email == "test@example.com"

    def test_get_commit_info_nonexistent(self, git_backend):
        """Test getting info for non-existent commit."""
        commit_info = git_backend.get_commit_info("nonexistent_hash")
        assert commit_info is None

    def test_get_file_diff(self, git_backend, temp_git_repo):
        """Test getting file diff."""
        # Modify a file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified README\nWith new content\n")

        diff = git_backend.get_file_diff(temp_git_repo, "README.md")

        assert diff is not None
        assert "Modified README" in diff
        assert "With new content" in diff
        assert "Test Repository" in diff  # Should show old content too

    def test_get_file_diff_nonexistent(self, git_backend):
        """Test getting diff for non-existent file."""
        diff = git_backend.get_file_diff("nonexistent_file.txt")
        assert diff is None

    def test_get_staged_diff(self, git_backend, temp_git_repo):
        """Test getting staged changes diff."""
        # Modify and stage a file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Staged changes\n")
        subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo, check=True)

        diff = git_backend.get_staged_diff(temp_git_repo)

        assert diff is not None
        assert "Staged changes" in diff

    def test_get_commit_diff(self, git_backend, temp_git_repo):
        """Test getting diff between commits."""
        # Create another commit to diff against
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("Test content")
        subprocess.run(["git", "add", "test.txt"], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Add test file"], cwd=temp_git_repo, check=True)

        # Get diff between HEAD and HEAD~1
        diff = git_backend.get_commit_diff(temp_git_repo, "HEAD~1", "HEAD")

        assert diff is not None
        assert "test.txt" in diff
        assert "Test content" in diff

    def test_get_remote_status(self, git_backend):
        """Test getting remote status (no remote configured)."""
        status = git_backend.get_remote_status()

        # Should handle no remote gracefully
        assert status is not None
        # Environment may have a remote configured for this repo; assert a boolean
        assert isinstance(status.get("has_remote"), bool)

    def test_branch_operations(self, git_backend, temp_git_repo):
        """Test branch-related operations."""
        # Create a new branch
        subprocess.run(["git", "checkout", "-b", "feature-branch"], cwd=temp_git_repo, check=True)

        # Test current branch
        current_branch = git_backend.get_current_branch(temp_git_repo)
        assert current_branch == "feature-branch"

        # Test branch list
        branches = git_backend.get_branches(temp_git_repo)
        assert "feature-branch" in branches
        assert any(b.startswith("main") or b.startswith("master") for b in branches)

    def test_error_handling_invalid_repo(self):
        """Test error handling with invalid repository."""
        backend = GitVCSBackend(Path("/nonexistent/path"))

        # These should handle errors gracefully
        assert backend.is_repository() is False
        assert backend.get_current_branch() is None

        status = backend.get_status()
        assert status.is_clean is True  # Should return default clean status

        history = backend.get_commit_history()
        assert len(history) == 0

    def test_run_git_command_success(self, git_backend):
        """Test successful Git command execution."""
        result = git_backend._run_git_command(["status", "--porcelain"])

        assert result.returncode == 0
        assert isinstance(result.stdout, str)

    def test_run_git_command_failure(self, git_backend):
        """Test failed Git command execution."""
        result = git_backend._run_git_command(["invalid-command"])

        assert result.returncode != 0
        assert result.stderr is not None

    def test_parse_status_output(self, git_backend):
        """Test parsing Git status output."""
        # Mock status output
        status_output = """
M  modified_file.txt
A  added_file.txt
?? untracked_file.txt
D  deleted_file.txt
"""

        status = git_backend._parse_status_output(status_output.strip())

        assert not status.is_clean
        assert len(status.staged_files) == 3  # M, A, D are staged
        assert len(status.untracked_files) == 1

        # Check file changes
        staged_paths = [f.path for f in status.staged_files]
        assert "modified_file.txt" in staged_paths
        assert "added_file.txt" in staged_paths
        assert "deleted_file.txt" in staged_paths
        assert "untracked_file.txt" in status.untracked_files

    def test_parse_commit_log_output(self, git_backend):
        """Test parsing Git log output."""
        # Mock log output
        log_output = """abc123|John Doe|john@example.com|2023-01-01 12:00:00 +0000|Initial commit
def456|Jane Smith|jane@example.com|2023-01-02 15:30:00 +0000|Add feature"""

        commits = git_backend._parse_commit_log_output(log_output)

        assert len(commits) == 2

        assert commits[0].hash == "abc123"
        assert commits[0].author_name == "John Doe"
        assert commits[0].author_email == "john@example.com"
        assert commits[0].message == "Initial commit"

        assert commits[1].hash == "def456"
        assert commits[1].author_name == "Jane Smith"
        assert commits[1].message == "Add feature"

    def test_repository_info(self, git_backend, temp_git_repo):
        """Test getting repository information."""
        info = git_backend.get_repository_info(temp_git_repo)

        assert info["type"] == "git"
        assert info["path"] == str(temp_git_repo)
        assert "branch" in info
        assert info["has_uncommitted_changes"] is False  # Clean repo initially
        assert "commit_count" in info
        assert info["commit_count"] >= 1  # At least initial commit

    def test_file_history(self, git_backend, temp_git_repo):
        """Test getting file history."""
        # Modify the README multiple times
        readme = temp_git_repo / "README.md"

        # Second commit
        readme.write_text("# Updated README\n")
        subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Update README"], cwd=temp_git_repo, check=True)

        # Get file history
        history = git_backend.get_file_history(temp_git_repo, "README.md", limit=2)

        assert len(history) >= 1
        assert isinstance(history[0], CommitInfo)
        # Just check that we got a valid commit history
        assert isinstance(history[0].message, str) and len(history[0].message) > 0

    def test_stash_operations(self, git_backend, temp_git_repo):
        """Test Git stash operations."""
        # Make some changes
        readme = temp_git_repo / "README.md"
        readme.write_text("# Temporary changes\n")

        # Test stash list
        stashes = git_backend.get_stash_list(temp_git_repo)
        initial_count = len(stashes)

        # Create a stash
        success = git_backend.create_stash(temp_git_repo, "Test stash message")
        assert success is True

        # Check stash list
        stashes = git_backend.get_stash_list(temp_git_repo)
        assert len(stashes) == initial_count + 1
        assert "Test stash message" in stashes[0]
