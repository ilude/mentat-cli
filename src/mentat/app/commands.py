from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..core import Command


@dataclass(slots=True)
class RunTool(Command):
    name: str
    args: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RunPrompt(Command):
    """Execute a single AI-assisted development task non-interactively."""

    prompt: str
    format: str = "text"  # json, text, markdown
    provider: Optional[str] = None
    safety_mode: Optional[str] = None
    output_file: Optional[str] = None


@dataclass(slots=True)
class StartSession(Command):
    """Start an interactive conversational session."""

    provider: Optional[str] = None
    safety_mode: Optional[str] = None
    restore_session: bool = False


@dataclass(slots=True)
class ValidateCommand(Command):
    """Validate a shell command against safety rules."""

    command_text: str
    safety_mode: str = "confirm"


@dataclass(slots=True)
class ApprovePattern(Command):
    """Approve a command pattern for execution."""

    pattern: str
    scope: str = "session"  # once, session, persistent
