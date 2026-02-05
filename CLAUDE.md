# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mentat CLI is an agent-driven CLI tool orchestrator built in Python. It uses clean architecture with CQRS patterns, dependency inversion, and a ports-and-adapters approach.

## Build & Development Commands

```bash
# Install dependencies
uv sync --group dev

# Run all quality checks (tests + typecheck + format) - use before commits
make check

# Individual commands
make test          # Run tests (quiet mode)
make test-cov      # Tests with coverage report
make typecheck     # Run mypy
make format        # Format with ruff + organize imports
make lint          # typecheck + format
make clean         # Remove cache files

# Run targeted tests during development (faster iteration)
pytest tests/unit/test_providers/ -v
pytest -k "test_name" -v
pytest tests/ -v --tb=short
```

## Architecture

### Layers

1. **Mentat Engine** (`src/mentat/core/`) - CQRS contracts and buses
   - `contracts.py`: Command, Query, Result base types
   - `bus.py`: CommandBus (dispatch) and QueryBus (ask)

2. **App Layer** (`src/mentat/app/`) - Use cases
   - `commands.py` / `queries.py`: DTOs
   - `command_handlers.py` / `query_handlers.py`: Handlers

3. **Infrastructure** (`src/mentat/infrastructure/`) - Adapters
   - `repositories.py`: ToolRepository protocol
   - `fs_tool_repository.py`: Filesystem implementation

4. **IoC Container** (`src/mentat/ioc/container.py`) - Minimal DI
   - `register_singleton()`, `register_factory()`, `resolve()`

5. **Providers** (`src/mentat/providers/`) - AI provider SDKs
   - `anthropic_provider.py`, `openai.py`, `selector.py`

6. **TUI** (`src/mentat/tui/`) - Textual-based interactive REPL

### Data Flow

- `mentat tools` → QueryBus → ToolRepository → list tools
- `mentat run <tool>` → CommandBus → execute tool → return result
- `mentat ask` / `mentat prompt` → Provider → AI response

## Key Patterns

- **CQRS**: Commands (writes) vs Queries (reads) through separate buses
- **Dependency Inversion**: Protocol-based interfaces, IoC wiring
- **Result[T]**: Operations return `Result` with ok flag + value/error
- **Async providers**: AI providers use asyncio

## Configuration

- Main config: `config/mentat.toml`
- Tool specs: TOML files in `tools/` directory
- Provider API keys: Environment variables (`MENTAT_ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)

## Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/` (gated by `RUN_CLAUDE_TESTS=true`)
- Coverage target: >80%
- Zero warnings policy

## Code Style

- Type annotations required on all functions
- Line length: 100
- Format: double quotes, Ruff
- Use `pathlib.Path` for filesystem paths
- Use `subprocess` + `shlex.split` for external commands
- Keep functions small (max 20-30 lines)

## CLI Entry Point

`src/mentat/cli.py` - Typer-based, wires IoC container and exposes:
- `mentat tools` - List available tools
- `mentat run <tool> -- <args>` - Execute a tool
- `mentat ask "<question>"` - Query AI provider
- `mentat prompt "<text>"` - Non-interactive prompt
- `mentat debug-provider` - Diagnostic info

## Adding New Features

**New tool**: Create TOML spec in `tools/`

**New use-case**:
1. Define DTO in `app/commands.py` or `app/queries.py`
2. Implement handler in `app/command_handlers.py` or `app/query_handlers.py`
3. Register in `ioc/container.py`
4. Expose via `cli.py`

**Swap infrastructure**: Implement the protocol, register in container
