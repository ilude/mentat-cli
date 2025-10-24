from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core import Query


@dataclass(slots=True)
class ToolInfo:
    name: str
    description: str
    command: str


@dataclass(slots=True)
class ListTools(Query[List[ToolInfo]]):
    pass
