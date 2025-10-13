---
applyTo:
  - ".github/prompts/*.prompt.md"
---

# GitHub Copilot Prompt Files Instructions

**Reference**: https://code.visualstudio.com/docs/copilot/customization/prompt-files

## Purpose
Create specialized prompt files for GitHub Copilot tasks and workflows.

## Project-Specific Requirements

### File Naming
- `<task-name>.prompt.md` (e.g., `check.prompt.md`, `test.prompt.md`)

### Frontmatter
```yaml
---
description: "Clear description of what this prompt accomplishes"
---
```

### Project Tools to Reference
- `make check` - Run all quality gates
- `make lint test` - Linting and testing 
- `uv run ruff check .` - Code linting
- `uv run mypy src` - Type checking
- `uv run pytest -q` - Test execution

### Essential Content Structure
1. **Objective** - Clear goal statement
2. **Context** - Project background (Python + uv, SOLID principles, TOML config)
3. **Instructions** - Step-by-step with iteration conditions
4. **Success Criteria** - Checkboxes for completion
5. **Error Handling** - Common issues and solutions

### Template
```markdown
---
description: "Task description"
---

# Task Name

## Objective
What to accomplish.

## Context  
- Mentat CLI: Python + uv project
- Quality gates: `make check`
- Architecture: SOLID, CQRS, IoC

## Instructions
1. Specific steps
2. Include iteration logic
3. Reference make targets

## Success Criteria
- [ ] Concrete checkboxes

## Troubleshooting
Common fixes.
```