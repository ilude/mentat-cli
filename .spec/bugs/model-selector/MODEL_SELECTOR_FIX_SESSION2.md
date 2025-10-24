# Model Selector Fix - Session 2

## Problem Statement
When users selected OpenAI in the `/model` command, nothing would happen - no loading indicator, no model list appeared. The same action worked fine for Anthropic.

## Root Cause Analysis

### Investigation Results
1. **Providers work correctly**: Created test script `test_model_selector_debug.py` that verified:
   - Anthropic provider: Returns 11 models successfully
   - OpenAI provider: Returns 96 models successfully
   - Both providers respond correctly when called directly

2. **Issue is not with provider logic**: Both `list_models()` methods work fine in isolation

3. **Issue identified as threading/UI interaction problem**: 
   - Background thread successfully fetches models
   - But `call_from_thread()` callback or subsequent UI update fails silently
   - No exceptions are visible to the user

## Fixes Applied

### 1. Added Comprehensive Logging (`src/mentat/tui/model_selector.py`)
- Added `import logging` and `logger = logging.getLogger(__name__)`
- Log at every step: fetch start, fetch success, UI update calls
- Log full tracebacks when exceptions occur
- All logs written to `.mentat_debug.log` (file-based, doesn't interfere with TUI)

### 2. Enhanced Error Handling in Background Thread
- Wrap `_fetch()` in try/except/finally block
- Log exceptions with full traceback
- Show user-friendly error messages (truncated to 60 chars)
- Always attempt UI update even if fetch fails
- Catch exceptions in UI update wrapper as well

### 3. Fixed ListView Index Race Condition
**Before:**
```python
list_view.clear()
list_view.index = 0  # ERROR: Setting index on empty list
list_view.append(ListItem(Static("Loading models...")))
```

**After:**
```python
list_view.clear()
list_view.append(ListItem(Static("Loading models...")))  # Add FIRST
# Set index AFTER appending
if list_view.children:
    try:
        list_view.index = 0
    except Exception as e:
        logger.error(f"Error setting loading index: {e}")
```

### 4. Improved Closure Capture in Threading
**Before:**
```python
self.app.call_from_thread(self._show_model_list, models)
```

**After:**
```python
def update_ui() -> None:
    try:
        self._show_model_list(models)
    except Exception as e:
        logger.error(f"Error in UI update: {e}")
        logger.error(traceback.format_exc())

self.app.call_from_thread(update_ui)
```

This ensures:
- Proper variable capture (models list is properly closed over)
- Exceptions in UI update are logged
- Better debugging if something goes wrong

### 5. Added Logging to CLI (`src/mentat/cli.py`)
- Added debug logging to `/model` command flow
- Logs provider resolution, model listing start/end
- Logs model selection results
- Helps trace the full flow from user action to model selection

### 6. Enabled Debug Logging in REPL
- Added `basicConfig` at start of REPL to enable DEBUG level logging
- Logs written to `.mentat_debug.log` file instead of stdout (avoids TUI corruption)

## Testing Artifacts Created

### `test_model_selector_debug.py`
- Tests direct provider resolution and model listing
- Verifies both Anthropic and OpenAI return models correctly
- Confirms providers are working properly

### `.mentat_debug.log`
- Auto-created when running `mentat` command
- Contains detailed debugging information
- Can be reviewed to diagnose issues

## How to Debug Further

1. **Run the CLI and try `/model` command:**
   ```bash
   mentat
   ```

2. **Check debug log:**
   ```bash
   cat .mentat_debug.log
   ```

3. **Look for:**
   - `Fetching models for provider: openai` - fetch started
   - `Successfully fetched X models for openai` - fetch succeeded
   - `Calling call_from_thread to update UI` - callback scheduled
   - `_show_model_list called with X models` - UI update started
   - Any `Error` lines indicating where failure occurred

## Expected Behavior After Fix

1. User types `/model`
2. Textual UI appears showing provider list
3. User navigates and presses Enter on "openai"
4. "Loading models..." message appears
5. After ~1-2 seconds, list of 96 OpenAI models appears
6. User navigates and selects a model
7. Model is set and REPL returns to prompt

## Key Code Changes Summary

**File: `src/mentat/tui/model_selector.py`**
- Added logging at module level
- Added try/except/finally around _show_model_list()
- Fixed ListView index race condition
- Enhanced _fetch() with detailed error logging
- Added wrapper lambda for call_from_thread callback
- Added error handling in wrapper lambda
- Improved logging messages throughout

**File: `src/mentat/cli.py`**
- Added logging import
- Added basicConfig to enable DEBUG logging
- Added debug logs to /model command flow
- Added logs for provider resolution and model listing

## Future Improvements

1. **Add timeout mechanism**: If models don't load after 10 seconds, show timeout error
2. **Add visual feedback**: Maybe a spinner or progress bar in the "Loading models..." item
3. **Cache provider models**: Avoid re-fetching on subsequent /model commands
4. **Async model fetching**: Use asyncio instead of threading for better Textual integration
