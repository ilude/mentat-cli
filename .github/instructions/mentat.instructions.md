# Copilot Instructions — Mentat CLI Project

## Context & Purpose

This repository implements **Mentat CLI**, a command-line system that orchestrates tools, maintains context, and supports agentic behavior through modular design.  
It is guided by two key documents stored in this repository:

- **/docs/PRD.md** – Product Requirements Document describing system purpose, goals, and key features.  
- **/docs/UserStories.md** – Detailed user stories defining behavior, user flows, and implementation expectations.

Copilot should refer to those documents conceptually to understand overall intent and scope when generating or refactoring code, even if not directly quoted.

---

## Technical & Architectural Principles

Follow these principles throughout:

- **Language:** Python ≥ 3.12  
- **Environment:** Managed with `uv`  
- **Config format:** TOML  
- **Core principles:** SOLID, CQRS, IoC, DRY  
- **Style:** Simple, flexible, readable > complex or clever  
- **No editor coupling:** No direct VSCode or IDE integrations; runs in terminal mode.

---

## Project Architecture Rules

**Primary directories:**
```
src/mentat/
├─ cli.py
├─ config/
├─ core/
├─ ioc/
├─ app/
├─ infrastructure/
└─ tests/
tools/
docs/
```

**Each layer’s purpose:**

- **core/** – Framework pieces: CommandBus, QueryBus, contracts, Result type.  
- **ioc/** – Simple inversion of control container (dependency registry).  
- **config/** – TOML loader + schema (Pydantic model).  
- **infrastructure/** – Repository and adapter implementations (default: filesystem).  
- **app/** – Commands, queries, and their handlers (CQRS).  
- **cli.py** – Typer entrypoint wiring buses, container, config, and commands.  
- **tests/** – Pytest suites validating CLI and bus behavior.  

---

## Style & Conventions

- Use **type hints** and **dataclasses** or **Pydantic models**.  
- Prefer `pathlib.Path` for all file I/O.  
- Use `subprocess` + `shlex.split` for external tool execution.  
- Maintain strict separation between read and write paths (CQRS).  
- Keep each file small and single-purpose (SOLID).  
- Use `typer` for CLI commands; avoid click or argparse unless essential.  
- Tests: `pytest` + `typer.testing.CliRunner`.  
- Use TOML for config and tool definitions (`mentat.toml`, `tools/*.toml`).  

---

## Generation Behavior for Copilot

When asked to **scaffold**, **generate**, or **extend** code:

1. Create full file paths and contents in correct locations.  
2. Always include `__init__.py` in new packages.  
3. Ensure new classes or functions are consistent with CQRS / IoC / SOLID design.  
4. Wire new features through the IoC container and buses, never with hard imports.  
5. Maintain DRY: reuse helper modules before duplicating logic.  
6. Comment code clearly when behavior is non-obvious.  
7. When referencing requirements or behavior, consider intent from **PRD.md** and **UserStories.md**.  

---

## Example Prompt Patterns for Copilot

- “Scaffold the Mentat CLI project structure using the architecture defined in this instruction file.”  
- “Add a new `ToolRepository` implementation for sqlite based on the interface in infrastructure/repositories.py.”  
- “Add a `ListSessions` query and handler to retrieve stored sessions from the storage backend.”  
- “Refactor `cli.py` to register new command handlers via IoC.”  
- “Generate tests for the QueryBus and CommandBus following the existing test style.”  

---

## References

- **PRD:** `/docs/PRD.md`  
- **User Stories:** `/docs/UserStories.md`  
- **Mentat CLI Scaffold:** See internal documentation and project structure generated from the scaffold template.  
- **uv documentation:** <https://github.com/astral-sh/uv>  
- **Copilot Customization Reference:** <https://code.visualstudio.com/docs/copilot/customization/overview>  

---

## Kickoff Prompt for Copilot Chat

You can paste this directly into Copilot Chat to start development:

```
You are my development copilot for the Mentat CLI project.

Use the `.github/copilot-instructions.md` file as your guiding specification.
Use the PRD (docs/PRD.md) and User Stories (docs/UserStories.md) to understand the purpose and expected behaviors.

Start by setting up the initial project skeleton:
- Generate the `pyproject.toml` for uv (Python 3.12+)
- Create the directory structure under `src/mentat/` following the architecture described in the instructions
- Include a `cli.py` Typer entrypoint with basic commands: `tools` (list) and `run` (execute tool)
- Add placeholder implementations for CommandBus, QueryBus, IoC container, config loader, and a filesystem ToolRepository
- Add smoke tests using `pytest` and `typer.testing.CliRunner`
- Generate `.gitignore` and README.md
Once done, show me a summary of created files and instructions for running with uv.
```

