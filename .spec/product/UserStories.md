# Mentat CLI – User Stories

## Overview
This document lists and describes the core user stories for **Mentat CLI**, covering functional capabilities, safety mechanisms, and extensibility goals. These stories are designed to guide development toward a secure, modular, and user-friendly command-line assistant.

---

## US-01: Storage Abstraction
> As a developer, I want to persist session context using interchangeable backends (file, DB, S3), so that I can adapt Mentat to my storage preferences.

**Acceptance Criteria:**
- Context data persists between sessions.
- Backend selection is configurable via `.mentat/config.json`.
- Default backend: file-based; alternative implementations supported.

---

## US-02: Version Control Awareness
> As a developer, I want Mentat to recognize and interact with my version control system (Git, etc.) without being hardcoded to it, so I can use Mentat in any repository.

**Acceptance Criteria:**
- Detects `.git` directories automatically.
- Abstracts VCS operations behind a `VCS` interface.
- Supports Git by default; allows extension to other systems.

---

## US-03: Command Execution Safety
> As a developer, I want Mentat to validate all shell commands against a configurable regex/glob pattern list before execution, so that I can ensure safe, predictable operations.

**Acceptance Criteria:**
- All commands are matched against `.mentat/permissions.json`.
- Denied patterns result in prompt for manual approval.
- Logs all executions with timestamp and approval source.

---

## US-04: Extensible VCS and Command Interfaces
> As a developer, I want Mentat's version control and execution layers to be pluggable, so I can use alternative systems or specialized workflows.

**Acceptance Criteria:**
- Abstract interfaces for both VCS and Command Execution layers.
- Developers can extend Mentat using custom implementations.
- Plugin discovery via `.mentat/plugins` directory.

---

## US-05: Interactive Terminal Mode
> As a developer, I want to start an interactive Mentat session (`mentat chat`) where I can iteratively issue commands, review edits, and refine outputs, so I can work conversationally within my terminal.

**Acceptance Criteria:**
- Launching `mentat chat` opens a conversational TUI.
- Maintains session context and message history.
- Inline approval and code diff review supported.
- Allows multi-turn reasoning and command refinement.

---

## US-06: Non-Interactive / Script Mode
> As a developer, I want to execute a single Mentat prompt non-interactively (`mentat run "..."`), so I can integrate Mentat into scripts, CI jobs, or quick terminal commands.

**Acceptance Criteria:**
- Executes one-shot prompts without persistent session.
- Supports output formats: JSON, Markdown, Text.
- Configurable via CLI flags (`--format`, `--output`, `--quiet`).

---

## US-07: Safety and Permission Controls
> As a developer, I want Mentat to verify and ask approval for risky operations before execution, using regex/glob matching and approval persistence, so my environment remains safe.

**Acceptance Criteria:**
- Safety rules defined in `.mentat/permissions.json`.
- Approval options: once, per session, or persistent.
- Three safety modes: `auto`, `confirm`, and `readonly`.
- Default safety mode: `confirm`.

---

## US-08: Extensibility via Mentat Tool Server Protocol (MTSP)
> As a developer, I want to register and use external tools (linters, test runners, security scanners) within Mentat, so that I can extend its capabilities to match my workflow.

**Acceptance Criteria:**
- Tools registered via `.mentat/tools.json`.
- Mentat can list, invoke, and parse tool results.
- Supports tool suggestions in response generation.

**Example Configuration:**
```
{
  "tools": [
    { "name": "snyk", "command": "snyk test", "description": "Security scan" },
    { "name": "pytest", "command": "pytest --maxfail=1", "description": "Run tests" }
  ]
}
```

---

## US-09: Multimodal Inputs (Deferred Feature)
> As a developer, I want Mentat to eventually support visual inputs like screenshots or diagrams, so I can share UI bugs or design issues.

**Acceptance Criteria (Deferred):**
- Placeholder API for image/file attachments.
- Not part of v1.0 scope; deferred to roadmap.

---

## US-10: Session Context Persistence
> As a developer, I want Mentat to remember my prior interactions and context within a project, so that I can maintain continuity across sessions.

**Acceptance Criteria:**
- Session context stored per project directory.
- History accessible and exportable via CLI.
- Context restoration supported when reopening projects.

---

## US-11: Provider Abstraction
> As a developer, I want Mentat to support multiple LLM providers, so I can choose models based on capability, privacy, or cost.

**Acceptance Criteria:**
- Provider configuration in `.mentat/config.json`.
- Default provider: OpenAI.
- Optional providers: Anthropic, Gemini, or local models (Ollama, LM Studio).
- Runtime provider switching via CLI flag (`--provider`).

---

## US-12: Developer Extensibility API
> As a developer, I want a documented extension API, so I can add my own integrations and features to Mentat.

**Acceptance Criteria:**
- Extensibility layer exposed via SDK.
- Plugin registration system documented.
- Example templates provided for external tool integration.

---

**Document Version:** vNext (October 2025)

**Authoring Context:** Extracted and expanded from Mentat CLI PRD vNext.
