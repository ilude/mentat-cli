# Data Model: Mentat CLI

**Date**: 2025-10-13  
**Feature**: Mentat CLI - AI Development Assistant  
**Phase**: 1 - Design & Contracts

## Core Entities

### Session
Represents an active conversation context with AI assistant.

**Attributes**:
- `session_id`: Unique identifier (UUID)
- `project_path`: Absolute path to project directory
- `created_at`: Session creation timestamp
- `updated_at`: Last activity timestamp
- `provider`: Currently active AI provider
- `safety_mode`: Active safety mode (auto/confirm/readonly)
- `context_size`: Current context size in tokens/bytes
- `status`: Session status (active/paused/terminated)

**Relationships**:
- Has many `Message` entries (conversation history)
- Has one `ProjectContext` (project state snapshot)
- References one `Configuration` (effective config for session)

**Validation Rules**:
- `session_id` must be valid UUID
- `project_path` must exist and be readable
- `safety_mode` must be one of valid enum values
- `context_size` must be non-negative

### Message
Represents a single message in conversation history.

**Attributes**:
- `message_id`: Unique identifier
- `session_id`: Foreign key to Session
- `timestamp`: Message timestamp
- `role`: Message role (user/assistant/system)
- `content`: Message content text
- `metadata`: Additional data (provider, tokens, etc.)
- `command_requests`: List of commands requested in message
- `approval_status`: Approval status for any commands

**Validation Rules**:
- `role` must be valid enum (user/assistant/system)
- `content` cannot be empty for user/assistant messages
- `command_requests` must be valid JSON array

### Command
Represents a system command to be executed.

**Attributes**:
- `command_id`: Unique identifier
- `session_id`: Associated session
- `message_id`: Message that generated command
- `command_text`: Full command string
- `parsed_args`: Parsed command arguments
- `safety_pattern`: Matching safety pattern (if any)
- `approval_status`: Approval status (pending/approved/denied)
- `approval_scope`: Approval scope (once/session/persistent)
- `executed_at`: Execution timestamp (if executed)
- `exit_code`: Command exit code (if executed)
- `output`: Command output (if executed)

**Validation Rules**:
- `command_text` cannot be empty
- `approval_status` must be valid enum
- `exit_code` must be valid integer if command executed

### ProjectContext
Represents current state of project being worked on.

**Attributes**:
- `project_path`: Project root directory path
- `vcs_type`: Detected VCS system (git/svn/none)
- `current_branch`: Active branch name (if VCS)
- `uncommitted_changes`: Count of uncommitted changes
- `project_files`: List of relevant project files
- `dependencies`: Detected project dependencies
- `last_scanned`: Last scan timestamp
- `file_tree_hash`: Hash of current file tree state

**Relationships**:
- Has many `FileSnapshot` entries
- Referenced by `Session` entities

**Validation Rules**:
- `project_path` must be valid directory path
- `vcs_type` must be supported VCS or none
- File paths in `project_files` must be relative to project root

### Configuration
Represents merged configuration from global/project/runtime sources.

**Attributes**:
- `config_id`: Configuration instance identifier  
- `global_config`: Global config values
- `project_config`: Project-specific overrides
- `runtime_overrides`: Runtime CLI/env overrides
- `effective_config`: Merged final configuration
- `validation_errors`: Any config validation issues

**Validation Rules**:
- All config sections must be valid TOML/JSON
- Required fields must be present in effective config
- Provider configurations must be valid for their type

### Tool
Represents an external tool registered via MTSP.

**Attributes**:
- `tool_name`: Tool identifier (from .mentat/tools.json)
- `description`: Tool description
- `command_template`: Command execution template
- `result_parser`: How to parse tool output
- `enabled`: Whether tool is currently enabled
- `last_used`: Last invocation timestamp
- `usage_count`: Number of times invoked

**Validation Rules**:
- `tool_name` must be unique within project
- `command_template` must be valid shell command
- `result_parser` must be supported format (json/text/xml)

### Approval
Represents user approval for command patterns.

**Attributes**:
- `approval_id`: Unique identifier
- `pattern`: Command pattern (regex/glob)
- `approval_type`: Type of approval (once/session/persistent)
- `granted_at`: When approval was granted
- `expires_at`: When approval expires (if applicable)
- `session_id`: Session where granted (if session-scoped)
- `usage_count`: Number of times pattern has been used
- `last_used`: Last time pattern was matched

**Validation Rules**:
- `pattern` must be valid regex or glob pattern
- `approval_type` must be valid enum value
- Session-scoped approvals must reference valid session

## State Transitions

### Session Lifecycle
1. **Created** → Project detected, initial context loaded
2. **Active** → User interaction, message exchange
3. **Paused** → Temporary suspension, context preserved
4. **Terminated** → Session ended, final state persisted

### Command Execution Flow
1. **Requested** → Command identified in user message
2. **Validating** → Safety pattern matching in progress
3. **Pending** → Awaiting user approval (if required)
4. **Approved** → Approved for execution
5. **Executing** → Command running
6. **Completed** → Execution finished (success/failure)
7. **Denied** → User or system denied execution

### Approval Lifecycle  
1. **Requested** → User asked to approve command pattern
2. **Granted** → User granted approval with specified scope
3. **Active** → Approval available for pattern matching
4. **Expired** → Time-based or usage-based expiration
5. **Revoked** → User manually revoked approval

## Data Relationships

```
Session (1) ←→ (N) Message
Session (1) ←→ (1) ProjectContext  
Session (1) ←→ (N) Command
Session (1) ←→ (N) Approval (session-scoped)
Message (1) ←→ (N) Command
ProjectContext (1) ←→ (N) FileSnapshot
Configuration (1) ←→ (N) Session (via reference)
Tool (N) ←→ (N) Command (via invocation records)
```

## Storage Considerations

- **Session data**: Frequent reads/writes, requires fast lookup by project_path
- **Message history**: Append-heavy, requires efficient pagination
- **Project context**: Cached data, requires invalidation on file changes  
- **Approvals**: Lookup-heavy during command validation, requires pattern indexing
- **Configuration**: Read-heavy during session initialization, requires merge logic

## Privacy and Security

- **Sensitive data**: Message content may contain secrets, require encryption at rest
- **Access control**: Project-scoped isolation, no cross-project data leakage
- **Audit trail**: Command execution logging for security and compliance
- **Data retention**: Configurable retention policies for conversation history