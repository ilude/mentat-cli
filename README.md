# Mentat CLI

Agent-driven CLI to orchestrate tools via simple TOML specs. Designed for clarity and extension with clean architecture, clear separation of reads vs writes, and dependency inversion.

## 🌟 Unique Features & Differentiators
- Mentat Engine: a minimal, testable core that’s easy to reason about and extend
- Mentat Tool Catalog: simple tool specs (TOML) discoverable from the filesystem
- MTSP-ready: designed to evolve into the Mentat Tool Server Protocol (roadmap)
- CLI wired through Command/Query buses for predictable flows
- Straightforward configuration using TOML
- Predictable process execution (spawns external commands with safe defaults)
- Scripted quality checks (lint, tests)

## 🧩 Common Capabilities
- Natural-language friendly CLI verbs (tools, run)
- Reads/writes local files required by tools (scoped to tool execution)
- Non-interactive CI-friendly workflow via single commands
- Git-friendly project layout and smoke tests

## � Why we’re building Mentat
Developers need a terminal-native assistant that understands repository context, respects safety boundaries, and remains open and extensible. Mentat aims to bring conversational, context-aware help directly to the command line without forcing an IDE or a single vendor’s stack. We emphasize:
- Open by design and self-hostable
- Abstraction over implementation (storage, VCS, providers)
- Shell-first ergonomics
- Safety and approval before actions
- Extensibility through a simple tool catalog and a protocol roadmap
- Human-centric control at every step

## 🧭 End goals
What success looks like for Mentat:
- Context-aware code generation, refactoring, and navigation from the CLI
- Safe execution via approvals and clear audit trails
- Pluggable storage, VCS, and model providers
- Rich interactive mode (TUI) for multi-turn collaboration (roadmap)
- Project-aware behavior via manifests (AGENT.md) and prompt templates (roadmap)
- A thriving ecosystem of community tools (MTSP) and integrations (roadmap)

## �🏗️ Architecture Overview
Mentat follows ports-and-adapters with a thin CLI surface and Mentat-branded layers.

- Mentat Engine (core contracts and buses)
	- Command, Query, and Result value types
	- CommandBus (dispatch) and QueryBus (ask)
- App (use-cases)
	- Request/response DTOs and handlers for commands/queries
- Tool Catalog (adapter)
	- ToolRepository protocol with a filesystem-backed implementation
	- Executes external processes as child commands
- Config
	- Configuration models and a TOML loader
- IoC
	- Minimal container wires repositories and handlers to the buses
- CLI
	- Exposes `mentat` commands and dispatches to buses

Data flow examples
1) `mentat tools` → QueryBus → list tools via `ToolRepository`
2) `mentat run <tool> -- <args>` → CommandBus → execute tool command → return exit code/stdout/stderr

## 🗂️ Project Layout
- `src/mentat/cli.py` – Typer entrypoint and bus wiring
- `src/mentat/core/` – CQRS contracts (`contracts.py`) and buses (`bus.py`)
- `src/mentat/ioc/` – Minimal IoC container
- `src/mentat/config/` – Pydantic config + TOML loader
- `src/mentat/infrastructure/` – Ports and adapters (filesystem tool repo)
- `src/mentat/app/` – Commands/Queries DTOs and handlers
- `tests/` – Smoke tests for CLI and buses

## 🧰 Mentat Tool Catalog (TOML)
Define tools under `tools/` (or set `tools_dir` in `config/mentat.toml`).

Example `tools/echo.toml`:

```toml
name = "echo"
description = "Echo arguments"
command = "python -c \"import sys; print(' '.join(sys.argv[1:]))\""
```

## 🔧 Configuration
Minimal config (`config/mentat.toml`):

```toml
# tools_dir can be a relative or absolute path
# tools_dir = "tools"
```

## Anthropic (Claude) provider

To use Anthropic (Claude) as a provider, set the API key in the environment or in `config/mentat.toml` under a `providers.anthropic` section.

Environment variable (recommended):

```pwsh
$env:MENTAT_ANTHROPIC_API_KEY = 'sk-...'
```

Optionally set model in `config/mentat.toml`:

```toml
[providers.anthropic]
api_key = ""
model = "claude-2.1"
```

Install the SDK locally if you want to run integration tests or call Anthropic directly:

```pwsh
pip install anthropic
```

Run the integration test (gated):

```pwsh
# $env:MENTAT_ANTHROPIC_API_KEY = 'sk-...'
# $env:RUN_CLAUDE_TESTS = 'true'
C:/Projects/Personal/mentat-cli/.venv/Scripts/python.exe -m pytest tests/integration/test_anthropic_integration.py -q
```

Notes:
- Integration tests are intentionally gated to avoid accidental API usage and costs. Do not set `RUN_CLAUDE_TESTS` in shared CI unless you intend to run the tests.
- The provider factory is registered in the container under the key `provider.anthropic` and will read config from `MentatConfig.providers.anthropic` if present.

Roadmap naming
- Project config: `.mentat/config.*`
- Tool registry: `.mentat/tools.*` (supersedes filesystem-only discovery)
These names align with broader Mentat conventions while remaining backward-compatible.

## 🚀 Quickstart

```pwsh
# Run CLI help
mentat --help

# List tools (from default ./tools)
mentat tools

# Run a tool by name with arguments
mentat run echo -- "Hello from Mentat"
```

## 🛠️ Development
Quality checks:

```pwsh
make check
```

## 🧱 Extending Mentat
Add a tool
1) Create a TOML spec in `tools/`
2) `uv run mentat tools` to verify
3) `uv run mentat run <name> -- <args>` to execute

Add a use-case
1) Define a DTO in `app/commands.py` or `app/queries.py`
2) Implement in `app/command_handlers.py` or `app/query_handlers.py`
3) Register in `ioc/container.py` and expose via `cli.py`

Swap infrastructure
- Implement the `ToolRepository` protocol (e.g., HTTP/DB-backed)
- Register it in the container; no changes to core/app required

## 🧭 Mentat Concepts (Roadmap)
- Safety Modes: `auto`, `confirm` (default), and `readonly` for controlled execution
- AGENT.md: project manifest for behavior/style rules automatically ingested at session start
- Prompt Templates: reusable prompts under `.mentat/prompts/` with `/command` invocation in interactive mode
- Reason–Act–Verify Loop: structured cycle for transparency and safe automation

## 🧭 Comparative Positioning
For how Mentat relates to other CLIs (Copilot, Claude Code, Gemini, etc.), see `docs/ReferenceImplementations.md`.

## 📓 Style Notes
- Small, single-purpose functions; clarity over cleverness
- Keep configuration straightforward (TOML), keep adapters thin

## License
MIT