"""Tests for safety approvals system."""

import json
import tempfile
from pathlib import Path

import pytest

from mentat.safety.approvals import (
    ApprovalScope,
    ConsoleApprovalManager,
    InMemoryApprovalStore,
    PersistentApprovalStore,
)
from mentat.safety.validator import CommandValidation, ValidationResult


class TestInMemoryApprovalStore:
    """Test in-memory approval store."""

    @pytest.fixture
    def store(self):
        """Create an in-memory approval store."""
        return InMemoryApprovalStore()

    def test_add_and_check_approval(self, store):
        """Test adding and checking approvals."""
        assert store.has_approval("test_command") is False

        store.add_approval("test_command", ApprovalScope.SESSION)
        assert store.has_approval("test_command") is True

    def test_remove_approval(self, store):
        """Test removing approvals."""
        store.add_approval("test_command", ApprovalScope.SESSION)
        assert store.has_approval("test_command") is True

        store.remove_approval("test_command")
        assert store.has_approval("test_command") is False

    def test_clear_approvals(self, store):
        """Test clearing all approvals."""
        store.add_approval("command1", ApprovalScope.SESSION)
        store.add_approval("command2", ApprovalScope.SESSION)

        assert store.has_approval("command1") is True
        assert store.has_approval("command2") is True

        store.clear_approvals()

        assert store.has_approval("command1") is False
        assert store.has_approval("command2") is False

    def test_get_all_approvals(self, store):
        """Test getting all approvals."""
        approvals = store.get_all_approvals()
        assert len(approvals) == 0

        store.add_approval("command1", ApprovalScope.SESSION)
        store.add_approval("command2", ApprovalScope.ONCE)

        approvals = store.get_all_approvals()
        assert len(approvals) == 2
        assert ("command1", ApprovalScope.SESSION) in approvals
        assert ("command2", ApprovalScope.ONCE) in approvals


class TestPersistentApprovalStore:
    """Test persistent approval store."""

    @pytest.fixture
    def temp_store_path(self):
        """Create a temporary file path for the store."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            return Path(f.name)

    @pytest.fixture
    def store(self, temp_store_path):
        """Create a persistent approval store."""
        store = PersistentApprovalStore(temp_store_path)
        yield store
        # Cleanup
        if temp_store_path.exists():
            temp_store_path.unlink()

    def test_persistence(self, store, temp_store_path):
        """Test that approvals persist across instances."""
        # Add approvals
        store.add_approval("command1", ApprovalScope.PERSISTENT)
        store.add_approval("command2", ApprovalScope.SESSION)

        # Create new instance with same path
        new_store = PersistentApprovalStore(temp_store_path)

        # Only persistent approvals should remain
        assert new_store.has_approval("command1") is True
        assert new_store.has_approval("command2") is False

    def test_save_and_load(self, store):
        """Test explicit save and load operations."""
        store.add_approval("test_command", ApprovalScope.PERSISTENT)

        # Force save
        store.save()

        # Verify file exists and contains data
        assert store.store_path.exists()
        with open(store.store_path) as f:
            data = json.load(f)
        assert "test_command" in data

        # Clear and reload
        store.clear_approvals()
        assert store.has_approval("test_command") is False

        store.load()
        assert store.has_approval("test_command") is True

    def test_file_corruption_handling(self, temp_store_path):
        """Test handling of corrupted store files."""
        # Create corrupted file
        with open(temp_store_path, "w") as f:
            f.write("invalid json content")

        # Should handle corruption gracefully
        store = PersistentApprovalStore(temp_store_path)
        approvals = store.get_all_approvals()
        assert len(approvals) == 0

    def test_missing_file_handling(self, temp_store_path):
        """Test handling of missing store files."""
        # Remove file if it exists
        if temp_store_path.exists():
            temp_store_path.unlink()

        # Should handle missing file gracefully
        store = PersistentApprovalStore(temp_store_path)
        approvals = store.get_all_approvals()
        assert len(approvals) == 0


class TestConsoleApprovalManager:
    """Test console approval manager."""

    @pytest.fixture
    def manager(self):
        """Create console approval manager with in-memory store."""
        store = InMemoryApprovalStore()
        return ConsoleApprovalManager(store)

    @pytest.fixture
    def validation(self):
        """Sample validation result requiring approval."""
        return CommandValidation(
            command="test command",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="medium",
            matched_pattern=None,
            reason="Command not in allowed patterns",
        )

    def test_check_existing_approval(self, manager, validation):
        """Test checking existing approvals."""
        # No existing approval
        has_approval = manager.check_approval(validation)
        assert has_approval is False

        # Add approval and check again
        manager.store.add_approval(validation.command, ApprovalScope.SESSION)
        has_approval = manager.check_approval(validation)
        assert has_approval is True

    def test_approval_scope_handling(self, manager, validation):
        """Test different approval scopes."""
        # Test ONCE scope - should be removed after first use
        result = manager.handle_approval_request(validation, ApprovalScope.ONCE)
        assert result is True

        # Check that approval exists
        assert manager.store.has_approval(validation.command) is True

        # Use the approval - should be removed
        has_approval = manager.check_approval(validation)
        assert has_approval is True
        assert manager.store.has_approval(validation.command) is False  # Removed after use

        # Test SESSION scope - should persist during session
        result = manager.handle_approval_request(validation, ApprovalScope.SESSION)
        assert result is True

        # Should persist after use
        has_approval = manager.check_approval(validation)
        assert has_approval is True
        assert manager.store.has_approval(validation.command) is True

    def test_format_approval_prompt(self, manager, validation):
        """Test approval prompt formatting."""
        prompt = manager._format_approval_prompt(validation)

        assert validation.command in prompt
        assert validation.risk_level in prompt
        assert validation.reason in prompt

    def test_format_risk_indicator(self, manager):
        """Test risk indicator formatting."""
        indicator = manager._format_risk_indicator("low")
        assert "🟢" in indicator or "LOW" in indicator

        indicator = manager._format_risk_indicator("medium")
        assert "🟡" in indicator or "MEDIUM" in indicator

        indicator = manager._format_risk_indicator("high")
        assert "🟠" in indicator or "HIGH" in indicator

        indicator = manager._format_risk_indicator("critical")
        assert "🔴" in indicator or "CRITICAL" in indicator

    def test_approval_statistics(self, manager):
        """Test approval statistics."""
        stats = manager.get_approval_stats()
        assert stats["total_approvals"] == 0
        assert stats["by_scope"]["session"] == 0
        assert stats["by_scope"]["persistent"] == 0
        assert stats["by_scope"]["once"] == 0

        # Add some approvals
        manager.store.add_approval("cmd1", ApprovalScope.SESSION)
        manager.store.add_approval("cmd2", ApprovalScope.PERSISTENT)
        manager.store.add_approval("cmd3", ApprovalScope.ONCE)

        stats = manager.get_approval_stats()
        assert stats["total_approvals"] == 3
        assert stats["by_scope"]["session"] == 1
        assert stats["by_scope"]["persistent"] == 1
        assert stats["by_scope"]["once"] == 1

    def test_clear_expired_approvals(self, manager):
        """Test clearing expired approvals."""
        # Add approvals with different scopes
        manager.store.add_approval("session_cmd", ApprovalScope.SESSION)
        manager.store.add_approval("persistent_cmd", ApprovalScope.PERSISTENT)
        manager.store.add_approval("once_cmd", ApprovalScope.ONCE)

        # Clear session-scoped approvals
        manager.clear_session_approvals()

        assert manager.store.has_approval("session_cmd") is False
        assert manager.store.has_approval("persistent_cmd") is True
        assert manager.store.has_approval("once_cmd") is False  # ONCE is also session-scoped

    def test_approval_export_import(self, manager):
        """Test exporting and importing approvals."""
        # Add some approvals
        manager.store.add_approval("cmd1", ApprovalScope.SESSION)
        manager.store.add_approval("cmd2", ApprovalScope.PERSISTENT)

        # Export approvals
        exported = manager.export_approvals()
        assert len(exported) == 2

        # Clear and import
        manager.store.clear_approvals()
        assert len(manager.store.get_all_approvals()) == 0

        manager.import_approvals(exported)
        assert len(manager.store.get_all_approvals()) == 2
        assert manager.store.has_approval("cmd1") is True
        assert manager.store.has_approval("cmd2") is True

    def test_approval_with_patterns(self, manager):
        """Test approvals with command patterns."""
        # Test exact command matching
        validation1 = CommandValidation(
            command="git status",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="low",
            matched_pattern=None,
            reason="Command not in patterns",
        )

        manager.store.add_approval("git status", ApprovalScope.SESSION)
        assert manager.check_approval(validation1) is True

        # Test that similar command doesn't match
        validation2 = CommandValidation(
            command="git status --porcelain",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="low",
            matched_pattern=None,
            reason="Command not in patterns",
        )

        assert manager.check_approval(validation2) is False

    def test_approval_context_information(self, manager, validation):
        """Test that approval context includes helpful information."""
        # Mock the _prompt_user method to capture the prompt
        prompted_text = None

        def mock_prompt(text):
            nonlocal prompted_text
            prompted_text = text
            return True

        manager._prompt_user = mock_prompt

        # Request approval
        manager.request_approval(validation)

        # Verify prompt contains context
        assert prompted_text is not None
        assert validation.command in prompted_text
        assert validation.risk_level in prompted_text

    def test_persistent_store_remove_and_clear(self):
        """Test PersistentApprovalStore remove and clear operations."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = Path(f.name)

        try:
            store = PersistentApprovalStore(temp_path)

            # Test remove_approval
            store.add_approval("cmd1", ApprovalScope.PERSISTENT)
            assert store.has_approval("cmd1") is True

            store.remove_approval("cmd1")
            assert store.has_approval("cmd1") is False

            # Test clear_approvals doesn't affect persistence
            store.add_approval("cmd2", ApprovalScope.PERSISTENT)
            store.clear_approvals()
            assert len(store.get_all_approvals()) == 0

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_persistent_store_corrupted_file_handling(self):
        """Test PersistentApprovalStore handles corrupted JSON files gracefully."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            temp_path = Path(f.name)

        try:
            # Create corrupted JSON file
            temp_path.write_text("invalid json content")

            # Should handle corruption gracefully
            store = PersistentApprovalStore(temp_path)
            assert len(store.get_all_approvals()) == 0

            # Should be able to add approvals after corruption
            store.add_approval("test_cmd", ApprovalScope.PERSISTENT)
            assert store.has_approval("test_cmd") is True

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_console_manager_formatting_methods(self, manager):
        """Test ConsoleApprovalManager prompt and risk formatting."""
        validation = CommandValidation(
            command="rm -rf /",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="critical",
            matched_pattern=None,
            reason="Dangerous deletion command",
        )

        # Test prompt formatting
        prompt = manager._format_approval_prompt(validation)
        assert "Command requires approval:" in prompt
        assert "rm -rf /" in prompt
        assert "critical" in prompt
        assert "Dangerous deletion command" in prompt

        # Test risk indicator formatting
        assert manager._format_risk_indicator("low") == "🟢 LOW"
        assert manager._format_risk_indicator("medium") == "🟡 MEDIUM"
        assert manager._format_risk_indicator("high") == "🟠 HIGH"
        assert manager._format_risk_indicator("critical") == "🔴 CRITICAL"
        assert manager._format_risk_indicator("unknown") == "UNKNOWN"

    def test_console_manager_once_consumption(self, manager):
        """Test that ONCE approvals are consumed after first check."""
        validation = CommandValidation(
            command="test_cmd",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="low",
            matched_pattern=None,
            reason="Test command",
        )

        # Add ONCE approval
        manager.store.add_approval("test_cmd", ApprovalScope.ONCE)
        assert manager.store.has_approval("test_cmd") is True

        # First check should return True and consume the approval
        assert manager.check_approval(validation) is True
        assert manager.store.has_approval("test_cmd") is False  # Should be consumed

        # Second check should return False
        assert manager.check_approval(validation) is False

    def test_console_manager_approval_stats(self, manager):
        """Test ConsoleApprovalManager.get_approval_stats method."""
        # Test empty stats
        stats = manager.get_approval_stats()
        assert stats["total_approvals"] == 0
        assert stats["by_scope"]["session"] == 0
        assert stats["by_scope"]["persistent"] == 0
        assert stats["by_scope"]["once"] == 0

        # Add various approval types
        manager.store.add_approval("cmd1", ApprovalScope.SESSION)
        manager.store.add_approval("cmd2", ApprovalScope.PERSISTENT)
        manager.store.add_approval("cmd3", ApprovalScope.ONCE)
        manager.store.add_approval("cmd4", ApprovalScope.SESSION)

        stats = manager.get_approval_stats()
        assert stats["total_approvals"] == 4
        assert stats["by_scope"]["session"] == 2
        assert stats["by_scope"]["persistent"] == 1
        assert stats["by_scope"]["once"] == 1

    def test_console_manager_clear_session_approvals(self, manager):
        """Test ConsoleApprovalManager.clear_session_approvals method."""
        # Add mixed approval types
        manager.store.add_approval("session_cmd", ApprovalScope.SESSION)
        manager.store.add_approval("persistent_cmd", ApprovalScope.PERSISTENT)
        manager.store.add_approval("once_cmd", ApprovalScope.ONCE)

        # Clear session approvals
        manager.clear_session_approvals()

        # Only persistent should remain
        assert manager.store.has_approval("session_cmd") is False
        assert manager.store.has_approval("persistent_cmd") is True
        assert manager.store.has_approval("once_cmd") is False

    def test_console_manager_handle_approval_request(self, manager):
        """Test ConsoleApprovalManager.handle_approval_request method."""
        validation = CommandValidation(
            command="test_cmd",
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="low",
            matched_pattern=None,
            reason="Test command",
        )

        # Test successful approval handling
        result = manager.handle_approval_request(validation, ApprovalScope.SESSION)
        assert result is True
        assert manager.store.has_approval("test_cmd") is True

    def test_console_manager_export_import_approvals(self, manager):
        """Test ConsoleApprovalManager export/import functionality."""
        # Add approvals
        manager.store.add_approval("cmd1", ApprovalScope.SESSION)
        manager.store.add_approval("cmd2", ApprovalScope.PERSISTENT)

        # Test export
        exported = manager.export_approvals()
        assert len(exported) == 2
        assert {"command": "cmd1", "scope": "session"} in exported
        assert {"command": "cmd2", "scope": "persistent"} in exported

        # Clear store and test import
        manager.store.clear_approvals()
        imported_data = [
            {"command": "imported_cmd1", "scope": "session"},
            {"command": "imported_cmd2", "scope": "persistent"},
            {"command": "invalid_cmd", "scope": "invalid"},  # Should default to session
        ]

        manager.import_approvals(imported_data)
        assert manager.store.has_approval("imported_cmd1") is True
        assert manager.store.has_approval("imported_cmd2") is True
        assert (
            manager.store.has_approval("invalid_cmd") is True
        )  # Should be imported with session scope


class TestApprovalStore:
    """Test the ApprovalStore class for async operations and file I/O."""

    @pytest.fixture
    def temp_path(self):
        """Create a temporary directory for approval storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def approval_store(self, temp_path):
        """Create an approval store with temporary directory."""
        from mentat.safety.approvals import ApprovalStore

        return ApprovalStore(base_path=temp_path / "approvals")

    @pytest.mark.asyncio
    async def test_store_persistent_approval(self, approval_store):
        """Test storing persistent approvals."""
        command_pattern = "git commit -m *"

        # Store approval
        await approval_store.store_approval(command_pattern, ApprovalScope.PERSISTENT)

        # Check it was stored
        has_approval = await approval_store.has_approval("git commit -m 'test'")
        assert has_approval is True

    @pytest.mark.asyncio
    async def test_store_session_approval(self, approval_store):
        """Test storing session-scoped approvals."""
        command_pattern = "npm install *"
        session_id = "test_session_123"

        # Store approval
        await approval_store.store_approval(command_pattern, ApprovalScope.SESSION, session_id)

        # Check it was stored
        has_approval = await approval_store.has_approval("npm install lodash", session_id)
        assert has_approval is True

        # Should not match without session
        has_approval_no_session = await approval_store.has_approval("npm install lodash")
        assert has_approval_no_session is False

    @pytest.mark.asyncio
    async def test_store_once_approval(self, approval_store):
        """Test storing ONCE scope approval (no storage needed)."""
        # ONCE approvals don't need storage, but should not error
        await approval_store.store_approval("test", ApprovalScope.ONCE)

        # Should not be found since ONCE isn't stored
        has_approval = await approval_store.has_approval("test")
        assert has_approval is False

    @pytest.mark.asyncio
    async def test_persistent_file_corruption_handling(self, approval_store):
        """Test handling of corrupted persistent approval file."""
        # Write corrupted JSON
        approval_store.persistent_file.parent.mkdir(parents=True, exist_ok=True)
        approval_store.persistent_file.write_text("invalid json {")

        # Should handle corruption gracefully
        has_approval = await approval_store._has_persistent_approval("test")
        assert has_approval is False

        # Should be able to store new approvals after corruption
        await approval_store._store_persistent_approval("test_pattern")

        # Should now work correctly
        has_approval = await approval_store._has_persistent_approval("test_pattern")
        assert has_approval is True

    @pytest.mark.asyncio
    async def test_persistent_file_missing_approvals_key(self, approval_store):
        """Test handling of persistent file with missing approvals key."""
        # Write JSON without approvals key
        approval_store.persistent_file.parent.mkdir(parents=True, exist_ok=True)
        with open(approval_store.persistent_file, "w") as f:
            json.dump({"other_key": "value"}, f)

        # Should handle missing key gracefully
        await approval_store._store_persistent_approval("test_pattern")

        # Should work correctly after fixing structure
        has_approval = await approval_store._has_persistent_approval("test_pattern")
        assert has_approval is True

    @pytest.mark.asyncio
    async def test_persistent_file_invalid_approvals_type(self, approval_store):
        """Test handling of persistent file with wrong approvals type."""
        # Write JSON with approvals as non-list
        approval_store.persistent_file.parent.mkdir(parents=True, exist_ok=True)
        with open(approval_store.persistent_file, "w") as f:
            json.dump({"approvals": "not_a_list"}, f)

        # Should convert to list and work
        await approval_store._store_persistent_approval("test_pattern")

        has_approval = await approval_store._has_persistent_approval("test_pattern")
        assert has_approval is True

    @pytest.mark.asyncio
    async def test_cleanup_session_approvals(self, approval_store):
        """Test cleanup of session approvals."""
        session_id = "test_session"

        # Add session approvals
        await approval_store._store_session_approval("pattern1", session_id)
        await approval_store._store_session_approval("pattern2", session_id)

        # Verify they exist
        assert await approval_store._has_session_approval("pattern1", session_id)

        # Clean up
        await approval_store.cleanup_session_approvals(session_id)

        # Should be gone
        assert not await approval_store._has_session_approval("pattern1", session_id)

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_session(self, approval_store):
        """Test cleanup of nonexistent session (should not error)."""
        # Should not error when cleaning up nonexistent session
        await approval_store.cleanup_session_approvals("nonexistent_session")

    @pytest.mark.asyncio
    async def test_list_approvals_all_scopes(self, approval_store):
        """Test listing approvals across all scopes."""
        # Add persistent approval
        await approval_store._store_persistent_approval("persistent_pattern")

        # Add session approval
        session_id = "test_session"
        await approval_store._store_session_approval("session_pattern", session_id)

        # List all approvals
        approvals = await approval_store.list_approvals()

        # Should contain both
        patterns = [a["pattern"] for a in approvals]
        assert "persistent_pattern" in patterns
        assert "session_pattern" in patterns

    @pytest.mark.asyncio
    async def test_list_approvals_persistent_only(self, approval_store):
        """Test listing only persistent approvals."""
        # Add both types
        await approval_store._store_persistent_approval("persistent_pattern")
        await approval_store._store_session_approval("session_pattern", "session")

        # List only persistent
        approvals = await approval_store.list_approvals(ApprovalScope.PERSISTENT)

        # Should contain only persistent
        assert len(approvals) == 1
        assert approvals[0]["pattern"] == "persistent_pattern"
        assert approvals[0]["scope"] == "persistent"

    @pytest.mark.asyncio
    async def test_list_approvals_session_only(self, approval_store):
        """Test listing only session approvals."""
        # Add both types
        await approval_store._store_persistent_approval("persistent_pattern")
        session_id = "test_session"
        await approval_store._store_session_approval("session_pattern", session_id)

        # List only session
        approvals = await approval_store.list_approvals(ApprovalScope.SESSION)

        # Should contain only session
        assert len(approvals) == 1
        assert approvals[0]["pattern"] == "session_pattern"
        assert approvals[0]["scope"] == "session"
        assert approvals[0]["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_list_persistent_approvals_missing_file(self, approval_store):
        """Test listing persistent approvals when file doesn't exist."""
        # Ensure file doesn't exist
        if approval_store.persistent_file.exists():
            approval_store.persistent_file.unlink()

        # Should return empty list
        approvals = await approval_store._list_persistent_approvals()
        assert approvals == []

    @pytest.mark.asyncio
    async def test_list_persistent_approvals_corrupted_file(self, approval_store):
        """Test listing persistent approvals with corrupted file."""
        # Write corrupted file
        approval_store.persistent_file.parent.mkdir(parents=True, exist_ok=True)
        approval_store.persistent_file.write_text("invalid json")

        # Should return empty list gracefully
        approvals = await approval_store._list_persistent_approvals()
        assert approvals == []

    def test_pattern_matches_exact(self, approval_store):
        """Test exact pattern matching."""
        assert approval_store._pattern_matches("git status", "git status") is True
        assert approval_store._pattern_matches("git status", "git commit") is False

    def test_pattern_matches_wildcard(self, approval_store):
        """Test wildcard pattern matching."""
        assert approval_store._pattern_matches("git commit -m hello", "git commit *") is True
        assert approval_store._pattern_matches("npm install lodash", "npm install *") is True
        assert approval_store._pattern_matches("git status", "npm *") is False

    @pytest.mark.asyncio
    async def test_has_approval_no_session_id(self, approval_store):
        """Test checking approval without session ID."""
        # Add persistent approval
        await approval_store._store_persistent_approval("test_pattern")

        # Should find persistent approval without session ID
        has_approval = await approval_store.has_approval("test_pattern")
        assert has_approval is True

        # Should not find non-existent pattern
        has_approval = await approval_store.has_approval("nonexistent")
        assert has_approval is False

    @pytest.mark.asyncio
    async def test_session_approval_duplicate_pattern(self, approval_store):
        """Test adding duplicate session approval patterns."""
        session_id = "test_session"
        pattern = "duplicate_pattern"

        # Add same pattern twice
        await approval_store._store_session_approval(pattern, session_id)
        await approval_store._store_session_approval(pattern, session_id)

        # Should only exist once in the list
        assert len(approval_store.session_approvals[session_id]) == 1
        assert approval_store.session_approvals[session_id][0] == pattern


class TestConsoleApprovalManagerEdgeCases:
    """Test edge cases for ConsoleApprovalManager."""

    @pytest.fixture
    def temp_path(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def manager_with_store(self, temp_path):
        """Create manager with real approval store."""
        from mentat.safety.approvals import ApprovalStore

        store = ApprovalStore(base_path=temp_path / "approvals")
        return ConsoleApprovalManager(approval_store=store)

    def test_prompt_user_keyboard_interrupt(self, manager_with_store):
        """Test handling of KeyboardInterrupt during prompt."""

        def mock_input(prompt):
            raise KeyboardInterrupt()

        # Mock input to raise KeyboardInterrupt
        import builtins

        original_input = builtins.input
        builtins.input = mock_input

        try:
            result = manager_with_store._prompt_user("Test prompt")
            assert result is False
        finally:
            builtins.input = original_input

    def test_prompt_user_eof_error(self, manager_with_store):
        """Test handling of EOFError during prompt."""

        def mock_input(prompt):
            raise EOFError()

        # Mock input to raise EOFError
        import builtins

        original_input = builtins.input
        builtins.input = mock_input

        try:
            result = manager_with_store._prompt_user("Test prompt")
            assert result is False
        finally:
            builtins.input = original_input

    def test_request_approval_variations(self, manager_with_store):
        """Test request_approval with various input patterns."""
        validation = CommandValidation(
            command="test command",
            result=ValidationResult.REQUIRES_APPROVAL,
            explanation="Test approval request",
        )

        # Mock different user responses
        responses = ["y", "yes", "Y", "YES", "n", "no", "N", "NO", "invalid", ""]
        expected = [True, True, True, True, False, False, False, False, False, False]

        import builtins

        original_input = builtins.input

        for response, expected_result in zip(responses, expected, strict=False):
            builtins.input = lambda _prompt, r=response: r
            try:
                result = manager_with_store.request_approval(validation)
                assert result == expected_result
            finally:
                builtins.input = original_input
