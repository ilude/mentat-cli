# Tasks: Mentat CLI - AI Development Assistant

**Input**: Design documents from `/specs/001-build-the-mentat/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure extension

- [x] T001 Create new module directory structure for storage, VCS, providers, safety, TUI, session
- [x] T002 [P] Create __init__.py files for all new modules: src/mentat/{storage,vcs,providers,safety,tui,session}/
- [x] T003 [P] Update pyproject.toml dependencies: Rich, Textual, httpx, asyncio support
- [x] T004 [P] Create base configuration templates: config/permissions.json (safety patterns)
- [x] T005 [P] Setup test directory structure: tests/{unit,integration,acceptance}/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create storage abstraction interfaces in src/mentat/infrastructure/storage/interfaces.py
- [x] T007 [P] Create VCS abstraction interfaces in src/mentat/vcs/interfaces.py
- [x] T008 [P] Create provider abstraction interfaces in src/mentat/providers/interfaces.py
- [x] T009 [P] Create safety system interfaces in src/mentat/safety/validator.py
- [x] T010 [P] Create session management interfaces in src/mentat/session/context.py
- [x] T011 Implement filesystem storage backend in src/mentat/infrastructure/storage/filesystem.py
- [x] T012 [P] Implement Git VCS backend in src/mentat/vcs/git.py
- [x] T013 [P] Implement VCS detector in src/mentat/vcs/detector.py
- [x] T014 [P] Implement safety pattern engine in src/mentat/safety/patterns.py
- [x] T015 [P] Implement approval management in src/mentat/safety/approvals.py
- [ ] T016 Update IoC container to register new services in src/mentat/ioc/container.py
- [x] T017 Create core data models: Session, Message, Command, ProjectContext in src/mentat/core/models.py
- [ ] T018 [P] Create CQRS commands for new operations in src/mentat/app/commands.py
- [ ] T019 [P] Create CQRS queries for new operations in src/mentat/app/queries.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Non-Interactive Command Execution (Priority: P1) 🎯 MVP

**Goal**: Enable single AI-assisted development tasks via `mentat run [prompt]` with structured output

**Independent Test**: Run `mentat run "create a Python function to parse JSON"` and receive structured output

### Implementation for User Story 1

- [ ] T020 [P] [US1] Create RunCommand DTO in src/mentat/app/commands.py (add to existing file)
- [ ] T021 [P] [US1] Create RunCommandHandler in src/mentat/app/command_handlers.py (add to existing file)
- [ ] T022 [US1] Implement AI provider selection logic in src/mentat/providers/selector.py
- [ ] T023 [P] [US1] Create OpenAI provider implementation in src/mentat/providers/openai.py
- [ ] T024 [P] [US1] Create output formatter for JSON/text/markdown in src/mentat/infrastructure/formatters.py
- [ ] T025 [US1] Add `mentat run` command to CLI in src/mentat/cli.py (extend existing)
- [ ] T026 [US1] Wire RunCommand through command bus in src/mentat/cli.py
- [ ] T027 [P] [US1] Add basic error handling and exit codes for run command
- [ ] T028 [P] [US1] Create integration test in tests/integration/test_run_command.py

**Checkpoint**: At this point, `mentat run` should work with basic AI provider integration

---

## Phase 4: User Story 3 - Safe Command Execution with Approval (Priority: P1)

**Goal**: Validate all system commands against configurable safety rules with approval workflows

**Independent Test**: Configure safety patterns, attempt various commands, verify approval workflows

### Implementation for User Story 3

- [ ] T029 [P] [US3] Create SafetyValidator implementation in src/mentat/safety/validator.py (complete interface)
- [ ] T030 [P] [US3] Create safety configuration loader in src/mentat/config/safety.py
- [ ] T031 [US3] Implement command validation pipeline in src/mentat/safety/pipeline.py
- [ ] T032 [P] [US3] Create approval UI components for terminal in src/mentat/safety/ui.py
- [ ] T033 [US3] Integrate safety validation with RunCommandHandler (modify T021)
- [ ] T034 [P] [US3] Create safety mode configuration (auto/confirm/readonly) in src/mentat/config/models.py
- [ ] T035 [P] [US3] Add safety logging and audit trail in src/mentat/safety/audit.py
- [ ] T036 [P] [US3] Create unit tests for safety patterns in tests/unit/test_safety/test_patterns.py
- [ ] T037 [P] [US3] Create integration tests for approval flows in tests/integration/test_safety_workflows.py

**Checkpoint**: Safety system blocks dangerous commands and manages approvals properly

---

## Phase 5: User Story 2 - Interactive Development Session (Priority: P2)

**Goal**: Conversational terminal session with context persistence and multi-turn conversations

**Independent Test**: Run `mentat chat`, issue multiple related commands, verify context persistence

### Implementation for User Story 2

- [ ] T038 [P] [US2] Create ChatCommand DTO and handler in src/mentat/app/
- [ ] T039 [P] [US2] Create conversation history management in src/mentat/session/history.py
- [ ] T040 [US2] Implement session persistence using storage backend in src/mentat/session/persistence.py
- [ ] T041 [P] [US2] Create TUI chat interface using Textual in src/mentat/tui/chat.py
- [ ] T042 [P] [US2] Create custom TUI widgets (message display, input) in src/mentat/tui/widgets.py
- [ ] T043 [US2] Add session context management (variables, state) in src/mentat/session/context.py (complete implementation)
- [ ] T044 [P] [US2] Add `mentat chat` command to CLI in src/mentat/cli.py
- [ ] T045 [US2] Implement session restore functionality in src/mentat/session/restore.py
- [ ] T046 [P] [US2] Create interactive command processor (/help, /status, etc.) in src/mentat/tui/commands.py
- [ ] T047 [P] [US2] Add diff preview functionality for code changes in src/mentat/tui/diff.py
- [ ] T048 [P] [US2] Create acceptance tests for multi-turn conversations in tests/acceptance/test_interactive_session.py

**Checkpoint**: Interactive chat sessions work with context persistence and history

---

## Phase 6: User Story 4 - Project Context Awareness (Priority: P2)

**Goal**: Understand project structure, version control state, and maintain awareness across sessions

**Independent Test**: Run Mentat in Git repository, verify branch detection and project structure awareness

### Implementation for User Story 4

- [ ] T049 [P] [US4] Complete VCS detector implementation in src/mentat/vcs/detector.py (extend T013)
- [ ] T050 [P] [US4] Create project scanner for file structure in src/mentat/infrastructure/scanner.py
- [ ] T051 [US4] Implement project context builder in src/mentat/session/project_context.py
- [ ] T052 [P] [US4] Create dependency detector (package.json, requirements.txt) in src/mentat/infrastructure/dependencies.py
- [ ] T053 [US4] Integrate project context with session initialization in src/mentat/session/context.py
- [ ] T054 [P] [US4] Add project context to AI prompts in src/mentat/providers/context_injector.py
- [ ] T055 [P] [US4] Create project context queries in src/mentat/app/queries.py (add to existing)
- [ ] T056 [P] [US4] Add project status display to TUI in src/mentat/tui/status.py
- [ ] T057 [P] [US4] Create integration tests for VCS detection in tests/integration/test_vcs_implementations.py

**Checkpoint**: Mentat understands project structure and VCS state

---

## Phase 7: User Story 5 - External Tool Integration (Priority: P3)

**Goal**: Integrate existing development tools through Mentat Tool Server Protocol (MTSP)

**Independent Test**: Register a tool in .mentat/tools.json and verify Mentat can invoke it

### Implementation for User Story 5

- [ ] T058 [P] [US5] Define MTSP protocol interfaces in src/mentat/infrastructure/mtsp/protocol.py
- [ ] T059 [P] [US5] Create MTSP tool client in src/mentat/infrastructure/mtsp/client.py
- [ ] T060 [US5] Implement tool registry from .mentat/tools.json in src/mentat/infrastructure/mtsp/registry.py
- [ ] T061 [P] [US5] Create tool invocation commands in src/mentat/app/commands.py (add ToolCommand)
- [ ] T062 [P] [US5] Create tool command handlers in src/mentat/app/command_handlers.py
- [ ] T063 [US5] Add `mentat tools` CLI commands to src/mentat/cli.py
- [ ] T064 [P] [US5] Create tool result parsers in src/mentat/infrastructure/mtsp/parsers.py
- [ ] T065 [P] [US5] Integrate tool results with AI context in src/mentat/providers/tool_integration.py
- [ ] T066 [P] [US5] Create unit tests for MTSP protocol in tests/unit/test_mtsp/
- [ ] T067 [P] [US5] Create integration tests for tool registration in tests/integration/test_mtsp_protocol.py

**Checkpoint**: External tools can be registered and invoked through Mentat

---

## Phase 8: User Story 6 - Multi-Provider AI Support (Priority: P3)

**Goal**: Support multiple AI providers (OpenAI, Anthropic, local models) with runtime switching

**Independent Test**: Configure multiple providers, switch between them, verify seamless operation

### Implementation for User Story 6

- [ ] T068 [P] [US6] Create Anthropic provider in src/mentat/providers/anthropic.py
- [ ] T069 [P] [US6] Create Gemini provider in src/mentat/providers/gemini.py
- [ ] T070 [P] [US6] Create local model provider (Ollama) in src/mentat/providers/local.py
- [ ] T071 [US6] Implement provider switching logic in src/mentat/providers/selector.py (extend T022)
- [ ] T072 [P] [US6] Add provider configuration management in src/mentat/config/providers.py
- [ ] T073 [P] [US6] Add --provider CLI option to run and chat commands in src/mentat/cli.py
- [ ] T074 [US6] Implement provider fallback logic in src/mentat/providers/fallback.py
- [ ] T075 [P] [US6] Add provider status to TUI in src/mentat/tui/provider_status.py
- [ ] T076 [P] [US6] Create provider capability detection in src/mentat/providers/capabilities.py
- [ ] T077 [P] [US6] Create integration tests for provider switching in tests/integration/test_provider_switching.py

**Checkpoint**: Multiple AI providers work with seamless switching

---

## Phase 9: Polish & Integration

**Purpose**: Cross-cutting concerns and final quality gates

- [ ] T078 [P] Create comprehensive configuration validation in src/mentat/config/validator.py
- [ ] T079 [P] Add comprehensive error handling and user-friendly messages across all modules
- [ ] T080 [P] Create performance monitoring and metrics in src/mentat/infrastructure/metrics.py
- [ ] T081 [P] Add comprehensive logging configuration in src/mentat/infrastructure/logging.py
- [ ] T082 [P] Create CLI help system and documentation in src/mentat/cli_help.py
- [ ] T083 [P] Add graceful shutdown handling for interactive sessions
- [ ] T084 Create end-to-end acceptance tests in tests/acceptance/test_complete_workflows.py
- [ ] T085 [P] Update documentation and README with usage examples
- [ ] T086 [P] Performance testing and optimization (startup time, context loading)

---

## Dependencies & Execution Strategy

### User Story Completion Order
1. **US1 (Non-Interactive)** → **US3 (Safety)** → **US2 (Interactive)** → **US4 (Context)** → **US5 (Tools)** → **US6 (Providers)**

### MVP Scope (Minimum Viable Product)
- Phase 1-4 (Setup + Foundation + US1 + US3)
- Delivers: `mentat run` with safety validation
- Success criteria: T001-T037 complete

### Parallel Execution Opportunities

**Within Foundation Phase (T006-T019)**:
- Storage, VCS, Provider interfaces can be developed in parallel
- Safety patterns and approval systems are independent
- Data models independent of interface implementations

**Within User Story 1 (T020-T028)**:
- DTOs, handlers, and providers can be developed in parallel
- Output formatters independent of core logic
- Tests can be written in parallel with implementation

**Within User Story 3 (T029-T037)**:
- Validation, configuration, and UI components are independent
- Safety logging separate from core validation
- Tests can be developed in parallel

**Cross-Story Parallelization**:
- After Foundation: US1, US3 can be developed simultaneously (different modules)
- After US1+US3: US2, US4 can be developed simultaneously
- US5, US6 can be developed in parallel (different abstraction layers)

### Quality Gates
- All tests must pass before phase completion
- MyPy type checking clean for each phase
- Ruff linting clean for each phase
- Integration tests validate interface contracts
- Acceptance tests verify user story completion

### Implementation Strategy
1. **Foundation First**: Complete Phase 2 entirely before user stories
2. **MVP Delivery**: Focus on US1+US3 for immediate value
3. **Incremental Growth**: Add user stories in priority order
4. **Parallel Development**: Use [P] markers for concurrent work
5. **Independent Testing**: Each user story testable in isolation

---

## Task Summary

**Total Tasks**: 86
- Setup: 5 tasks
- Foundation: 14 tasks  
- User Story 1 (P1): 9 tasks
- User Story 3 (P1): 9 tasks
- User Story 2 (P2): 11 tasks
- User Story 4 (P2): 9 tasks
- User Story 5 (P3): 10 tasks
- User Story 6 (P3): 10 tasks
- Polish: 9 tasks

**Parallel Opportunities**: 47 tasks marked [P] (55% parallelizable)

**MVP Tasks**: T001-T037 (37 tasks - Foundation + US1 + US3)

**Independent Test Criteria Per Story**: Each user story phase includes specific validation that story works independently of others.
