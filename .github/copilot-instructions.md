# Copilot Instructions — Mentat CLI Project

## Context & Purpose  
This repository is for **Mentat CLI**, an agent-driven CLI tool built in **Python + uv**.  
It should follow the principles:  
- **SOLID** (single responsibility, open/closed, etc.)  
- **CQRS** (separate Commands vs Queries)  
- **Inversion of Control / IoC** (dependency injection)  
- **DRY (don’t repeat yourself)**  
- **Simplicity and flexibility over complexity**  

We use **TOML** for configuration (less whitespace ambiguity).  
We will not integrate with VSCode or any specific editor directly (Copilot is an external assist).  

When asked to scaffold code, create directories and files exactly (with `src/mentat`, `config`, `core`, `ioc`, `app`, `infrastructure`, `tests` etc.). Use `pyproject.toml` targeting uv.  

## File & Directory Rules

When you generate or suggest files:

- Always include `__init__.py` where Python packages are needed.  
- Use relative imports within the `src/mentat` package.  
- Use Pydantic for config models (for TOML) or standard dataclasses where appropriate.  
- Use a minimal IoC container pattern (factory or singleton registry).  
- For `core`, define `Command`, `Query`, `CommandBus`, `QueryBus`, `Result` types.  
- In `app/commands.py` and `app/queries.py`, define command and query DTOs (dataclasses).  
- In `app/command_handlers.py` and `app/query_handlers.py`, define handler functions that will be wired via IoC and the buses.  
- In `infrastructure/`, produce interface (protocol) definitions (e.g. `ToolRepository`) and one file-system (fs) implementation backed by TOML tool spec files.  
- In CLI entrypoint (e.g. `cli.py`), use `typer` (or similar minimal CLI framework) to wire commands to dispatch through the command/query buses.  
- Write smoke tests: test that CLI helps, test that Bus dispatch/ask works.  

## Style & Conventions

- Use **snake_case** for functions and variables, **PascalCase** for classes.  
- Use type annotations everywhere.  
- Prefer `pathlib.Path` over raw strings for filesystem paths.  
- Keep functions small (max 20–30 lines-ish) and single-purpose.  
- Avoid duplicating logic: refactor common behavior into shared utility or base modules.  
- Avoid overly clever meta-programming; favor clarity.  
- For TOML loading, use `tomllib` (Python 3.11+).  
- Use `subprocess` + `shlex.split` when executing external commands.  
- CLI exit codes: use `typer.Exit` or `sys.exit` consistently.  
- In tests, use `pytest`, `typer.testing.CliRunner`, and minimal fixtures.  

## Prompt Behavior Guidance

- When user says “scaffold project,” produce **exact file manifest** + **full content** for each file.  
- If asked to “add a new command/tool integration,” generate new command/query DTO, handler code, update IoC wiring in `cli.py` or a bootstrap module.  
- When code is requested, wrap it within appropriate module and indicate the folder path (so Copilot generates under correct path).  
- If asked to refactor, maintain SOLID, IoC, and DRY principles; show diff or full updated file.  
- Always assume this Copilot prompt is part of the project’s core instructions and is always in scope.

## Example Minimal Prompt You Might Give Copilot (after this instruction)

> “Scaffold the entire Mentat CLI project structure (directories + files) including pyproject.toml, minimal IoC container, command/query buses, config loader, file-system tool repository, CLI entrypoint with `tools` and `run` commands, test files.”

---

You can save these instructions in `.github/copilot-instructions.md` (repository-wide instructions) or in `.github/instructions/mentat.instructions.md`. Copilot will automatically apply them to code generation in this project. :contentReference[oaicite:0]{index=0}  
