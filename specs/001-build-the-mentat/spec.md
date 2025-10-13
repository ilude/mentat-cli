# Feature Specification: Mentat CLI - AI Development Assistant

**Feature Branch**: `001-build-the-mentat`  
**Created**: 2025-10-13  
**Status**: Draft  
**Input**: User description: "Build the Mentat CLI application as defined in docs/PRD.md and docs/UserStories.md with storage abstraction, VCS awareness, command safety, interactive/non-interactive modes, and extensibility via MTSP"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-Interactive Command Execution (Priority: P1)

A developer wants to execute a single AI-assisted development task from their terminal or script without starting an interactive session.

**Why this priority**: Core CLI functionality that provides immediate value and enables automation/scripting integration.

**Independent Test**: Can be fully tested by running `mentat run "create a Python function to parse JSON"` and receiving structured output that delivers immediate development assistance.

**Acceptance Scenarios**:

1. **Given** a project directory, **When** user runs `mentat run "analyze this codebase"`, **Then** system outputs analysis in requested format (JSON/text/markdown)
2. **Given** a command requiring file changes, **When** safety mode is "confirm", **Then** system prompts for approval before executing changes
3. **Given** an unsafe command pattern, **When** command validation fails, **Then** system denies execution and logs the attempt

---

### User Story 2 - Interactive Development Session (Priority: P2)

A developer wants to start a conversational terminal session where they can iteratively discuss, review, and refine development tasks with AI assistance.

**Why this priority**: Enables complex multi-turn development workflows and maintains context across interactions.

**Independent Test**: Can be fully tested by running `mentat chat`, issuing multiple related commands, and verifying context persistence and conversation history.

**Acceptance Scenarios**:

1. **Given** an active chat session, **When** user requests code changes, **Then** system displays diff preview and waits for approval
2. **Given** a multi-turn conversation, **When** user references previous context, **Then** system understands and maintains conversation continuity
3. **Given** session with pending changes, **When** user exits and restarts, **Then** system offers to restore session context

---

### User Story 3 - Safe Command Execution with Approval (Priority: P1)

A developer wants all system commands to be validated against configurable safety rules with granular approval options to prevent accidental damage.

**Why this priority**: Critical safety feature that builds user trust and prevents destructive actions.

**Independent Test**: Can be fully tested by configuring safety patterns, attempting various commands, and verifying approval workflows work correctly.

**Acceptance Scenarios**:

1. **Given** safety mode "confirm", **When** any command is executed, **Then** system prompts for approval unless pre-approved
2. **Given** a dangerous command pattern, **When** user attempts execution, **Then** system blocks and requires explicit approval
3. **Given** user approves a command "for this session", **When** same pattern occurs again, **Then** system auto-approves within session only

---

### User Story 4 - Project Context Awareness (Priority: P2)

A developer wants Mentat to understand their project structure, version control state, and maintain awareness across sessions.

**Why this priority**: Essential for intelligent assistance that considers project-specific context and constraints.

**Independent Test**: Can be fully tested by running Mentat in a Git repository and verifying it detects branches, uncommitted changes, and project structure.

**Acceptance Scenarios**:

1. **Given** a Git repository, **When** Mentat starts, **Then** system detects current branch and uncommitted changes
2. **Given** project files, **When** user asks for changes, **Then** system considers existing code patterns and project structure
3. **Given** previous session context, **When** user restarts Mentat, **Then** system restores relevant conversation history

---

### User Story 5 - External Tool Integration (Priority: P3)

A developer wants to integrate their existing development tools (linters, test runners, security scanners) with Mentat through a standard protocol.

**Why this priority**: Extends Mentat's capabilities and integrates with existing workflows, but not essential for core functionality.

**Independent Test**: Can be fully tested by registering a tool in .mentat/tools.json and verifying Mentat can discover, invoke, and interpret results.

**Acceptance Scenarios**:

1. **Given** tools registered in .mentat/tools.json, **When** user requests tool listing, **Then** system displays available tools with descriptions
2. **Given** a registered linter tool, **When** Mentat suggests using it, **Then** system can invoke tool and interpret results
3. **Given** tool execution results, **When** analysis completes, **Then** system incorporates findings into development suggestions

---

### User Story 6 - Multi-Provider AI Support (Priority: P3)

A developer wants to choose their preferred AI provider (OpenAI, Anthropic, local models) for different use cases or based on privacy/cost preferences.

**Why this priority**: Provides flexibility and prevents vendor lock-in, but core functionality works with any single provider.

**Independent Test**: Can be fully tested by configuring different providers and verifying Mentat can switch between them at runtime.

**Acceptance Scenarios**:

1. **Given** multiple providers configured, **When** user specifies `--provider anthropic`, **Then** system uses Claude for that session
2. **Given** default provider unavailable, **When** system attempts connection, **Then** system falls back to alternative provider if configured
3. **Given** provider-specific capabilities, **When** user requests advanced features, **Then** system selects appropriate provider automatically

---

### Edge Cases

- What happens when .mentat/config.json is corrupted or missing?
- How does system handle network failures during AI provider communication?
- What occurs when user interrupts (Ctrl+C) during command execution?
- How does system behave when Git repository is in merge conflict state?
- What happens when storage backend becomes unavailable during session?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide non-interactive command execution via `mentat run [prompt]` with structured output formats
- **FR-002**: System MUST support interactive terminal sessions via `mentat chat` with conversation history and context persistence
- **FR-003**: System MUST validate all shell commands against configurable regex/glob patterns in .mentat/permissions.json
- **FR-004**: System MUST support three safety modes: auto (pre-approved commands execute automatically), confirm (prompt for all commands), readonly (no destructive actions)
- **FR-005**: System MUST persist session context using pluggable storage backends (file system default, with database and cloud storage extensions)
- **FR-006**: System MUST detect and interact with version control systems through abstract interface with Git default implementation
- **FR-007**: System MUST support multiple AI providers through configurable interface (OpenAI, Anthropic, Gemini, local models)
- **FR-008**: System MUST integrate external tools via Mentat Tool Server Protocol (MTSP) with registration in .mentat/tools.json
- **FR-009**: System MUST maintain project awareness including file structure, dependencies, and version control state
- **FR-010**: System MUST provide granular approval options: once, per-session, or persistent for command patterns
- **FR-011**: System MUST support configuration hierarchy: global (~/.mentat/config.json), project (.mentat/config.json), runtime overrides
- **FR-012**: System MUST log all command executions with timestamps and approval sources for audit purposes

### Key Entities

- **Session**: Represents a conversation context with history, project state, and configuration
- **Command**: Represents a shell or system command with safety validation and approval status  
- **Project**: Represents workspace context including files, VCS state, and tool configurations
- **Provider**: Represents AI service connection with capabilities and configuration
- **Tool**: Represents external development tool with invocation protocol and result parsing
- **Approval**: Represents user consent for command execution with scope and persistence rules
- **Configuration**: Represents settings hierarchy from global to project to runtime levels

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete simple development tasks using `mentat run` in under 30 seconds from command to output
- **SC-002**: Interactive sessions maintain context across 50+ conversation turns without degradation
- **SC-003**: Safety system blocks 100% of commands matching deny patterns while allowing approved patterns
- **SC-004**: System starts and loads project context in under 3 seconds for projects with 10,000+ files
- **SC-005**: Context persistence works reliably across session restarts with 99%+ data integrity
- **SC-006**: Tool integration protocol supports 95% of common development tools without custom code
- **SC-007**: Provider switching completes in under 2 seconds with seamless conversation continuity
- **SC-008**: 90% of users successfully complete their first development task within 5 minutes of installation

## Assumptions

- Users have Python 3.12+ and basic terminal familiarity
- Default Git integration assumes standard Git workflows and commands
- File system storage backend provides adequate performance for typical project sizes (<100MB context)
- Standard internet connection available for AI provider communication (offline mode not required for MVP)
- Common development tools follow standard CLI patterns for MTSP integration
- Users understand basic regex/glob patterns for safety configuration
