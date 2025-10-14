"""Small helper utilities for GitVCSBackend to keep methods thin and testable.

These are intentionally small wrappers so higher-level methods in
`GitVCSBackend` remain short and easy to reason about (reduces cyclomatic
complexity for radon measurements).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .git_commands import run_git_command
from .git_parsing import (
    get_commit_count,
    get_commit_files,
    get_commit_log_output,
    parse_commit_log_lines,
    parse_commit_log_output,
)
from .interfaces import CommitInfo, VCSStatus


def is_repo_dir(path: Path) -> bool:
    """Fast filesystem-level check for a git repository."""
    try:
        if not path.exists() or not path.is_dir():
            return False
        return (path / ".git").exists()
    except Exception:
        return False


def try_rev_parse_git_dir(path: Path) -> bool:
    """Use `git rev-parse --git-dir` to detect a repository.

    This is a fall-back to the filesystem check above.
    """
    res = run_git_command(path, ["rev-parse", "--git-dir"])
    return res.returncode == 0


def normalize_branches_output(output: str) -> List[str]:
    """Normalize output from `git branch -a` into a simple list of names.

    Removes the leading `* ` marker and filters out HEAD/notes lines.
    """
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    out: List[str] = []
    for b in lines:
        if b.startswith("* "):
            b = b[2:]
        if not b or b.startswith("(") or b.startswith("HEAD"):
            continue
        out.append(b)
    return out


def diff_with_fallback(path: Path, file_path: Optional[str] = None) -> str:
    """Return a git diff, attempting `diff HEAD` then `diff` as a fallback.

    Keeps the decision logic out of the public method.
    """
    args = ["diff", "HEAD"]
    if file_path:
        args += ["--", file_path]
    res = run_git_command(path, args)
    if res.returncode != 0:
        args = ["diff"] + (["--", file_path] if file_path else [])
        res = run_git_command(path, args)
    return res.stdout if res.returncode == 0 else ""


def uncommitted_changes_list(path: Path) -> List[str]:
    """Return a list of files with uncommitted changes.

    Attempts `diff --name-only HEAD` then `diff --name-only` as a fallback to
    support repositories without a HEAD yet.
    """
    res = run_git_command(path, ["diff", "--name-only", "HEAD"])
    if res.returncode != 0:
        res = run_git_command(path, ["diff", "--name-only"])
    if res.returncode == 0:
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return []


def parse_remote_status_output(output: str) -> Dict[str, object]:
    """Parse `git remote -v` output into a dict.{"has_remote": bool, "remotes": {...}}

    The shape mirrors the previous implementation used across the codebase.
    """
    if not output.strip():
        return {"has_remote": False}
    remotes: Dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes[parts[0]] = parts[1]
    return {"has_remote": bool(remotes), "remotes": remotes}


def stash_list_from_output(output: str) -> List[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def create_clean_status(explicit_path: bool) -> VCSStatus:
    """Return a clean status object, optionally collapsing untracked files to a count."""
    return VCSStatus(
        current_branch=None,
        uncommitted_changes=0,
        untracked_files=0 if explicit_path else [],
        staged_files=[],
        ahead_commits=0,
        behind_commits=0,
        is_clean=True,
    )


def remote_tracking_counts(path: Path, current_branch: Optional[str]) -> Tuple[int, int]:
    """Return (ahead, behind) commit counts for the upstream of the provided branch."""
    if not current_branch:
        return 0, 0
    res = run_git_command(path, ["rev-parse", "--abbrev-ref", f"{current_branch}@{{upstream}}"])
    if res.returncode != 0:
        return 0, 0
    upstream = res.stdout.strip()
    if not upstream:
        return 0, 0
    ahead = get_commit_count(path, f"{upstream}..{current_branch}")
    behind = get_commit_count(path, f"{current_branch}..{upstream}")
    return ahead, behind


def current_branch(path: Path) -> Optional[str]:
    """Return the current branch name for the repository at path."""
    res = run_git_command(path, ["branch", "--show-current"])
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    res = run_git_command(path, ["rev-parse", "--abbrev-ref", "HEAD"])
    if res.returncode == 0:
        name = res.stdout.strip()
        return name if name != "HEAD" else None
    return None


def recent_commits(path: Path, count: int) -> List[CommitInfo]:
    """Return a list of recent commits for the repository."""
    log_output = get_commit_log_output(path, count)
    if not log_output:
        return []
    return parse_commit_log_lines(path, log_output, get_commit_files)


def file_history(path: Path, file_path: str, limit: Optional[int]) -> List[CommitInfo]:
    """Return commit history for a single file."""
    args: List[str] = ["log", "--pretty=format:%H|%an|%ae|%ai|%s"]
    if limit:
        args.insert(1, f"-{limit}")
    args += ["--", file_path]
    res = run_git_command(path, args)
    if res.returncode != 0:
        return []
    commits = parse_commit_log_output(res.stdout)
    for commit in commits:
        commit.files_changed = [file_path]
    return commits


def commit_info(path: Path, commit_hash: str) -> Optional[CommitInfo]:
    """Return metadata for a specific commit."""
    res = run_git_command(
        path, ["show", "--quiet", "--pretty=format:%H|%an|%ae|%ai|%s", commit_hash]
    )
    if res.returncode != 0:
        return None
    parts = res.stdout.strip().split("|", 4)
    if len(parts) < 5:
        return None
    hash_, author_name, author_email, date, message = parts
    files = get_commit_files(path, commit_hash)
    return CommitInfo(
        hash=hash_,
        author=author_name,
        date=date,
        message=message,
        files_changed=files,
        author_name=author_name,
        author_email=author_email,
    )


def staged_diff(path: Path) -> Optional[str]:
    res = run_git_command(path, ["diff", "--cached"])
    return res.stdout if res.returncode == 0 else None


def commit_diff(path: Path, commit_a: str, commit_b: str) -> Optional[str]:
    res = run_git_command(path, ["diff", f"{commit_a}..{commit_b}"])
    return res.stdout if res.returncode == 0 else None


def remote_status(path: Path) -> Dict[str, object]:
    res = run_git_command(path, ["remote", "-v"])
    if res.returncode != 0 or not res.stdout.strip():
        return {"has_remote": False}
    return parse_remote_status_output(res.stdout)


def branch_list(path: Path) -> List[str]:
    res = run_git_command(path, ["branch", "-a"])
    if res.returncode != 0:
        return []
    return normalize_branches_output(res.stdout)


def repository_commit_count(path: Path) -> int:
    res = run_git_command(path, ["rev-list", "--count", "HEAD"])
    if res.returncode == 0 and res.stdout.strip().isdigit():
        return int(res.stdout.strip())
    return 0


def stash_entries(path: Path) -> List[str]:
    res = run_git_command(path, ["stash", "list"])
    if res.returncode != 0:
        return []
    return stash_list_from_output(res.stdout)


def create_stash_entry(path: Path, message: str) -> bool:
    args = ["stash", "push"]
    if message:
        args += ["-m", message]
    res = run_git_command(path, args)
    return res.returncode == 0


def resolve_diff_request(
    base_path: Path, path_or_file: Union[Path, str], file_path: Optional[str]
) -> tuple[Path, Optional[str]]:
    if isinstance(path_or_file, Path):
        return path_or_file, file_path
    return base_path, path_or_file
