from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, List, Optional

from .git_utils import StagedFile
from .interfaces import CommitInfo, VCSOperationError, VCSStatus


def get_commit_count(path: Path, rev_range: str) -> int:
    from .git_commands import run_git_command

    res = run_git_command(path, ["rev-list", "--count", rev_range])
    if res.returncode == 0:
        try:
            return int(res.stdout.strip() or 0)
        except ValueError:
            return 0
    return 0


def get_commit_log_output(path: Path, count: int) -> str:
    from .git_commands import run_git_command
    from .interfaces import VCSOperationError

    res = run_git_command(path, ["log", f"-{count}", "--pretty=format:%H|%an|%ae|%ai|%s"])
    if res.returncode != 0:
        if (
            "does not have any commits yet" in res.stderr
            or "directory name is invalid" in res.stderr
        ):
            return ""
        # For all other errors, raise
        raise VCSOperationError(f"Failed to get commit history: {res.stderr}")
    return res.stdout.strip()


def get_commit_files(path: Path, commit_hash: str) -> list[str]:
    from .git_commands import run_git_command

    res = run_git_command(path, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash])
    if res.returncode != 0:
        return []
    return [f.strip() for f in res.stdout.splitlines() if f.strip()]


def parse_git_status_output(output: str) -> VCSStatus:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    untracked_files: List[str] = []
    staged: List[Any] = []
    for line in lines:
        if line.startswith("??"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                untracked_files.append(parts[1])
        else:
            code = line[:2]
            if code[0] != " ":
                staged.append(StagedFile(path=line[3:], status=code.strip()))
    uncommitted = len(lines) - len(untracked_files)
    return VCSStatus(
        current_branch=None,
        uncommitted_changes=uncommitted,
        untracked_files=untracked_files,
        staged_files=staged,
        ahead_commits=0,
        behind_commits=0,
        is_clean=len(lines) == 0,
    )


def parse_git_status(
    path: Path,
    run_git_command: Callable[[Path, List[str]], subprocess.CompletedProcess[str]],
) -> tuple[List[str], List[Any], int]:
    res = run_git_command(path, ["status", "--porcelain"])
    if res.returncode != 0:
        raise VCSOperationError(f"Git status failed: {res.stderr}")
    lines = [line for line in res.stdout.splitlines()]
    untracked: List[str] = []
    staged: List[Any] = []
    uncommitted = 0
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("??"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                untracked.append(parts[1])
            continue
        code = line[:2]
        file_path = line[3:] if len(line) > 3 else ""
        if code[0] != " ":
            staged.append(StagedFile(path=file_path, status=code.strip()))
        uncommitted += 1
    return untracked, staged, uncommitted


def parse_commit_log_lines(
    path: Path,
    log_output: str,
    get_commit_files: Callable[[Path, str], List[str]],
) -> List[CommitInfo]:
    commits: List[CommitInfo] = []
    for line in log_output.splitlines():
        if not line.strip():
            continue
        c = parse_single_commit(path, line, get_commit_files)
        if c:
            commits.append(c)
    return commits


def parse_single_commit(
    path: Path,
    line: str,
    get_commit_files: Callable[[Path, str], List[str]],
) -> Optional[CommitInfo]:
    parts = line.split("|", 4)
    if len(parts) < 5:
        return None
    h, an, ae, dt, msg = parts
    files = get_commit_files(path, h)
    return CommitInfo(
        hash=h,
        author=an,
        date=dt,
        message=msg,
        files_changed=files,
        author_name=an,
        author_email=ae,
    )


def parse_commit_log_output(output: str) -> List[CommitInfo]:
    commits: List[CommitInfo] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        h, an, ae, dt, msg = parts
        commits.append(
            CommitInfo(
                hash=h,
                author=an,
                date=dt,
                message=msg,
                files_changed=[],
                author_name=an,
                author_email=ae,
            )
        )
    return commits
