---
mode: 'agent'
model: gpt-5-mini
description: 'Run make check and iteratively fix all errors and warnings until clean. Focus on linting, type checking, and testing issues. Keep iterating until zero errors and warnings remain.'
---

# Quality Check and Fix

## Objective
Run `make check` and systematically address all errors and warnings until the command passes completely with no issues.

## Context
- Project uses `make check` as the primary quality gate
- Includes: linting (ruff), type checking (mypy), and testing (pytest)
- Must achieve zero errors and zero warnings for completion
- Current known issues: test import errors, interface mismatches, missing pytest-asyncio

## Instructions

### Phase 1: Initial Assessment
1. Run `make check` to see current status
2. Categorize all errors and warnings by type:
   - Linting errors (ruff)
   - Type checking errors (mypy) 
   - Import errors (pytest collection)
   - Test failures (pytest execution)
   - Missing dependencies

### Phase 2: Systematic Resolution
For each category of issues, apply these steps:

#### Linting Issues (ruff)
1. Run `uv run ruff check .` to see specific errors
2. Use `uv run ruff check --fix .` for auto-fixable issues
3. Manually fix remaining issues (syntax, imports, type annotations)
4. Verify with `uv run ruff check .` until "All checks passed!"

#### Type Checking Issues (mypy)
1. Run `uv run mypy src` to see type errors
2. Add missing type annotations
3. Fix type mismatches and imports
4. Verify with `uv run mypy src` until "Success: no issues found"

#### Import Errors (pytest)
1. Identify missing classes/modules in test imports
2. Either:
   - Implement missing classes in source code, OR
   - Update test imports to match actual implementation
3. Ensure all test files can be imported without errors

#### Interface Mismatches
1. Compare test expectations with actual implementation
2. Update tests to match current interfaces:
   - `Session.session_id` instead of `Session.id`
   - Correct method signatures and parameters
   - Proper async/await usage

#### Missing Dependencies
1. Add `pytest-asyncio` to pyproject.toml if needed for async tests
2. Run `uv sync` to update dependencies
3. Verify async test markers are recognized

### Phase 3: Iteration Loop
**CRITICAL**: Continue this process until completion:

1. Run `make check`
2. If ANY errors or warnings exist:
   - Identify the next highest priority issue
   - Apply appropriate fix from Phase 2
   - Return to step 1
3. If NO errors or warnings exist:
   - Run `make check` one final time to confirm
   - Document any changes made
   - TASK COMPLETE

### Phase 4: Verification
1. Run `make check` and confirm output shows:
   - `uv run ruff check .` → "All checks passed!"
   - `uv run mypy src` → "Success: no issues found"
   - `uv run pytest -q` → All tests pass OR properly skip with no errors
2. Verify original working tests still pass:
   - `uv run pytest tests/test_buses.py tests/test_cli.py -v`
3. Confirm no regressions in core functionality

## Success Criteria
- [ ] `make check` exits with code 0
- [ ] Zero linting errors from ruff
- [ ] Zero type checking errors from mypy  
- [ ] Zero pytest collection errors
- [ ] All tests pass or skip appropriately
- [ ] No warnings in output
- [ ] Original 5 core tests still pass

## Error Handling

### Common Issues and Solutions
- **Import errors**: Check actual class names and module structure
- **Type annotation errors**: Add return types to all functions, especially nested ones
- **Test interface mismatches**: Align test expectations with current implementation
- **Async test warnings**: Add pytest-asyncio dependency and proper configuration

### When Stuck
1. Focus on one error at a time
2. Check actual source code to understand current interfaces
3. Prioritize linting and type checking before test fixes
4. Use `git status` to track changes and avoid regressions

### Quality Gates Priority
1. Linting (ruff) - Foundation for code quality
2. Type checking (mypy) - Catch type-related issues
3. Test collection - Ensure tests can be loaded
4. Test execution - Verify functionality

## Notes
- This is an iterative process - expect multiple cycles
- Each fix may reveal new issues
- Always verify fixes don't break existing functionality
- Document significant changes for review