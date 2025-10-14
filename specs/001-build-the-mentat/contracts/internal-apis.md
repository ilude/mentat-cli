# Internal API Contracts

**Date**: 2025-10-13  
**Feature**: Mentat CLI - AI Development Assistant  
**Phase**: 1 - Design & Contracts

## Storage Interface

### StorageBackend Protocol

```python
from typing import Protocol, Optional, Dict, Any, List
from datetime import datetime

class StorageBackend(Protocol):
    """Abstract interface for session and context storage."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize storage backend with configuration."""
        ...
    
    def store_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Store session data."""
        ...
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID."""
        ...
    
    def list_sessions(self, project_path: str) -> List[str]:
        """List session IDs for a project."""
        ...
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and return success status."""
        ...
    
    def store_message(self, session_id: str, message: Dict[str, Any]) -> str:
        """Store message and return message ID."""
        ...
    
    def load_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Load messages for session with pagination."""
        ...
    
    def cleanup_expired(self, retention_days: int) -> int:
        """Clean up expired data and return count deleted."""
        ...
```

### VCS Interface

```python
from typing import Protocol, Optional, List, Dict, Any
from pathlib import Path

class VCSBackend(Protocol):
    """Abstract interface for version control systems."""
    
    def is_repository(self, path: Path) -> bool:
        """Check if path is a VCS repository."""
        ...
    
    def get_current_branch(self, path: Path) -> Optional[str]:
        """Get current branch name."""
        ...
    
    def get_uncommitted_changes(self, path: Path) -> List[str]:
        """Get list of files with uncommitted changes."""
        ...
    
    def get_repository_status(self, path: Path) -> Dict[str, Any]:
        """Get comprehensive repository status."""
        ...
    
    def get_file_history(self, path: Path, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get commit history for specific file."""
        ...
    
    def get_diff(self, path: Path, file_path: str) -> str:
        """Get diff for uncommitted changes."""
        ...
```

### Provider Interface

```python
from typing import Protocol, List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

@dataclass
class Message:
    role: str  # user, assistant, system
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass  
class ProviderResponse:
    content: str
    metadata: Dict[str, Any]
    usage: Dict[str, int]  # tokens, cost, etc.

class AIProvider(Protocol):
    """Abstract interface for AI providers."""
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize provider with configuration."""
        ...
    
    async def generate_response(self, messages: List[Message], **kwargs) -> ProviderResponse:
        """Generate single response from message history."""
        ...
    
    async def stream_response(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        """Stream response chunks as they're generated."""
        ...
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        ...
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get provider capabilities (streaming, function_calling, etc.)."""
        ...
    
    async def health_check(self) -> bool:
        """Check if provider is available and configured correctly."""
        ...
```

### Safety Interface

```python
from typing import Protocol, List, Dict, Any, Optional
from enum import Enum

class SafetyMode(Enum):
    AUTO = "auto"
    CONFIRM = "confirm" 
    READONLY = "readonly"

class ApprovalScope(Enum):
    ONCE = "once"
    SESSION = "session"
    PERSISTENT = "persistent"

@dataclass
class SafetyResult:
    allowed: bool
    matched_pattern: Optional[str]
    requires_approval: bool
    reason: str

@dataclass
class Approval:
    pattern: str
    scope: ApprovalScope
    granted_at: datetime
    expires_at: Optional[datetime]
    usage_count: int

class SafetyValidator(Protocol):
    """Abstract interface for command safety validation."""
    
    def validate_command(self, command: str, mode: SafetyMode) -> SafetyResult:
        """Validate command against safety patterns."""
        ...
    
    def add_approval(self, pattern: str, scope: ApprovalScope, session_id: Optional[str] = None) -> None:
        """Grant approval for command pattern."""
        ...
    
    def revoke_approval(self, pattern: str, scope: ApprovalScope, session_id: Optional[str] = None) -> bool:
        """Revoke approval for command pattern."""
        ...
    
    def list_approvals(self, session_id: Optional[str] = None) -> List[Approval]:
        """List active approvals."""
        ...
    
    def load_patterns(self, config: Dict[str, Any]) -> None:
        """Load safety patterns from configuration."""
        ...
```

### Tool Protocol Interface

```python
from typing import Protocol, Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ToolSpec:
    name: str
    description: str
    command: str
    result_parser: str  # json, text, xml
    timeout: int
    enabled: bool

@dataclass
class ToolResult:
    exit_code: int
    stdout: str
    stderr: str
    parsed_result: Optional[Dict[str, Any]]
    execution_time: float

class ToolRunner(Protocol):
    """Abstract interface for external tool execution."""
    
    def register_tool(self, spec: ToolSpec) -> bool:
        """Register new tool from specification."""
        ...
    
    def list_tools(self) -> List[ToolSpec]:
        """List all registered tools."""
        ...
    
    def get_tool(self, name: str) -> Optional[ToolSpec]:
        """Get tool specification by name."""
        ...
    
    async def execute_tool(self, name: str, args: List[str]) -> ToolResult:
        """Execute tool with arguments."""
        ...
    
    def unregister_tool(self, name: str) -> bool:
        """Remove tool registration."""
        ...
    
    async def test_tool(self, name: str) -> bool:
        """Test if tool can be executed successfully."""
        ...
```

### Session Management Interface

```python
from typing import Protocol, Optional, Dict, Any, List
from uuid import UUID

class SessionManager(Protocol):
    """Abstract interface for session lifecycle management."""
    
    def create_session(self, project_path: str, config: Dict[str, Any]) -> str:
        """Create new session and return session ID."""
        ...
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load existing session by ID."""
        ...
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session state."""
        ...
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to session and return message ID."""
        ...
    
    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from session."""
        ...
    
    def list_sessions(self, project_path: str) -> List[Dict[str, Any]]:
        """List sessions for project."""
        ...
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and all associated data."""
        ...
    
    def get_project_context(self, project_path: str) -> Dict[str, Any]:
        """Get current project context and state."""
        ...
```

## Error Handling Contracts

### Exception Hierarchy

```python
class MentatError(Exception):
    """Base exception for all Mentat errors."""
    pass

class ConfigurationError(MentatError):
    """Configuration validation or loading errors.""" 
    pass

class ProviderError(MentatError):
    """AI provider connection or response errors."""
    pass

class SafetyError(MentatError):
    """Command safety validation errors."""
    pass

class StorageError(MentatError):
    """Storage backend errors."""
    pass

class VCSError(MentatError):
    """Version control system errors."""
    pass

class ToolError(MentatError):
    """External tool execution errors."""
    pass

class SessionError(MentatError):
    """Session management errors."""
    pass
```

### Error Response Format

```json
{
  "error": {
    "code": "PROVIDER_UNAVAILABLE", 
    "message": "Unable to connect to OpenAI API",
    "details": {
      "provider": "openai",
      "status_code": 503,
      "retry_after": 60
    },
    "suggestions": [
      "Check your API key configuration",
      "Verify network connectivity", 
      "Try a different provider with --provider flag"
    ]
  }
}
```