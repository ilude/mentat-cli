import subprocess
from pathlib import Path
from typing import List


def run_git_command(
    cwd: Path,
    cmd: List[str],
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as e:
        return subprocess.CompletedProcess(["git"] + cmd, 1, "", str(e))
