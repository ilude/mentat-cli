"""Small helper utilities for GitVCSBackend to keep methods thin and testable.

These are intentionally small wrappers so higher-level methods in
`GitVCSBackend` remain short and easy to reason about (reduces cyclomatic
complexity for radon measurements).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .git_commands import run_git_command


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
