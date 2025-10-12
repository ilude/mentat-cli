# Mentat CLI

Agent-driven CLI to orchestrate tools. Follows SOLID, CQRS, and IoC with a simple, extensible design.

## Features
- Typer-based CLI
- Commands/Queries wired via buses
- Filesystem tool repository reading TOML specs

## Quickstart (using uv)

Prerequisites: Python 3.12+ and uv installed.

```pwsh
# Install dependencies
uv sync

# Run CLI help
uv run mentat --help

# List tools (from default ./tools)
uv run mentat tools

# Run a tool by name with arguments
uv run mentat run echo -- "Hello from Mentat"
```

## Project Layout
- `src/mentat/cli.py` – Typer entrypoint
- `src/mentat/core/` – CQRS contracts and buses
- `src/mentat/ioc/` – Minimal IoC container
- `src/mentat/config/` – Pydantic config model and TOML loader
- `src/mentat/infrastructure/` – ToolRepository protocol and FS impl
- `src/mentat/app/` – Commands/queries DTOs and handlers
- `tests/` – Smoke tests for CLI and buses

## Tools
Define tools as TOML files under `tools/` (or configure `config/mentat.toml`).

Example `tools/echo.toml`:

```toml
name = "echo"
description = "Echo arguments"
command = "python -c \"import sys; print(' '.join(sys.argv[1:]))\""
```

## Config
Default config path: `config/mentat.toml`.

```toml
# config/mentat.toml
# tools_dir can be a relative or absolute path
# tools_dir = "tools"
```

## Testing
```pwsh
uv run pytest -q
```

## License
MIT