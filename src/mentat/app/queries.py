from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..core import Query


@dataclass(slots=True)
class ToolInfo:
    name: str
    description: str
    command: str


@dataclass(slots=True)
class ListTools(Query[List[ToolInfo]]):
    pass


@dataclass(slots=True)
class GetSessionStatus(Query[dict]):
    """Query current session status and context."""

    session_id: Optional[str] = None


@dataclass(slots=True)
class GetProjectContext(Query[dict]):
    """Query project context and VCS information."""

    project_path: Optional[str] = None


@dataclass(slots=True)
class ListApprovals(Query[List[dict]]):
    """Query list of active safety approvals."""

    session_id: Optional[str] = None
    scope: Optional[str] = None


@dataclass(slots=True)
class GetConversationHistory(Query[List[dict]]):
    """Query conversation history from a session."""

    session_id: str
    limit: int = 50
    offset: int = 0
