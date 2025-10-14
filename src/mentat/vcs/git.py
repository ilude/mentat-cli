"""Git version control system implementation."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from . import git_helpers as gh
from .git_commands import run_git_command
from .git_parsing import parse_git_status
from .git_private import GitPrivateAPI
from .interfaces import (
    BaseVCSBackend,
    CommitInfo,
    VCSStatus,
    VCSType,
)


class GitVCSBackend(GitPrivateAPI, BaseVCSBackend):
    """Git implementation of VCS backend."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or Path.cwd()

    def get_type(self) -> VCSType:
        return VCSType.GIT

    def is_repository(self, path: Optional[Path] = None) -> bool:
        path = path or self._path
        # Prefer a fast filesystem check, fall back to git invocation
        if gh.is_repo_dir(path):
            return True
        try:
            return run_git_command(path, ["rev-parse", "--git-dir"]).returncode == 0
        except Exception:
            return False

    def get_status(self, path: Optional[Path] = None) -> VCSStatus:
        explicit_path = path is not None
        path = path or self._path

        if not self.is_repository(path):
            return gh.create_clean_status(explicit_path)

        current_branch = self.get_current_branch(path)
        untracked_files, staged_files, uncommitted_changes = parse_git_status(path, run_git_command)
        ahead_commits, behind_commits = gh.remote_tracking_counts(path, current_branch)

        ut_files: Union[int, List[str]] = len(untracked_files) if explicit_path else untracked_files
        is_clean = (uncommitted_changes == 0) and (len(untracked_files) == 0)

        return VCSStatus(
            current_branch=current_branch,
            uncommitted_changes=uncommitted_changes,
            untracked_files=ut_files,
            staged_files=staged_files,
            ahead_commits=ahead_commits,
            behind_commits=behind_commits,
            is_clean=is_clean,
        )

    def get_current_branch(self, path: Optional[Path] = None) -> Optional[str]:
        target = path or self._path
        return gh.current_branch(target) if self.is_repository(target) else None

    def get_uncommitted_changes(self, path: Optional[Path] = None) -> List[str]:
        target = path or self._path
        return gh.uncommitted_changes_list(target) if self.is_repository(target) else []

    def get_recent_commits(self, path: Optional[Path] = None, count: int = 10) -> List[CommitInfo]:
        target = path or self._path
        return gh.recent_commits(target, count) if self.is_repository(target) else []

    def get_file_history(
        self,
        path: Optional[Path] = None,
        file_path: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[CommitInfo]:
        path = path or self._path
        if not file_path or not self.is_repository(path):
            return []
        return gh.file_history(path, file_path, limit)

    def get_diff(self, path: Optional[Path] = None, file_path: Optional[str] = None) -> str:
        target = path or self._path
        return gh.diff_with_fallback(target, file_path) if self.is_repository(target) else ""

    def get_commit_history(self, path: Optional[Path] = None, limit: int = 10) -> List[CommitInfo]:
        return self.get_recent_commits(path or self._path, count=limit)

    def get_commit_info(
        self, commit_hash: str, path: Optional[Path] = None
    ) -> Optional[CommitInfo]:
        target = path or self._path
        return gh.commit_info(target, commit_hash) if self.is_repository(target) else None

    def get_staged_diff(self, path: Optional[Path] = None) -> Optional[str]:
        target = path or self._path
        return gh.staged_diff(target) if self.is_repository(target) else None

    def get_commit_diff(
        self,
        path: Optional[Path] = None,
        commit_a: Optional[str] = None,
        commit_b: Optional[str] = None,
    ) -> Optional[str]:
        target = path or self._path
        if not self.is_repository(target) or not commit_a or not commit_b:
            return None
        return gh.commit_diff(target, commit_a, commit_b)

    def get_remote_status(self, path: Optional[Path] = None) -> dict:
        target = path or self._path
        return gh.remote_status(target) if self.is_repository(target) else {"has_remote": False}

    def get_branches(self, path: Optional[Path] = None) -> List[str]:
        target = path or self._path
        return gh.branch_list(target) if self.is_repository(target) else []

    def get_repository_info(self, path: Optional[Path] = None) -> dict:
        path = path or self._path
        status = self.get_status(path)
        return {
            "type": "git",
            "path": str(path),
            "branch": status.current_branch,
            "ahead": status.ahead_commits,
            "behind": status.behind_commits,
            "is_clean": status.is_clean,
            "has_uncommitted_changes": not status.is_clean,
            "commit_count": gh.repository_commit_count(path),
        }

    def get_stash_list(self, path: Optional[Path] = None) -> List[str]:
        target = path or self._path
        return gh.stash_entries(target) if self.is_repository(target) else []

    def create_stash(self, path: Optional[Path] = None, message: str = "") -> bool:
        target = path or self._path
        return gh.create_stash_entry(target, message) if self.is_repository(target) else False

    def get_file_diff(
        self, path_or_file: Union[Path, str], file_path: Optional[str] = None
    ) -> Optional[str]:
        path, filename = gh.resolve_diff_request(self._path, path_or_file, file_path)
        if not filename:
            return None
        if not self.is_repository(path):
            return None
        if not (path / filename).exists():
            return None
        diff = self.get_diff(path, filename)
        return diff if diff is not None else ""
