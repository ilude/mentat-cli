---
applyTo:
  - ".github/instructions/*.instruction.md"
---

# GitHub Copilot Instructions Guidelines

**Reference**: https://code.visualstudio.com/docs/copilot/customization/custom-instructions

## Purpose
Create targeted instruction files for specific file types, tools, or workflows.

## Instruction File Structure

### File Naming
- `<topic>.instruction.md` (e.g., `python-code.instruction.md`, `testing.instruction.md`)

### Required Header
```markdown
---
applyTo:
  - "file/pattern/**/*.ext"
---

# Title

**Reference**: [URL if applicable]

## Purpose
What this covers.
```

### AppliesTo Patterns (Examples)
- `**/*.py` - All Python files
- `tests/**/*.py` - Test files only  
- `src/mentat/**/*.py` - Core module files
- `Makefile` - Makefile instructions
- `pyproject.toml` - Python configuration

### Content Structure
1. **Purpose** - Clear scope statement
2. **Project Context** - Mentat CLI specifics
3. **Rules and Standards** - Coding standards, conventions
4. **Tool Integration** - Project commands and tools
5. **Validation** - How to verify compliance

### Template
```markdown
---
applyTo:
  - "pattern"
---

# Topic Instructions  

**Reference**: [URL]

## Purpose
Scope description.

## Project Context
- Mentat CLI: Python + uv, SOLID principles
- Quality gates: `make check`
- Tools: ruff, mypy, pytest

## Rules and Standards
Key requirements and conventions.

## Tool Integration  
Project-specific commands and usage.

## Validation
Verification steps.
```

## Key Principles
- **Focused Scope**: One instruction per file type/domain
- **Precise Patterns**: Use specific `applyTo` glob patterns
- **Project-Specific**: Reference Mentat CLI tools and conventions
- **Cross-Reference**: Link related instructions rather than duplicate