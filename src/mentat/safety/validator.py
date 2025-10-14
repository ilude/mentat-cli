"""Safety system interfaces for Mentat CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class SafetyMode(Enum):
    """Safety modes for command execution."""

    AUTO = "auto"  # Execute pre-approved commands automatically
    CONFIRM = "confirm"  # Prompt for confirmation on all commands
    READONLY = "readonly"  # Block all destructive operations


class ApprovalScope(Enum):
    """Scope for command approval persistence."""

    ONCE = "once"  # One-time approval
    SESSION = "session"  # Approval valid for current session
    PERSISTENT = "persistent"  # Approval persists across sessions


class ValidationResult(Enum):
    """Result of command validation."""

    ALLOWED = "allowed"  # Command is explicitly allowed
    DENIED = "denied"  # Command is explicitly denied
    REQUIRES_APPROVAL = "requires_approval"  # Command needs user approval


@dataclass
class SafetyPattern:
    """Safety pattern for command validation."""

    pattern: str
    is_allow: bool  # True for allow patterns, False for deny patterns
    description: str


@dataclass
class CommandValidation:
    """Result of command safety validation."""

    command: str
    result: ValidationResult
    matched_pattern: Optional[SafetyPattern] = None
    risk_level: str = "low"  # low, medium, high, critical
    explanation: str = ""
    reason: str = ""  # Alias for explanation for backward compatibility


@dataclass
class ApprovalRequest:
    """Request for user approval of a command."""

    command: str
    risk_level: str
    explanation: str
    suggested_scope: ApprovalScope = ApprovalScope.ONCE


class SafetyValidator(Protocol):
    """Protocol for safety validation implementations."""

    def validate_command(self, command: str) -> CommandValidation:
        """Validate a command against safety patterns."""
        ...

    def is_command_approved(self, command: str, session_id: Optional[str] = None) -> bool:
        """Check if command has existing approval."""
        ...

    def add_approval(
        self, command: str, scope: ApprovalScope, session_id: Optional[str] = None
    ) -> None:
        """Add approval for a command pattern."""
        ...

    def remove_approval(
        self, command: str, scope: ApprovalScope, session_id: Optional[str] = None
    ) -> None:
        """Remove approval for a command pattern."""
        ...

    def get_safety_mode(self) -> SafetyMode:
        """Get current safety mode."""
        ...

    def set_safety_mode(self, mode: SafetyMode) -> None:
        """Set safety mode."""
        ...

    def load_patterns(self, config_path: str) -> None:
        """Load safety patterns from configuration."""
        ...


class ApprovalManager(Protocol):
    """Protocol for managing command approvals."""

    async def request_approval(self, request: ApprovalRequest) -> bool:
        """Request user approval for a command."""
        ...

    async def store_approval(
        self, command_pattern: str, scope: ApprovalScope, session_id: Optional[str] = None
    ) -> None:
        """Store approval for future use."""
        ...

    async def has_approval(self, command: str, session_id: Optional[str] = None) -> bool:
        """Check if command has stored approval."""
        ...

    async def cleanup_session_approvals(self, session_id: str) -> None:
        """Clean up approvals for a session."""
        ...

    async def list_approvals(self, scope: Optional[ApprovalScope] = None) -> List[Dict[str, Any]]:
        """List current approvals."""
        ...


class BaseSafetyValidator(ABC):
    """Base class for safety validator implementations."""

    def __init__(self, safety_mode: SafetyMode = SafetyMode.CONFIRM):
        """Initialize safety validator."""
        self.safety_mode = safety_mode
        self.patterns: List[SafetyPattern] = []

    @abstractmethod
    def validate_command(self, command: str) -> CommandValidation:
        """Validate a command against safety patterns."""
        pass

    @abstractmethod
    def is_command_approved(self, command: str, session_id: Optional[str] = None) -> bool:
        """Check if command has existing approval."""
        pass

    @abstractmethod
    def add_approval(
        self, command: str, scope: ApprovalScope, session_id: Optional[str] = None
    ) -> None:
        """Add approval for a command pattern."""
        pass

    @abstractmethod
    def remove_approval(
        self, command: str, scope: ApprovalScope, session_id: Optional[str] = None
    ) -> None:
        """Remove approval for a command pattern."""
        pass

    def get_safety_mode(self) -> SafetyMode:
        """Get current safety mode."""
        return self.safety_mode

    def set_safety_mode(self, mode: SafetyMode) -> None:
        """Set safety mode."""
        self.safety_mode = mode

    @abstractmethod
    def load_patterns(self, config_path: str) -> None:
        """Load safety patterns from configuration."""
        pass


class SafetyError(Exception):
    """Base exception for safety-related errors."""

    pass


class CommandDeniedError(SafetyError):
    """Raised when a command is denied by safety validation."""

    pass


class ApprovalRequiredError(SafetyError):
    """Raised when a command requires approval."""

    pass
