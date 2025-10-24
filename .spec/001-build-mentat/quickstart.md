# Quickstart Guide: Mentat CLI Development

**Date**: 2025-10-13  
**Feature**: Mentat CLI - AI Development Assistant  
**Phase**: 1 - Design & Contracts

## Development Environment Setup

### Prerequisites
- Python 3.12+
- uv package manager
- Git (for VCS integration testing)
- VS Code with GitHub Copilot (recommended)

### Initial Setup

1. **Clone and prepare environment**:
```bash
git checkout 001-build-the-mentat
uv sync --group dev
```

2. **Verify existing foundation**:
```bash
make lint  # Should pass - Ruff and MyPy clean
make test  # Should pass - existing tests green
```

3. **Run current CLI**:
```bash
uv run mentat tools  # Lists existing tools (echo, specify-*)
```

## Implementation Order

### Phase 1: Core Interfaces (Week 1)

#### 1.1: Storage Abstraction
```bash
# Create storage module structure
mkdir -p src/mentat/infrastructure/storage
touch src/mentat/infrastructure/storage/{__init__.py,interfaces.py,filesystem.py}
```

**Key files to implement**:
- `src/mentat/infrastructure/storage/interfaces.py` - `StorageBackend` Protocol
- `src/mentat/infrastructure/storage/filesystem.py` - Default filesystem implementation
- `tests/unit/test_storage/test_interfaces.py` - Protocol compliance tests

**Acceptance criteria**: Storage backend can persist and retrieve session data.

#### 1.2: VCS Abstraction  
```bash
mkdir -p src/mentat/vcs
touch src/mentat/vcs/{__init__.py,interfaces.py,git.py,detector.py}
```

**Key files to implement**:
- `src/mentat/vcs/interfaces.py` - `VCSBackend` Protocol
- `src/mentat/vcs/git.py` - Git implementation via subprocess
- `src/mentat/vcs/detector.py` - Auto-detection logic

**Acceptance criteria**: VCS backend detects Git repos and reports branch/status.

#### 1.3: Safety Layer
```bash  
mkdir -p src/mentat/safety
touch src/mentat/safety/{__init__.py,validator.py,approvals.py,patterns.py}
```

**Key files to implement**:
- `src/mentat/safety/validator.py` - `SafetyValidator` Protocol implementation
- `src/mentat/safety/patterns.py` - Regex/glob pattern matching engine
- `src/mentat/safety/approvals.py` - Approval persistence and management

**Acceptance criteria**: Safety system blocks dangerous commands, allows approved patterns.

### Phase 2: Provider Integration (Week 2)

#### 2.1: Provider Abstraction
```bash
mkdir -p src/mentat/providers  
touch src/mentat/providers/{__init__.py,interfaces.py,openai.py,anthropic.py}
```

**Key files to implement**:
- `src/mentat/providers/interfaces.py` - `AIProvider` Protocol
- `src/mentat/providers/openai.py` - OpenAI API client
- `src/mentat/providers/anthropic.py` - Anthropic API client

**Acceptance criteria**: Provider abstraction enables runtime switching between AI services.

### Phase 3: Session Management (Week 3)

#### 3.1: Session Layer
```bash
mkdir -p src/mentat/session
touch src/mentat/session/{__init__.py,context.py,history.py}
```

**Key files to implement**:
- `src/mentat/session/context.py` - Session lifecycle management
- `src/mentat/session/history.py` - Conversation history handling

**Acceptance criteria**: Sessions persist across restarts with full conversation context.

### Phase 4: CLI Commands (Week 4)

#### 4.1: Core Commands
Extend existing `src/mentat/cli.py` with new commands:

```python
# Add to existing CLI
@app.command()
def run(prompt: str, format: str = "text", provider: str = None):
    """Execute single AI task non-interactively."""
    
@app.command() 
def chat(provider: str = None, restore: bool = False):
    """Start interactive session."""

@app.command()
def config(action: str, key: str = None, value: str = None):
    """Manage configuration."""
```

#### 4.2: TUI Mode
```bash
mkdir -p src/mentat/tui
touch src/mentat/tui/{__init__.py,chat.py,widgets.py,screens.py}
```

**Key files to implement**:
- `src/mentat/tui/chat.py` - Main interactive chat interface using Textual
- `src/mentat/tui/widgets.py` - Custom TUI components

**Acceptance criteria**: Interactive chat mode provides rich terminal UI for conversation.

### Phase 5: Tool Integration (Week 5)

#### 5.1: MTSP Implementation
```bash
mkdir -p src/mentat/infrastructure/mtsp
touch src/mentat/infrastructure/mtsp/{__init__.py,protocol.py,client.py}
```

**Key files to implement**:
- `src/mentat/infrastructure/mtsp/protocol.py` - Tool protocol definitions
- `src/mentat/infrastructure/mtsp/client.py` - Tool execution client

**Acceptance criteria**: External tools can be registered and invoked via JSON specs.

## Testing Strategy

### Unit Tests (Per Module)
```bash
# Test each interface implementation
pytest tests/unit/test_storage/
pytest tests/unit/test_vcs/  
pytest tests/unit/test_safety/
pytest tests/unit/test_providers/
```

### Integration Tests (Cross-Module)
```bash
# Test interface interactions
pytest tests/integration/test_storage_backends.py
pytest tests/integration/test_provider_switching.py  
```

### Acceptance Tests (End-to-End)
```bash
# Test user stories
pytest tests/acceptance/test_noninteractive_run.py
pytest tests/acceptance/test_interactive_session.py
pytest tests/acceptance/test_safety_workflows.py
```

## Configuration Examples

### Minimal Development Config
```json
{
  "provider": {
    "default": "openai",
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4"
    }
  },
  "safety": {
    "mode": "confirm"
  },
  "storage": {
    "backend": "filesystem"
  }
}
```

### Development Tool Registration
```json
{
  "tools": [
    {
      "name": "test",
      "description": "Run project tests", 
      "command": "make test",
      "result_parser": "text",
      "timeout": 60
    },
    {
      "name": "lint",
      "description": "Run code quality checks",
      "command": "make lint", 
      "result_parser": "text",
      "timeout": 30
    }
  ]
}
```

## IoC Container Wiring

### Extend Existing Container
```python
# In src/mentat/ioc/container.py
def bootstrap() -> None:
    # Existing wiring...
    
    # Add new interface registrations
    container.register(StorageBackend, FilesystemStorage)
    container.register(VCSBackend, GitBackend) 
    container.register(SafetyValidator, PatternValidator)
    container.register(AIProvider, OpenAIProvider)
    container.register(SessionManager, DefaultSessionManager)
```

## Quality Gates

### Pre-Commit Checklist
```bash
make lint     # Ruff + MyPy pass
make test     # All tests pass
```

### Definition of Done (Per Phase)
- [ ] All unit tests pass with >90% coverage
- [ ] Integration tests demonstrate interface compatibility  
- [ ] Acceptance tests validate user story completion
- [ ] Code follows existing CQRS/IoC patterns
- [ ] MyPy type checking passes without ignores
- [ ] Ruff linting passes without warnings
- [ ] Documentation updated for public APIs

### Performance Benchmarks
- Session startup: <3 seconds
- Provider switching: <2 seconds  
- Command validation: <100ms
- Message persistence: <50ms
- Project context scan: <5 seconds (10k files)

## Troubleshooting

### Common Development Issues

**Import errors**: Ensure `__init__.py` files exist in all new modules
**Test failures**: Run `uv run pytest -v` for detailed output
**Type errors**: Use `uv run mypy src/mentat` to see specific issues
**Configuration errors**: Validate JSON with `uv run mentat config validate`

### Debug Mode
```bash
export MENTAT_LOG_LEVEL=DEBUG
uv run mentat run "test prompt"  # Shows detailed execution logs
```
