# 🧠 Mentat CLI – Product Requirements Document (PRD)

## 1. Overview
**Mentat CLI** is a terminal-based AI development assistant designed to provide a conversational interface for software development tasks — code generation, refactoring, analysis, and project automation — entirely from the command line. It brings the intelligence of LLM-based assistants directly into the developer workflow while maintaining strong principles of openness, modularity, and safety.

---

## 2. Goals and Principles
- **Open by Design:** Mentat is modular and open source, allowing users to self-host and extend it.
- **Abstraction over Implementation:** Subsystems (storage, version control, LLM providers, etc.) are abstracted behind interfaces to enable pluggable implementations.
- **Shell-Native:** Operates as a CLI first; no dependency on proprietary IDEs.
- **Secure by Default:** Commands and edits are always verified before execution.
- **Context-Aware:** Understands project structure and session context to reason about codebases holistically.
- **Composable & Extensible:** Integrates external tools and workflows via a standard protocol.
- **Human-Centric Control:** Users maintain complete control over when and how Mentat acts.

---

## 3. Core Functional Areas

### 3.1 Session Context & Storage
- Maintains a context of prior interactions within a project session.
- Context is persisted locally, with a **swappable storage backend**:
  - Default: file-based storage  
  - Alternatives: SQLite, Postgres, ChromaDB, or S3-compatible object storage
- A storage interface abstraction allows developers to plug in their own engine.

### 3.2 Version Control Awareness
- Aware of `.git` directories, branches, and commit state.
- Version control integration is **not hard-coded to Git** — Mentat provides an abstract `VCS` interface.
- Default implementation detects and uses Git; users can implement alternatives.

### 3.3 Command Execution & Safety
- Can execute shell commands and modify files.
- **Regex/Glob-Based Validation:** All commands validated through regex/glob pattern matching.
- **Approval Persistence:** Users can approve a command **once**, for the **current session**, or **permanently**.
- **Safety Modes:**
  - `auto`: executes pre-approved or matching commands automatically
  - `confirm`: prompts for approval before executing any command (default)
  - `readonly`: disables all destructive actions
- This formalizes prior discussions (VS Code-style command matching) and mirrors safety controls seen in Codex/Claude.

### 3.4 Interactive and Non-Interactive Modes
#### Interactive Mode (TUI)
- `mentat chat` launches a **terminal UI (TUI)** for multi-turn interaction.
- Displays conversation history, context summary, and code diffs.
- Users can accept, reject, or edit suggestions inline.
- Session persists until manually closed.

#### Non-Interactive (Script) Mode
- `mentat run "..."` executes a **single prompt non-interactively**.
- Outputs structured results (JSON, text, or markdown).
- Flags for automation:
  - `--output`: write results to file
  - `--format`: choose output format (`json`, `md`, `text`)
  - `--quiet`: suppress extra logs for CI/CD integration

### 3.5 Extensibility via Mentat Tool Server Protocol (MTSP)
- Introduces a standard for external integrations (conceptually similar to MCP).
- Tools (linters, test runners, API scanners, etc.) are registered in `.mentat/tools.json`.

  **Example:**
  ```
  {
    "tools": [
      { "name": "snyk", "command": "snyk test", "description": "Security scan" },
      { "name": "pytest", "command": "pytest --maxfail=1", "description": "Run tests" }
    ]
  }
  ```

- Mentat can discover, invoke, and interpret tool output.
- Enables community-driven extensions and automation beyond built-in capabilities.

### 3.6 Model and Provider Abstraction
- LLM interface is abstracted to support multiple providers.
- Default provider: OpenAI-compatible API.
- Optional providers: Anthropic (Claude), Google (Gemini), local models (Ollama, LM Studio).
- Provider selection configurable via `.mentat/config.json`.

### 3.7 Multimodal Input (Deferred Feature)
- Architecture reserves an interface for multimodal input (images, diagrams, screenshots).
- **Deferred for v1.0**, but a placeholder API will exist.
- Intended use case: screenshots of UI bugs/design issues to guide code fixes during future iterations.

### 3.8 Project Manifest (`AGENT.md`)
- Mentat supports the emerging **`AGENT.md` industry standard** for defining project-specific behavior, style, and goals.
- When present in a repository, this file is automatically parsed and injected into Mentat’s contextual understanding at session start.

**Example:**
```
# AGENT.md
name: Mentat CLI
description: AI-assisted development environment
languages: [python, go]
style: "functional + typed"
rules:
  - Document all public methods
  - Prefer dependency injection
context:
  - Use SQLite by default
  - Avoid global state
```
- Parsed at initialization if present in project root.
- Overrides or augments `.mentat/config.json`.
- Supports YAML or Markdown front-matter syntax.

### 3.9 Prompt Templates (`prompt.md` / Slash Commands)
- Mentat supports reusable **Prompt Templates** defined as Markdown files under `.mentat/prompts/`.
- Each template may be invoked using `/command` syntax in interactive mode (e.g., `/review`, `/test`).

**Example structure:**
```
.mentat/
└── prompts/
    ├── review.prompt.md
    ├── test.prompt.md
    └── doc.prompt.md
```
- Compatible with VS Code Copilot’s `prompt.md` approach.
- Templates can include placeholders (`{{file}}`, `{{branch}}`) replaced at runtime.
- Templates are discoverable via `mentat commands list`.

---

## 4. System Architecture

### 4.1 Modular Layers
1. **Command Layer** — CLI entrypoints (`mentat chat`, `mentat run`, `mentat tool list`)
2. **Core Engine** — Message parsing, prompt assembly, session context
3. **Storage Interface** — Abstract persistence (local, DB, or remote)
4. **VCS Interface** — Abstracted version control integration
5. **Safety Layer** — Regex matching, approvals, policy enforcement
6. **Model Provider Interface** — Connections to LLM APIs
7. **Tool Server Layer (MTSP)** — Invokes external commands via a standard protocol

### 4.2 Configuration Hierarchy
- **Global config:** `~/.mentat/config.json`
- **Project config:** `.mentat/config.json`
- **Runtime overrides:** environment variables and CLI flags

### 4.3 Agent Workflow Model (Reason–Act–Verify Loop)
- Mentat executes all major actions through a **structured reasoning cycle**:
  1. **Reason** — Interpret user intent, gather relevant context (files, history, AGENT.md).
  2. **Act** — Perform generation, file edits, or tool invocations.
  3. **Verify** — Evaluate results, summarize actions, and request user approval when needed.
- This ensures transparency, reproducibility, and safe iterative improvement of generated code.

---

## 5. User Stories
*(User stories remain unchanged — see separate Mentat CLI User Stories document.)*

---

## 6. Roadmap Summary
| Milestone | Focus | Notes |
|---|---|---|
| **v1.0 (Core CLI)** | Context management, safety system, storage & VCS abstraction | Foundational release |
| **v1.1 (Interactivity)** | TUI mode, persistent sessions, approvals UI, Reason–Act–Verify loop | Adds conversational workflows |
| **v1.2 (Contextual Enhancements)** | `AGENT.md` manifest & Prompt Templates | Adds contextual guidance + reusable prompts |
| **v1.3 (Extensibility)** | Developer SDK, Commit/PR automation | Expands MTSP and introduces Git integration |
| **v1.4 (Multimodal Input)** | Add image/screenshot input API | Deferred until post-v1.3 |

---

## 7. Competitive Positioning
Mentat CLI draws from the strengths of industry peers:
- **Codex CLI:** safety modes and agent manifests  
- **Claude Code:** slash commands and tool integration  
- **Gemini CLI:** open-source ReAct agent architecture  
- **Copilot:** IDE-level refinement and multi-file awareness  
- **OpenCode:** TUI-first, provider-agnostic design  

Mentat’s differentiation: a **fully open, extensible, self-hostable CLI platform** that emphasizes developer autonomy and safety.

---

## 8. Success Metrics
- CLI adoption (downloads, active sessions)
- Number of third-party tools integrated via MTSP
- Command approval opt-in rate (indicator of trust)
- Session persistence duration (interactive usage)
- User satisfaction (survey/NPS)

---

## 9. Future Considerations
- Multimodal inputs (images, diagrams)
- Real-time collaboration (multi-user sessions)
- Web-based dashboard for context visualization
- Model fine-tuning and local inference engine support

---

**Document Version:** vNext (Merged October 2025)  
**Authoring Context:** Updated with AGENT.md, Prompt Templates, and Reason–Act–Verify model inclusion.

