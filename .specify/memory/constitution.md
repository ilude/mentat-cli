<!--
Sync Impact Report:
- Version change: [new constitution] → 1.0.0
- New principles: Added 7 core principles from PRD
- Added sections: Architecture Requirements, Development Workflow
- Templates requiring updates: ✅ updated plan-template.md references
- Follow-up TODOs: None
-->

# Mentat CLI Constitution

## Core Principles

### I. Open by Design
Mentat MUST be modular and open source, allowing users to self-host and extend it. All components MUST support pluggable implementations through abstract interfaces. No vendor lock-in or proprietary dependencies SHALL be introduced that prevent self-hosting or community extension.

### II. Abstraction over Implementation  
Subsystems (storage, version control, LLM providers, etc.) MUST be abstracted behind interfaces to enable multiple implementations. Default implementations SHALL be provided, but users MUST be able to substitute their own. Interface definitions take precedence over specific technology choices.

### III. Shell-Native (NON-NEGOTIABLE)
Mentat MUST operate as a CLI first with no dependency on proprietary IDEs. All functionality MUST be accessible via command line. Integration with editors is acceptable but MUST NOT be required for core functionality. Terminal-based interfaces take priority over graphical ones.

### IV. Secure by Default
Commands and edits MUST always be verified before execution. All operations MUST pass through configurable safety validation using regex/glob patterns. User approval MUST be required for destructive actions unless explicitly pre-approved. Safety modes (auto/confirm/readonly) MUST be honored.

### V. Context-Aware
Mentat MUST understand project structure and maintain session context. Version control state, file relationships, and conversation history MUST inform all operations. Context persistence across sessions is REQUIRED to enable iterative development workflows.

### VI. Composable & Extensible  
External tools MUST integrate via the Mentat Tool Server Protocol (MTSP). Tool registration through .mentat/tools.json MUST be supported. Community extensions and workflow automation MUST be possible without modifying core Mentat code.

### VII. Human-Centric Control
Users MUST maintain complete control over when and how Mentat acts. All automated actions MUST be transparent and reversible. Approval mechanisms MUST be granular (once/session/persistent). User intent takes precedence over automated suggestions.

## Architecture Requirements

**Technology Stack**: Python 3.12+ with uv package management, following SOLID principles with CQRS pattern for commands/queries and IoC container for dependency injection.

**Required Interfaces**: Storage abstraction, VCS abstraction, Provider abstraction, Safety layer, Tool protocol layer. Each MUST support multiple implementations and runtime switching.

**Configuration Hierarchy**: Global config (~/.mentat/config.json), project config (.mentat/config.json), runtime overrides via environment variables and CLI flags.

## Development Workflow  

**Testing Discipline**: All new functionality MUST have corresponding tests. Integration tests REQUIRED for interface implementations. Safety mechanisms MUST be tested with both positive and negative cases.

**Code Quality**: MyPy type checking and Ruff linting MUST pass before commits. Pre-commit quality gates (make lint && make test) MUST be run and pass.

**Documentation**: All public APIs MUST be documented. Interface contracts MUST include usage examples. Configuration options MUST have clear descriptions and defaults.

## Governance

This constitution supersedes all other development practices and technical decisions. All pull requests MUST verify compliance with these principles. Any violation MUST be explicitly justified and approved. Amendments require documentation of impact, approval from maintainers, and migration plan for existing code.

Complexity beyond these principles MUST be justified against user value and maintenance burden. When in doubt, choose the simpler solution that preserves user control and extensibility.

**Version**: 1.0.0 | **Ratified**: 2025-10-13 | **Last Amended**: 2025-10-13