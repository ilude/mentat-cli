# Implementation Plan: Mentat CLI - AI Development Assistant

**Branch**: `001-build-the-mentat` | **Date**: 2025-10-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-the-mentat/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build Mentat CLI as a terminal-based AI development assistant with modular architecture supporting interactive/non-interactive modes, configurable safety, and extensible tool integration. Extends existing CQRS/IoC foundation with new abstraction layers for storage, VCS, providers, safety, and TUI components.

## Technical Context

**Language/Version**: Python 3.12+ with uv package management
**Primary Dependencies**: Typer (CLI), Pydantic (config), Rich (terminal output), Textual (TUI), httpx (HTTP clients), subprocess (command execution)
**Storage**: Pluggable backends - filesystem default, SQLite/PostgreSQL/S3 extensions via abstract interface
**Testing**: pytest with MyPy type checking, Ruff linting, integration tests for interface implementations
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux) with PowerShell and bash support
**Project Type**: Single CLI application with modular library architecture
**Performance Goals**: <3s startup, <2s provider switching, 50+ conversation turns without degradation
**Constraints**: Terminal-only interface, no GUI dependencies, offline-capable storage layer
**Scale/Scope**: Individual developer workflows, projects up to 10k files, session context <100MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**✅ I. Open by Design**: All components use abstract interfaces (Storage, VCS, Provider, Safety, Tool protocols). No vendor lock-in or proprietary dependencies.

**✅ II. Abstraction over Implementation**: Storage backends, VCS systems, AI providers, and safety mechanisms are pluggable via interfaces. Default implementations provided for each.

**✅ III. Shell-Native (NON-NEGOTIABLE)**: Pure CLI application using Typer framework. TUI mode uses terminal-based Textual framework. No GUI or IDE dependencies.

**✅ IV. Secure by Default**: Safety layer validates all commands against configurable patterns. Approval mechanisms (once/session/persistent) implemented. Three safety modes supported.

**✅ V. Context-Aware**: Session persistence via storage abstraction. VCS integration for project state awareness. Conversation history maintained across sessions.

**✅ VI. Composable & Extensible**: MTSP protocol for external tool integration. Tool registration via .mentat/tools.json. Community extensions possible without core modifications.

**✅ VII. Human-Centric Control**: Granular approval system for all automated actions. User intent takes precedence over automation. All actions transparent and reversible.

**Architecture Compliance**: Python 3.12+ with uv, CQRS pattern, IoC container, modular interfaces all maintained per constitution requirements.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/mentat/
├── __init__.py
├── cli.py                    # Main CLI entrypoint (existing)
├── app/                      # CQRS application layer (existing)
│   ├── commands.py           # Command DTOs (existing)
│   ├── queries.py            # Query DTOs (existing)  
│   ├── command_handlers.py   # Command handlers (existing)
│   └── query_handlers.py     # Query handlers (existing)
├── core/                     # Core domain layer (existing)
│   ├── bus.py               # Command/Query buses (existing)
│   └── contracts.py         # Core interfaces (existing)
├── ioc/                     # IoC container (existing)
│   └── container.py         # DI container (existing)
├── config/                  # Configuration layer (existing)
│   ├── models.py            # Pydantic models (existing)
│   └── loader.py            # TOML loader (existing)
├── infrastructure/          # Infrastructure layer (existing + expanded)
│   ├── repositories.py      # Tool repository interfaces (existing)
│   ├── fs_tool_repository.py # Filesystem tool repo (existing)
│   ├── storage/            # NEW: Storage abstraction
│   │   ├── __init__.py
│   │   ├── interfaces.py   # Storage protocols
│   │   ├── filesystem.py   # File-based storage (default)
│   │   ├── sqlite.py       # SQLite storage backend
│   │   └── s3.py          # S3-compatible storage backend
│   └── mtsp/              # NEW: Tool Server Protocol
│       ├── __init__.py
│       ├── protocol.py    # MTSP interfaces
│       └── client.py      # Tool invocation client
├── vcs/                    # NEW: Version Control abstraction
│   ├── __init__.py
│   ├── interfaces.py       # VCS protocols
│   ├── git.py             # Git implementation (default)
│   └── detector.py        # VCS detection logic
├── safety/                 # NEW: Safety and approval layer
│   ├── __init__.py
│   ├── validator.py       # Command validation
│   ├── approvals.py       # Approval management
│   └── patterns.py        # Pattern matching engine
├── providers/              # NEW: AI Provider abstraction
│   ├── __init__.py
│   ├── interfaces.py      # Provider protocols
│   ├── openai.py          # OpenAI provider (default)
│   ├── anthropic.py       # Anthropic/Claude provider
│   ├── gemini.py          # Google Gemini provider
│   └── local.py           # Local model provider (Ollama/LM Studio)
├── tui/                   # NEW: Terminal UI components
│   ├── __init__.py
│   ├── chat.py           # Interactive chat interface
│   ├── widgets.py        # Custom TUI widgets
│   └── screens.py        # Screen layouts
└── session/               # NEW: Session management
    ├── __init__.py
    ├── context.py         # Session context handling
    └── history.py         # Conversation history

tests/
├── unit/                  # Unit tests by module
│   ├── test_safety/
│   ├── test_providers/
│   ├── test_vcs/
│   ├── test_storage/
│   └── test_tui/
├── integration/           # Integration tests for interfaces
│   ├── test_storage_backends.py
│   ├── test_vcs_implementations.py
│   ├── test_provider_switching.py
│   └── test_mtsp_protocol.py
└── acceptance/           # End-to-end acceptance tests
    ├── test_interactive_session.py
    ├── test_noninteractive_run.py
    └── test_safety_workflows.py

config/                   # Configuration templates
├── mentat.toml          # Default config (existing)
└── permissions.json     # Default safety patterns

tools/                   # Tool specifications (existing + expanded)
├── echo.toml           # Example tool (existing)
├── specify-init.toml   # Spec-kit integration (existing)
└── specify-check.toml  # Spec-kit integration (existing)
```

**Structure Decision**: Extending existing CQRS/IoC architecture with new modular layers. Each new module (vcs/, safety/, providers/, tui/, session/) follows existing patterns with interfaces, default implementations, and IoC wiring. Infrastructure layer expanded to support storage backends and MTSP protocol.

## Complexity Tracking

No constitution violations identified. All architectural decisions align with established principles.
