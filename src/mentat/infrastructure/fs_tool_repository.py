from __future__ import annotations

import subprocess
import shlex
from pathlib import Path
from typing import Iterable, List

from .repositories import ToolRepository, ToolSpec, _load_tool_toml


class FsToolRepository(ToolRepository):
    def __init__(self, tools_dir: Path) -> None:
        self.tools_dir = tools_dir

    def _iter_tool_files(self) -> Iterable[Path]:
        td = self.tools_dir
        if not td.exists() or not td.is_dir():
            return []
        return sorted(td.glob("*.toml"))

    def list_tools(self) -> Iterable[ToolSpec]:
        for p in self._iter_tool_files():
            spec = _load_tool_toml(p)
            if spec:
                yield spec

    def get_tool(self, name: str) -> ToolSpec | None:
        for spec in self.list_tools():
            if spec.name == name:
                return spec
        return None

    def run_tool(self, name: str, args: List[str]) -> int:
        spec = self.get_tool(name)
        if not spec:
            return 2  # not found
        # Compose command: allow args appended to the command string
        base = shlex.split(spec.command)
        cmd = base + args
        proc = subprocess.run(cmd)
        return proc.returncode
