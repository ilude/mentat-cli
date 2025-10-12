from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..core import Command


@dataclass(slots=True)
class RunTool(Command):
    name: str
    args: List[str] = field(default_factory=list)
