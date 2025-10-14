"""Private helper mixin exposing legacy GitVCSBackend internals for tests."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess
from typing import List, Optional, Sequence, cast

from .git_commands import run_git_command
from .git_helpers import create_clean_status
from .git_parsing import (
    parse_commit_log_output,
    parse_git_status_output,
    parse_single_commit,
)
from .interfaces import CommitInfo, VCSOperationError, VCSStatus


class GitPrivateAPI:
    """Compatibility layer with thin wrappers used by existing unit tests."""

    _path: Path

    def _run_git_command(self, *args: object) -> CompletedProcess[str]:
        if len(args) == 1:
            command = cast(Sequence[str], args[0])
            return run_git_command(self._path, list(command))
        if len(args) == 2:
            repo_path = cast(Path, args[0])
            command = cast(Sequence[str], args[1])
            return run_git_command(repo_path, list(command))
        raise TypeError("_run_git_command expects (args) or (path, args)")

    def _get_commit_count(self, path: Path, rev_range: str) -> int:
        res = self._run_git_command(path, ["rev-list", "--count", rev_range])
        if res.returncode == 0:
            try:
                return int(res.stdout.strip() or 0)
            except ValueError:
                return 0
        return 0

    def _get_commit_log_output(self, path: Path, count: int) -> str:
        res = self._run_git_command(path, ["log", f"-{count}", "--pretty=format:%H|%an|%ae|%ai|%s"])
        if res.returncode != 0:
            if (
                "does not have any commits yet" in res.stderr
                or "directory name is invalid" in res.stderr
            ):
                return ""
            raise VCSOperationError(f"Failed to get commit history: {res.stderr}")
        return res.stdout.strip()

    def _parse_status_output(self, output: str) -> VCSStatus:
        return parse_git_status_output(output)

    def _parse_commit_log_output(self, output: str) -> List[CommitInfo]:
        return parse_commit_log_output(output)

    def _get_commit_files(self, path: Path, commit_hash: str) -> List[str]:
        res = self._run_git_command(
            path, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
        )
        if res.returncode != 0:
            return []
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]

    def _parse_single_commit(self, path: Path, line: str) -> Optional[CommitInfo]:
        return parse_single_commit(path, line, self._get_commit_files)

    def _parse_commit_log_lines(self, path: Path, log_output: str) -> List[CommitInfo]:
        commits: List[CommitInfo] = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
            commit = self._parse_single_commit(path, line)
            if commit:
                commits.append(commit)
        return commits

    def _create_clean_status(self, explicit_path: bool) -> VCSStatus:
        return create_clean_status(explicit_path)

    def _get_remote_tracking_counts(
        self, path: Path, current_branch: Optional[str]
    ) -> tuple[int, int]:
        if not current_branch:
            return 0, 0
        res = self._run_git_command(
            path, ["rev-parse", "--abbrev-ref", f"{current_branch}@{{upstream}}"]
        )
        if res.returncode != 0:
            return 0, 0
        upstream = res.stdout.strip()
        if not upstream:
            return 0, 0
        ahead = self._get_commit_count(path, f"{upstream}..{current_branch}")
        behind = self._get_commit_count(path, f"{current_branch}..{upstream}")
        return ahead, behind
