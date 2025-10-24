from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Iterable, List

from .repositories import ToolExecutionResult, ToolRepository, ToolSpec, _load_tool_toml


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

    def _build_command(self, spec: ToolSpec, args: List[str]) -> List[str]:
        base = shlex.split(spec.command)
        return base + list(args)

    def run_tool(self, name: str, args: List[str]) -> int:
        spec = self.get_tool(name)
        if not spec:
            return 2  # Not found sentinel
        cmd = self._build_command(spec, args)
        proc = subprocess.run(cmd)
        return proc.returncode

    def execute_tool(self, name: str, args: List[str]) -> ToolExecutionResult:
        spec = self.get_tool(name)
        if not spec:
            return ToolExecutionResult(exit_code=2, stdout="", stderr="Tool not found")
        cmd = self._build_command(spec, args)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            stdout = proc.stdout if proc.stdout is not None else ""
            stderr = proc.stderr if proc.stderr is not None else ""
            return ToolExecutionResult(exit_code=proc.returncode, stdout=stdout, stderr=stderr)
        except FileNotFoundError as exc:
            return ToolExecutionResult(exit_code=127, stdout="", stderr=str(exc))
        except Exception as exc:  # pragma: no cover - defensive fallback
            return ToolExecutionResult(exit_code=1, stdout="", stderr=str(exc))
