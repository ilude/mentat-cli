from __future__ import annotations

from dataclasses import dataclass

from ..core import Query


@dataclass(slots=True)
class ListTools(Query[list[str]]):
    pass
