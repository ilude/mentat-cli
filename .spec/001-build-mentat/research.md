# Research: Mentat CLI Technical Decisions

**Date**: 2025-10-13  
**Feature**: Mentat CLI - AI Development Assistant  
**Phase**: 0 - Research & Resolution

## Storage Abstraction Layer

**Decision**: Pluggable storage backends using Protocol interfaces with filesystem default

**Rationale**: 
- Constitution requires abstraction over implementation
- Different deployment scenarios need different storage (local dev vs cloud vs enterprise)
- Filesystem provides simple default, SQLite for better querying, S3 for cloud deployment
- Session context can grow large (conversation history, project state) requiring efficient storage

**Alternatives considered**:
- Single filesystem implementation: Too limiting for enterprise use cases
- Database-only approach: Adds complexity for simple local development
- In-memory only: Doesn't satisfy context persistence requirement

**Implementation approach**: Protocol-based interface with factory pattern, configurable via .mentat/config.json

## Version Control Interface

**Decision**: Abstract VCS interface with Git default implementation

**Rationale**:
- Constitution principle II requires abstraction over implementation
- Different organizations use different VCS (Git, SVN, Mercurial, Perforce)
- Git is overwhelmingly dominant but abstraction enables future extension
- Project context awareness requires understanding of branch state, uncommitted changes

**Alternatives considered**:
- Git-only implementation: Violates abstraction principle, limits adoption
- Multi-VCS detection without abstraction: Creates tight coupling and maintenance burden

**Implementation approach**: Protocol interface with detector pattern, subprocess-based Git implementation

## AI Provider Architecture

**Decision**: Provider abstraction supporting OpenAI, Anthropic, Google, and local models

**Rationale**:
- Avoids vendor lock-in per constitution principle I
- Different providers have different strengths (coding vs reasoning vs privacy)
- Local models important for privacy-sensitive environments
- Runtime provider switching enables optimal model selection per task

**Alternatives considered**:
- OpenAI-only: Vendor lock-in, privacy concerns for some users
- Plugin architecture: Over-engineering for known provider set

**Implementation approach**: Protocol interface with factory pattern, httpx for HTTP providers, subprocess for local model communication

## Safety and Approval System

**Decision**: Regex/glob pattern matching with three-tier approval system

**Rationale**:
- Constitution principle IV requires security by default
- Users need granular control over automation (once/session/persistent)
- Pattern matching provides flexible, user-configurable validation
- Audit logging required for compliance and debugging

**Alternatives considered**:
- Whitelist-only approach: Too restrictive, poor user experience
- ML-based safety detection: Over-complex, unpredictable behavior
- No safety system: Violates constitution security requirement

**Implementation approach**: Configurable pattern engine with approval persistence, structured logging

## Terminal UI Framework

**Decision**: Textual framework for interactive TUI mode

**Rationale**:
- Rich ecosystem with Textual provides terminal-native UI components
- Maintains shell-native principle III while enabling rich interaction
- Better than readline for complex multi-turn conversations
- Cross-platform terminal compatibility

**Alternatives considered**:
- Pure readline: Limited UI capabilities for complex interactions
- Web-based interface: Violates shell-native principle
- Custom TUI framework: Unnecessary complexity, reinventing wheel

**Implementation approach**: Textual screens and widgets, Rich for non-interactive output formatting

## Tool Integration Protocol

**Decision**: MTSP (Mentat Tool Server Protocol) with JSON-based tool registration

**Rationale**:
- Constitution principle VI requires extensibility without core modification  
- Standard protocol enables community tool development
- JSON registration provides simple configuration without code changes
- Subprocess execution maintains security isolation

**Alternatives considered**:
- Plugin API with Python imports: Security risks, complexity
- No tool integration: Limits extensibility and workflow integration

**Implementation approach**: JSON schema for tool specs, subprocess execution with result parsing

## Session Management

**Decision**: Context-aware session management with automatic state restoration

**Rationale**:
- Constitution principle V requires context awareness across sessions
- Conversation history and project state improve AI assistance quality
- Automatic restoration reduces friction in iterative development workflows

**Alternatives considered**:
- Stateless operation: Poor user experience, repeated context setup
- Manual session save/restore: User friction, likely to be forgotten

**Implementation approach**: Session serialization via storage abstraction, automatic checkpoint/restore

## Configuration System

**Decision**: Hierarchical configuration (global/project/runtime) using TOML format

**Rationale**:
- Existing codebase uses TOML with Pydantic, maintain consistency
- Hierarchy allows global defaults with project-specific overrides
- Environment variables enable CI/CD and deployment flexibility

**Alternatives considered**:
- YAML format: More complex parsing, whitespace sensitivity issues
- Single-level configuration: Inflexible for different deployment scenarios

**Implementation approach**: Extend existing Pydantic models, merge hierarchy in config loader

## Testing Strategy

**Decision**: Three-tier testing with unit/integration/acceptance levels

**Rationale**:
- Constitution requires comprehensive testing discipline
- Interface implementations need integration testing for correctness
- Safety mechanisms require both positive and negative test cases
- End-to-end acceptance tests validate user story completion

**Implementation approach**: pytest with fixtures for interface mocking, separate test directories by scope
