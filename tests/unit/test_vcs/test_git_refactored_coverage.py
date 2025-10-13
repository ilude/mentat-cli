"""Additional tests for refactored VCS Git methods to improve coverage."""

from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from mentat.vcs.git import GitVCSBackend
from mentat.vcs.interfaces import VCSOperationError


class TestGitVCSBackendRefactoredMethods:
    """Test the new helper methods created during complexity refactoring."""

    def test_get_commit_count_with_error(self):
        """Test _get_commit_count when git command fails."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock failed git command
            mock_run.return_value = CompletedProcess(
                args=[], returncode=1, stdout="", stderr="error"
            )

            result = backend._get_commit_count(Path("/test"), "main..origin/main")
            assert result == 0

    def test_get_commit_count_with_empty_output(self):
        """Test _get_commit_count when git returns empty output."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock successful git command with empty output
            mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="", stderr="")

            result = backend._get_commit_count(Path("/test"), "main..origin/main")
            assert result == 0

    def test_get_commit_log_output_no_commits_yet(self):
        """Test _get_commit_log_output when repository has no commits yet."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock git log failure for empty repository (Windows error)
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=128,
                stdout="",
                stderr="[WinError 267] The directory name is invalid",
            )

            result = backend._get_commit_log_output(Path("/test"), 10)
            assert result == ""

    def test_get_commit_log_output_other_error(self):
        """Test _get_commit_log_output when git log fails with other error."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock git log failure with different error
            mock_run.return_value = CompletedProcess(
                args=[], returncode=1, stdout="", stderr="fatal: not a git repository"
            )

            with pytest.raises(VCSOperationError, match="Failed to get commit history"):
                backend._get_commit_log_output(Path("/test"), 10)

    def test_parse_single_commit_invalid_format(self):
        """Test _parse_single_commit with invalid log line format."""
        backend = GitVCSBackend()

        # Test with insufficient parts (less than 5)
        result = backend._parse_single_commit(Path("/test"), "hash|author")
        assert result is None

    def test_parse_single_commit_valid_format(self):
        """Test _parse_single_commit with valid log line format."""
        backend = GitVCSBackend()

        with patch.object(backend, "_get_commit_files", return_value=["file1.py", "file2.py"]):
            line = "abc123|John Doe|john@example.com|2023-01-01|Initial commit"
            result = backend._parse_single_commit(Path("/test"), line)

            assert result is not None
            assert result.hash == "abc123"
            assert result.author == "John Doe"
            assert result.author_email == "john@example.com"
            assert result.message == "Initial commit"
            assert result.files_changed == ["file1.py", "file2.py"]

    def test_get_commit_files_error(self):
        """Test _get_commit_files when git diff-tree command fails."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock failed git diff-tree command
            mock_run.return_value = CompletedProcess(
                args=[], returncode=1, stdout="", stderr="error"
            )

            result = backend._get_commit_files(Path("/test"), "abc123")
            assert result == []

    def test_get_remote_tracking_counts_no_branch(self):
        """Test _get_remote_tracking_counts when no current branch."""
        backend = GitVCSBackend()

        ahead, behind = backend._get_remote_tracking_counts(Path("/test"), None)
        assert ahead == 0
        assert behind == 0

    def test_get_remote_tracking_counts_no_upstream(self):
        """Test _get_remote_tracking_counts when no upstream branch configured."""
        backend = GitVCSBackend()

        with patch.object(backend, "_run_git_command") as mock_run:
            # Mock failed upstream check
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=128,
                stdout="",
                stderr="fatal: no upstream configured for branch 'main'",
            )

            ahead, behind = backend._get_remote_tracking_counts(Path("/test"), "main")
            assert ahead == 0
            assert behind == 0

    def test_create_clean_status_explicit_path(self):
        """Test _create_clean_status with explicit path parameter."""
        backend = GitVCSBackend()

        status = backend._create_clean_status(explicit_path=True)
        assert status.untracked_files == 0  # int for explicit path
        assert status.is_clean is True

    def test_create_clean_status_implicit_path(self):
        """Test _create_clean_status without explicit path parameter."""
        backend = GitVCSBackend()

        status = backend._create_clean_status(explicit_path=False)
        assert status.untracked_files == []  # list for implicit path
        assert status.is_clean is True

    def test_parse_commit_log_lines_empty_input(self):
        """Test _parse_commit_log_lines with empty log output."""
        backend = GitVCSBackend()

        result = backend._parse_commit_log_lines(Path("/test"), "")
        assert result == []

    def test_parse_commit_log_lines_with_empty_lines(self):
        """Test _parse_commit_log_lines handling empty lines in output."""
        backend = GitVCSBackend()

        with patch.object(backend, "_parse_single_commit") as mock_parse:
            # Configure mock to return None for empty lines
            mock_parse.side_effect = lambda path, line: None if not line.strip() else MagicMock()

            log_output = "valid_line\n\n  \nvalid_line2"
            result = backend._parse_commit_log_lines(Path("/test"), log_output)

            # Should filter out None results from empty lines
            assert len(result) == 2  # Only valid lines should be processed
