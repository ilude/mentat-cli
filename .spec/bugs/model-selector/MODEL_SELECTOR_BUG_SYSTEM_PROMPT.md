# Model Selector Bug - System Prompt for Investigation

## Project Context
- **Project**: Mentat CLI - An agent-driven CLI tool built in Python
- **Framework**: Typer CLI with Textual TUI (Text User Interface)
- **Architecture**: CQRS pattern with IoC container, dependency injection
- **Key Components**: AI provider abstraction (Anthropic, OpenAI), command/query buses

## The Bug

### User-Reported Behavior
When users run the `/model` command in the REPL and select "openai", nothing happens - no loading indicator, no model list appears. The same action works fine for "anthropic".

**User's exact description**: "selecting openai and gpt-5-mini, then brings up the list of claude models.. selecting one of them does nothing" and later "selecting openai after using /model, nothing happens"

### Environment
- Python 3.14
- Textual 6.4.0
- Anthropic SDK (latest)
- OpenAI SDK (latest)
- Windows 10/11 with PowerShell

## Investigation Results

### What Works ✓
1. **Both providers work correctly when called directly**:
   - Anthropic provider: `list_models()` returns 11 models
   - OpenAI provider: `list_models()` returns 96 models
   - Both methods are synchronous and execute properly
   - API calls work, authentication works

2. **Provider resolution through IoC container works**:
   - `container.resolve("provider.anthropic")` → Returns working AnthropicProvider
   - `container.resolve("provider.openai")` → Returns working OpenAIProvider
   - Both have `list_models()` method that works

3. **Anthropic selection works**: When user selects "anthropic", models load and display correctly

### What Fails ✗
1. **OpenAI selection fails silently**: No error messages, no crash, just nothing happens
2. **No visible exception**: The failure is silent - no traceback shown to user
3. **Issue is isolated to Textual UI**: The problem occurs only when called from the TUI, not when tested directly

## Code Analysis

### Model Selector Architecture (`src/mentat/tui/model_selector.py`)

**Key Flow:**
1. User navigates to provider name and presses Enter
2. `action_select_item()` calls `_transition_to_model_selection()`
3. UI shows "Loading models..." placeholder
4. Background thread starts via `threading.Thread(target=_fetch, daemon=True)`
5. Thread calls `self.get_models(provider)` - this works fine
6. Thread calls `self.app.call_from_thread(self._show_model_list, models)` to update UI
7. `_show_model_list()` should update the ListView with models

**Problem Area**: Step 6-7, something fails silently

### Possible Root Causes

1. **`call_from_thread()` not being invoked or failing silently**
   - Textual's `call_from_thread()` might not be executing the callback
   - Exception might be swallowed internally by Textual
   - Race condition between thread and UI thread

2. **ListView state management issue**
   - After `list_view.clear()` and `list_view.index = 0`, state might be corrupted
   - Setting index before appending items could cause issues
   - ListView might not properly handle state transitions from provider → model view

3. **Closure/binding issue with bound methods**
   - Passing `self._show_model_list` as callback might not work properly with threading
   - Variable capture issue with `models` list in closure

4. **Exception in UI update callback not being logged**
   - Exception occurs in `_show_model_list()` but never surfaces
   - `call_from_thread()` might catch exceptions without logging

5. **Thread synchronization timing**
   - UI might not be ready when callback executes
   - Models list might be accessed before it's populated

## Fixes Attempted in Session 1

1. Added state machine (`_state = "providers"` / `_state = "models"`)
2. Changed from auto-trigger on selection to explicit Enter-key confirmation
3. Added bounds checking on ListView indices
4. Attempted to reset ListView state properly

**Result**: Tests pass, but issue still occurs in practice

## Fixes Attempted in Session 2

1. Added comprehensive logging (logs written to `.mentat_debug.log`)
2. Fixed ListView index race condition (set index AFTER appending items, not before)
3. Improved closure capture with wrapper lambda:
   ```python
   def update_ui() -> None:
       try:
           self._show_model_list(models)
       except Exception as e:
           logger.error(f"Error in UI update: {e}")
   self.app.call_from_thread(update_ui)
   ```
4. Added try/except/finally around `_fetch()` background thread
5. Added logging to CLI to trace `/model` command flow

**Expected to help**: But needs to be tested interactively

## Current Code State

### `src/mentat/tui/model_selector.py`
- Has logging infrastructure
- Background thread with error handling
- Wrapper lambda for callback
- Detailed logging at each step

### `src/mentat/cli.py`
- Logging enabled in REPL via `basicConfig`
- Debug logging in `/model` command handler
- Logs written to `.mentat_debug.log`

## Questions for Investigation

1. **Is `call_from_thread()` being called?** Check `.mentat_debug.log` for:
   ```
   Calling call_from_thread to update UI with X models
   ```

2. **Is `_show_model_list()` being invoked?** Check for:
   ```
   _show_model_list called with X models
   ```

3. **Is there an exception in the background thread?** Check for `Error` log entries

4. **Is there a timing issue?** Check timestamps in log file between fetch and UI update

5. **Is ListView being properly updated?** Check logging output:
   ```
   ListView cleared
   Added all X models
   Updated title
   Updated instructions
   ```

## Test Files Created

1. `test_model_selector_debug.py` - Direct provider testing (works)
2. `test_model_selector_tui.py` - Interactive TUI testing (not yet run)
3. `.mentat_debug.log` - Auto-created debug log file

## Suggested Investigation Approach for Larger Model

1. **Understand Textual's threading model**:
   - How does `call_from_thread()` work internally?
   - Are there known issues with threading in Textual 6.4.0?
   - Is there a better way to handle background operations?

2. **Analyze potential Textual-specific issues**:
   - ListView state transitions and clearing
   - Index management after clear/repopulate
   - Widget focus management during state changes
   - Screen lifecycle and app reference availability

3. **Consider alternative implementations**:
   - Use Textual's async/await patterns instead of threading?
   - Use a different callback mechanism?
   - Pre-fetch models synchronously before showing UI?
   - Use a different UI pattern (Worker class instead of threading)?

4. **Debug the actual execution**:
   - Run interactive session with `/model openai` 
   - Check `.mentat_debug.log` for where execution stops
   - Check if OpenAI API call itself is the bottleneck
   - Check if there's a difference in behavior between Anthropic and OpenAI lists

5. **Verify assumptions**:
   - Does the background thread actually complete for OpenAI?
   - Does `call_from_thread()` get called for OpenAI?
   - Does the wrapper lambda get executed?
   - Are there any exceptions being silently caught?

## Key Differences Between Anthropic (Works) and OpenAI (Fails)

| Aspect | Anthropic | OpenAI |
|--------|-----------|--------|
| Models Returned | 11 models | 96 models |
| Fetch Time | ~100ms | ~600ms |
| SDK Type | Anthropic SDK | OpenAI SDK |
| Error Handling | Simpler | More complex |
| Model List Size | Smaller | Larger |

**Hypothesis**: The issue might be related to:
- List size (96 vs 11 items might cause ListView performance issue)
- Fetch time (600ms vs 100ms might cause timeout/timing issue)
- SDK differences (OpenAI SDK might have thread-safety issues)

## Code Locations

- Model selector implementation: `src/mentat/tui/model_selector.py`
- CLI command handler: `src/mentat/cli.py` (lines 131-165)
- Provider implementations: `src/mentat/providers/openai.py` and `src/mentat/providers/anthropic_provider.py`
- Debug log: `.mentat_debug.log` (created when running mentat)

## Next Steps for Larger Model

1. Implement proper async/await using Textual's async patterns
2. Consider using Textual's `Worker` class instead of threading
3. Add pre-fetching strategy to avoid UI blocking
4. Review Textual documentation for ListView edge cases
5. Consider if ListView can handle 96+ items efficiently
6. Test with a simpler callback pattern (e.g., lambda vs bound method)
7. Check if there's a Textual version compatibility issue
