"""Git version control system implementation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, List, Optional, Union

from .git_commands import run_git_command
from .git_parsing import (
    get_commit_count,
    get_commit_files,
    get_commit_log_output,
    parse_commit_log_lines,
    parse_commit_log_output,
    parse_git_status,
    parse_git_status_output,
    parse_single_commit,
)
from .interfaces import (
    BaseVCSBackend,
    CommitInfo,
    VCSOperationError,
    VCSStatus,
    VCSType,
)


class GitVCSBackend(BaseVCSBackend):
    """Git implementation of VCS backend."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or Path.cwd()

    def _run_git_command(self, *args: Any) -> subprocess.CompletedProcess[str]:
        if len(args) == 1:
            # Only args provided, use self._path
            return run_git_command(self._path, args[0])
        elif len(args) == 2:
            # path, args
            return run_git_command(args[0], args[1])
        else:
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

    def _parse_single_commit(self, path: Path, line: str) -> Optional[CommitInfo]:
        return parse_single_commit(path, line, self._get_commit_files)

    def _get_commit_files(self, path: Path, commit_hash: str) -> List[str]:
        return get_commit_files(path, commit_hash)

    def _parse_commit_log_lines(self, path: Path, log_output: str) -> List[CommitInfo]:
        commits = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
            c = self._parse_single_commit(path, line)
            if c:
                commits.append(c)
        return commits

    def get_type(self) -> VCSType:
        return VCSType.GIT

    def is_repository(self, path: Optional[Path] = None) -> bool:
        path = path or self._path
        try:
            if not path.exists() or not path.is_dir():
                return False
            if (path / ".git").exists():
                return True
            result = run_git_command(path, ["rev-parse", "--git-dir"])
            return result.returncode == 0
        except Exception:
            return False

    def get_status(self, path: Optional[Path] = None) -> VCSStatus:
        explicit_path = path is not None
        path = path or self._path

        if not self.is_repository(path):
            return self._create_clean_status(explicit_path)

        current_branch = self.get_current_branch(path)
        untracked_files, staged_files, uncommitted_changes = parse_git_status(path, run_git_command)
        ahead_commits, behind_commits = self._get_remote_tracking_counts(path, current_branch)

        ut_files: Any = len(untracked_files) if explicit_path else untracked_files
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
        path = path or self._path
        if not self.is_repository(path):
            return None
        res = run_git_command(path, ["branch", "--show-current"])
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        res = run_git_command(path, ["rev-parse", "--abbrev-ref", "HEAD"])
        if res.returncode == 0:
            name = res.stdout.strip()
            return name if name != "HEAD" else None
        return None

    def get_uncommitted_changes(self, path: Optional[Path] = None) -> List[str]:
        path = path or self._path
        if not self.is_repository(path):
            return []
        res = run_git_command(path, ["diff", "--name-only", "HEAD"])
        if res.returncode != 0:
            res = run_git_command(path, ["diff", "--name-only"])
        if res.returncode == 0:
            return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return []

    def get_recent_commits(self, path: Optional[Path] = None, count: int = 10) -> List[CommitInfo]:
        path = path or self._path
        if not self.is_repository(path):
            return []
        log_output = get_commit_log_output(path, count)
        if not log_output:
            return []
        return parse_commit_log_lines(path, log_output, get_commit_files)

    def get_file_history(
        self,
        path: Optional[Path] = None,
        file_path: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[CommitInfo]:
        path = path or self._path
        if not file_path or not self.is_repository(path):
            return []
        args: List[str] = ["log", "--pretty=format:%H|%an|%ae|%ai|%s"]
        if limit:
            args.insert(1, f"-{limit}")
        args += ["--", file_path]
        res = run_git_command(path, args)
        if res.returncode != 0:
            return []
        commits: List[CommitInfo] = []
        for line in res.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) >= 5:
                h, an, ae, dt, msg = parts
                commits.append(
                    CommitInfo(
                        hash=h,
                        author=an,
                        date=dt,
                        message=msg,
                        files_changed=[file_path],
                        author_name=an,
                        author_email=ae,
                    )
                )
        return commits

    def get_diff(self, path: Optional[Path] = None, file_path: Optional[str] = None) -> str:
        path = path or self._path
        if not self.is_repository(path):
            return ""
        args: List[str] = ["diff", "HEAD"]
        if file_path:
            args += ["--", file_path]
        res = run_git_command(path, args)
        if res.returncode != 0:
            args = ["diff"] + (["--", file_path] if file_path else [])
            res = run_git_command(path, args)
        return res.stdout if res.returncode == 0 else ""

    def get_commit_history(self, path: Optional[Path] = None, limit: int = 10) -> List[CommitInfo]:
        return self.get_recent_commits(path or self._path, count=limit)

    def get_commit_info(
        self, commit_hash: str, path: Optional[Path] = None
    ) -> Optional[CommitInfo]:
        path = path or self._path
        if not self.is_repository(path):
            return None
        res = run_git_command(
            path, ["show", "--quiet", "--pretty=format:%H|%an|%ae|%ai|%s", commit_hash]
        )
        if res.returncode != 0:
            return None
        parts = res.stdout.strip().split("|", 4)
        if len(parts) < 5:
            return None
        h, an, ae, dt, msg = parts
        files = get_commit_files(path, commit_hash)
        return CommitInfo(
            hash=h,
            author=an,
            date=dt,
            message=msg,
            files_changed=files,
            author_name=an,
            author_email=ae,
        )

    def get_staged_diff(self, path: Optional[Path] = None) -> Optional[str]:
        path = path or self._path
        if not self.is_repository(path):
            return None
        res = run_git_command(path, ["diff", "--cached"])
        return res.stdout if res.returncode == 0 else None

    def get_commit_diff(
        self,
        path: Optional[Path] = None,
        commit_a: Optional[str] = None,
        commit_b: Optional[str] = None,
    ) -> Optional[str]:
        path = path or self._path
        if not self.is_repository(path) or not commit_a or not commit_b:
            return None
        res = run_git_command(path, ["diff", f"{commit_a}..{commit_b}"])
        return res.stdout if res.returncode == 0 else None

    def get_remote_status(self, path: Optional[Path] = None) -> dict:
        path = path or self._path
        if not self.is_repository(path):
            return {"has_remote": False}
        res = run_git_command(path, ["remote", "-v"])
        if res.returncode != 0 or not res.stdout.strip():
            return {"has_remote": False}
        remotes: dict[str, str] = {}
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                remotes[parts[0]] = parts[1]
        return {"has_remote": bool(remotes), "remotes": remotes}

    def get_branches(self, path: Optional[Path] = None) -> List[str]:
        path = path or self._path
        if not self.is_repository(path):
            return []
        res = run_git_command(path, ["branch", "-a"])
        if res.returncode != 0:
            return []
        branches: List[str] = []
        for line in res.stdout.splitlines():
            b = line.strip()
            if b.startswith("* "):
                b = b[2:]
            if b and not b.startswith("(") and not b.startswith("HEAD"):
                branches.append(b)
        return branches

    def get_repository_info(self, path: Optional[Path] = None) -> dict:
        path = path or self._path
        status = self.get_status(path)
        count = 0
        res = run_git_command(path, ["rev-list", "--count", "HEAD"])
        if res.returncode == 0 and res.stdout.strip().isdigit():
            count = int(res.stdout.strip())
        return {
            "type": "git",
            "path": str(path),
            "branch": status.current_branch,
            "ahead": status.ahead_commits,
            "behind": status.behind_commits,
            "is_clean": status.is_clean,
            "has_uncommitted_changes": not status.is_clean,
            "commit_count": count,
        }

    def get_stash_list(self, path: Optional[Path] = None) -> List[str]:
        path = path or self._path
        if not self.is_repository(path):
            return []
        res = run_git_command(path, ["stash", "list"])
        if res.returncode != 0:
            return []
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]

    def create_stash(self, path: Optional[Path] = None, message: str = "") -> bool:
        path = path or self._path
        if not self.is_repository(path):
            return False
        args = ["stash", "push"]
        if message:
            args += ["-m", message]
        res = run_git_command(path, args)
        return res.returncode == 0

    def get_file_diff(
        self, path_or_file: Union[Path, str], file_path: Optional[str] = None
    ) -> Optional[str]:
        path, filename = self._resolve_diff_parameters(path_or_file, file_path)
        if not self._can_generate_diff(path, filename):
            return None
        diff = self.get_diff(path, filename)
        return diff if diff is not None else ""

    def _resolve_diff_parameters(
        self, path_or_file: Union[Path, str], file_path: Optional[str]
    ) -> tuple[Path, Optional[str]]:
        if isinstance(path_or_file, Path):
            return path_or_file, file_path
        return self._path, path_or_file

    def _can_generate_diff(self, path: Path, filename: Optional[str]) -> bool:
        if not filename:
            return False
        if not self.is_repository(path):
            return False
        if not (path / filename).exists():
            return False
        return True

    def _create_clean_status(self, explicit_path: bool) -> VCSStatus:
        return VCSStatus(
            current_branch=None,
            uncommitted_changes=0,
            untracked_files=0 if explicit_path else [],
            staged_files=[],
            ahead_commits=0,
            behind_commits=0,
            is_clean=True,
        )

    # Parsing helpers now in git_parsing.py

    def _get_remote_tracking_counts(
        self, path: Path, current_branch: Optional[str]
    ) -> tuple[int, int]:
        if not current_branch:
            return 0, 0
        res = run_git_command(path, ["rev-parse", "--abbrev-ref", f"{current_branch}@{{upstream}}"])
        if res.returncode != 0:
            return 0, 0
        upstream = res.stdout.strip()
        ahead = get_commit_count(path, f"{upstream}..{current_branch}")
        behind = get_commit_count(path, f"{current_branch}..{upstream}")
        return ahead, behind
