from __future__ import annotations

import shlex
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Protocol


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    command: str


class ToolRepository(Protocol):
    def list_tools(self) -> Iterable[ToolSpec]:
        ...

    def get_tool(self, name: str) -> ToolSpec | None:
        ...

    def run_tool(self, name: str, args: List[str]) -> int:
        ...


def _load_tool_toml(path: Path) -> ToolSpec | None:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        name = data.get("name")
        desc = data.get("description", "")
        cmd = data.get("command")
        if not name or not cmd:
            return None
        return ToolSpec(name=name, description=desc, command=cmd)
    except Exception:
        return None
