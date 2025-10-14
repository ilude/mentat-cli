# CLI Interface Contracts

**Date**: 2025-10-13  
**Feature**: Mentat CLI - AI Development Assistant  
**Phase**: 1 - Design & Contracts

## Command Line Interface

### Core Commands

#### `mentat run`
Execute a single AI-assisted development task non-interactively.

```bash
mentat run [OPTIONS] PROMPT

Arguments:
  PROMPT    The development task or question to process

Options:
  --format TEXT       Output format: json|text|markdown [default: text]
  --output PATH       Write output to file instead of stdout  
  --provider TEXT     AI provider to use: openai|anthropic|gemini|local
  --safety TEXT       Safety mode: auto|confirm|readonly [default: confirm]
  --project PATH      Project directory [default: current directory]
  --config PATH       Config file path [default: .mentat/config.json]
  --quiet             Suppress progress and info messages
  --help              Show this message and exit
```

**Exit Codes**:
- 0: Success
- 1: General error
- 2: Safety validation failed
- 3: Provider connection failed
- 4: Configuration error

#### `mentat chat`
Start an interactive conversational session.

```bash
mentat chat [OPTIONS]

Options:
  --provider TEXT     AI provider to use: openai|anthropic|gemini|local
  --safety TEXT       Safety mode: auto|confirm|readonly [default: confirm]
  --project PATH      Project directory [default: current directory] 
  --config PATH       Config file path [default: .mentat/config.json]
  --restore           Restore previous session if available
  --help              Show this message and exit
```

**Interactive Commands** (within chat session):
- `/help` - Show available commands
- `/status` - Show session status and context
- `/safety [mode]` - Change safety mode
- `/provider [name]` - Switch AI provider  
- `/history` - Show conversation history
- `/save` - Save session state
- `/quit` - Exit session

#### `mentat tools`
Manage external tool integrations.

```bash
mentat tools [COMMAND] [OPTIONS]

Commands:
  list              List registered tools
  add PATH          Register tool from specification file
  remove NAME       Unregister tool by name
  run NAME ARGS     Execute tool with arguments
  test NAME         Test tool invocation

Options:
  --project PATH    Project directory [default: current directory]
  --help            Show this message and exit
```

#### `mentat config`
Manage configuration settings.

```bash
mentat config [COMMAND] [OPTIONS]

Commands:
  show              Show current effective configuration
  init              Initialize default configuration files
  validate          Validate configuration files
  set KEY VALUE     Set configuration value
  get KEY           Get configuration value

Options:
  --global          Operate on global config (~/.mentat/config.json)
  --project PATH    Project directory [default: current directory]
  --help            Show this message and exit
```

#### `mentat safety`
Manage safety patterns and approvals.

```bash
mentat safety [COMMAND] [OPTIONS]

Commands:
  patterns          List current safety patterns
  approvals         List active approvals  
  add-pattern TEXT  Add new safety pattern
  approve PATTERN   Grant approval for pattern
  revoke PATTERN    Revoke approval for pattern
  clear             Clear all session approvals

Options:
  --scope TEXT      Approval scope: once|session|persistent [default: session]
  --project PATH    Project directory [default: current directory]
  --help            Show this message and exit
```

### Environment Variables

- `MENTAT_CONFIG_PATH`: Override default config file location
- `MENTAT_LOG_LEVEL`: Logging level (DEBUG|INFO|WARNING|ERROR)
- `MENTAT_PROVIDER`: Default AI provider
- `MENTAT_SAFETY_MODE`: Default safety mode
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google Gemini API key

### Configuration File Format

```json
{
  "provider": {
    "default": "openai",
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4",
      "base_url": "https://api.openai.com/v1"
    },
    "anthropic": {
      "api_key": "${ANTHROPIC_API_KEY}",
      "model": "claude-3-sonnet-20240229"
    }
  },
  "safety": {
    "mode": "confirm",
    "patterns": {
      "allow": ["ls", "cat", "grep"],
      "deny": ["rm -rf", "sudo", "format"]
    }
  },
  "storage": {
    "backend": "filesystem",
    "path": ".mentat/sessions",
    "retention_days": 30
  },
  "tools": {
    "enabled": true,
    "timeout": 30,
    "registry": ".mentat/tools.json"
  }
}
```

### Tool Registration Format

```json
{
  "tools": [
    {
      "name": "pytest",
      "description": "Run Python tests",
      "command": "pytest --maxfail=1 {args}",
      "result_parser": "text",
      "timeout": 60,
      "enabled": true
    },
    {
      "name": "lint",
      "description": "Run code linting",
      "command": "ruff check {args}",
      "result_parser": "json",
      "timeout": 30,
      "enabled": true
    }
  ]
}
```