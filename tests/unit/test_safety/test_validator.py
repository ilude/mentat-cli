"""Tests for safety validator functionality."""

import pytest

from mentat.safety.validator import (
    BaseSafetyValidator,
    CommandValidation,
    SafetyError,
    SafetyMode,
    SafetyPattern,
    ValidationResult,
)


class ConcreteSafetyValidator(BaseSafetyValidator):
    """Concrete implementation for testing abstract base class."""

    def validate_command(self, command: str) -> CommandValidation:
        """Simple validation implementation for testing."""
        # Check for dangerous patterns
        dangerous_patterns = ["rm -rf", "del /s", "format c:", "sudo rm"]

        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return CommandValidation(
                    command=command,
                    result=ValidationResult.DENIED,
                    matched_pattern=SafetyPattern(
                        pattern=pattern,
                        is_allow=False,
                        description=f"Dangerous command pattern: {pattern}",
                    ),
                    risk_level="critical",
                    explanation=f"Command contains dangerous pattern: {pattern}",
                )

        # Check for allowed patterns
        safe_patterns = ["ls", "dir", "cat", "echo"]
        for pattern in safe_patterns:
            if command.lower().startswith(pattern):
                return CommandValidation(
                    command=command,
                    result=ValidationResult.ALLOWED,
                    matched_pattern=SafetyPattern(
                        pattern=pattern, is_allow=True, description=f"Safe command: {pattern}"
                    ),
                    risk_level="low",
                )

        # Default: requires approval
        return CommandValidation(
            command=command,
            result=ValidationResult.REQUIRES_APPROVAL,
            risk_level="medium",
            explanation="Command requires user approval",
        )

    def is_command_approved(self, command: str, session_id=None) -> bool:
        """Simple approval check for testing."""
        # Mock approval logic
        return command in getattr(self, "_approved_commands", set())

    def add_approval(self, command: str, session_id=None) -> None:
        """Add approval for testing."""
        if not hasattr(self, "_approved_commands"):
            self._approved_commands = set()
        self._approved_commands.add(command)

    def remove_approval(self, command: str, session_id=None) -> None:
        """Remove approval for testing."""
        if hasattr(self, "_approved_commands"):
            self._approved_commands.discard(command)

    def load_patterns(self, config_path: str) -> None:
        """Load patterns from config for testing."""
        # Mock implementation - just store the path
        self._config_path = config_path


class TestSafetyPattern:
    """Test SafetyPattern data class."""

    def test_safety_pattern_creation(self):
        """Test creating SafetyPattern instances."""
        allow_pattern = SafetyPattern(
            pattern="git status", is_allow=True, description="Safe git command"
        )

        assert allow_pattern.pattern == "git status"
        assert allow_pattern.is_allow is True
        assert allow_pattern.description == "Safe git command"

        deny_pattern = SafetyPattern(
            pattern="rm -rf *", is_allow=False, description="Dangerous deletion"
        )

        assert deny_pattern.pattern == "rm -rf *"
        assert deny_pattern.is_allow is False
        assert deny_pattern.description == "Dangerous deletion"


class TestCommandValidation:
    """Test CommandValidation data class."""

    def test_command_validation_creation(self):
        """Test creating CommandValidation instances."""
        pattern = SafetyPattern("test", True, "test pattern")

        validation = CommandValidation(
            command="test command",
            result=ValidationResult.ALLOWED,
            matched_pattern=pattern,
            risk_level="low",
            explanation="Test explanation",
        )

        assert validation.command == "test command"
        assert validation.result == ValidationResult.ALLOWED
        assert validation.matched_pattern == pattern
        assert validation.risk_level == "low"
        assert validation.explanation == "Test explanation"

    def test_command_validation_defaults(self):
        """Test CommandValidation with default values."""
        validation = CommandValidation(command="test", result=ValidationResult.REQUIRES_APPROVAL)

        assert validation.command == "test"
        assert validation.result == ValidationResult.REQUIRES_APPROVAL
        assert validation.matched_pattern is None
        assert validation.risk_level == "low"
        assert validation.explanation == ""


class TestSafetyMode:
    """Test SafetyMode enumeration."""

    def test_safety_mode_values(self):
        """Test SafetyMode enum values."""
        assert SafetyMode.AUTO.value == "auto"
        assert SafetyMode.CONFIRM.value == "confirm"
        assert SafetyMode.READONLY.value == "readonly"

    def test_safety_mode_from_string(self):
        """Test creating SafetyMode from string values."""
        assert SafetyMode("auto") == SafetyMode.AUTO
        assert SafetyMode("confirm") == SafetyMode.CONFIRM
        assert SafetyMode("readonly") == SafetyMode.READONLY

        with pytest.raises(ValueError):
            SafetyMode("invalid")


class TestValidationResult:
    """Test ValidationResult enumeration."""

    def test_validation_result_values(self):
        """Test ValidationResult enum values."""
        assert ValidationResult.ALLOWED.value == "allowed"
        assert ValidationResult.DENIED.value == "denied"
        assert ValidationResult.REQUIRES_APPROVAL.value == "requires_approval"


class TestBaseSafetyValidator:
    """Test BaseSafetyValidator abstract base class."""

    @pytest.fixture
    def validator(self):
        """Create concrete validator for testing."""
        return ConcreteSafetyValidator()

    def test_validator_initialization_default(self):
        """Test validator initialization with default safety mode."""
        validator = ConcreteSafetyValidator()

        assert validator.safety_mode == SafetyMode.CONFIRM
        assert validator.patterns == []

    def test_validator_initialization_custom_mode(self):
        """Test validator initialization with custom safety mode."""
        validator = ConcreteSafetyValidator(SafetyMode.AUTO)

        assert validator.safety_mode == SafetyMode.AUTO
        assert validator.patterns == []

    def test_get_safety_mode(self, validator):
        """Test getting current safety mode."""
        assert validator.get_safety_mode() == SafetyMode.CONFIRM

        validator.safety_mode = SafetyMode.READONLY
        assert validator.get_safety_mode() == SafetyMode.READONLY

    def test_set_safety_mode(self, validator):
        """Test setting safety mode."""
        validator.set_safety_mode(SafetyMode.AUTO)
        assert validator.safety_mode == SafetyMode.AUTO

        validator.set_safety_mode(SafetyMode.READONLY)
        assert validator.safety_mode == SafetyMode.READONLY

    def test_validate_command_denied(self, validator):
        """Test command validation with denied result."""
        result = validator.validate_command("rm -rf /important/data")

        assert result.result == ValidationResult.DENIED
        assert result.risk_level == "critical"
        assert result.matched_pattern is not None
        assert result.matched_pattern.is_allow is False
        assert "rm -rf" in result.explanation.lower()

    def test_validate_command_allowed(self, validator):
        """Test command validation with allowed result."""
        result = validator.validate_command("ls -la")

        assert result.result == ValidationResult.ALLOWED
        assert result.risk_level == "low"
        assert result.matched_pattern is not None
        assert result.matched_pattern.is_allow is True

    def test_validate_command_requires_approval(self, validator):
        """Test command validation requiring approval."""
        result = validator.validate_command("custom-tool --complex-operation")

        assert result.result == ValidationResult.REQUIRES_APPROVAL
        assert result.risk_level == "medium"
        assert "requires user approval" in result.explanation.lower()

    def test_is_command_approved_false(self, validator):
        """Test checking approval for unapproved command."""
        assert validator.is_command_approved("test command") is False

    def test_is_command_approved_true(self, validator):
        """Test checking approval for approved command."""
        validator.add_approval("test command")
        assert validator.is_command_approved("test command") is True

    def test_add_approval(self, validator):
        """Test adding command approval."""
        command = "test command"
        assert validator.is_command_approved(command) is False

        validator.add_approval(command)
        assert validator.is_command_approved(command) is True

    def test_remove_approval(self, validator):
        """Test removing command approval."""
        command = "test command"
        validator.add_approval(command)
        assert validator.is_command_approved(command) is True

        validator.remove_approval(command)
        assert validator.is_command_approved(command) is False

    def test_remove_approval_nonexistent(self, validator):
        """Test removing approval for command that wasn't approved."""
        # Should not raise error
        validator.remove_approval("nonexistent command")

    def test_load_patterns(self, validator):
        """Test loading patterns from config."""
        config_path = "/path/to/config.yaml"
        validator.load_patterns(config_path)

        # Verify config path was stored (mock implementation)
        assert validator._config_path == config_path

    def test_approval_with_session_id(self, validator):
        """Test approval operations with session ID."""
        command = "session command"
        session_id = "test-session-123"

        # Test approval with session ID
        validator.add_approval(command, session_id)
        assert validator.is_command_approved(command, session_id) is True

        # Remove approval
        validator.remove_approval(command, session_id)
        assert validator.is_command_approved(command, session_id) is False

    def test_multiple_dangerous_patterns(self, validator):
        """Test validation with multiple dangerous patterns."""
        dangerous_commands = ["sudo rm -rf /", "del /s /q C:\\*", "format c: /q", "rm -rf *"]

        for cmd in dangerous_commands:
            result = validator.validate_command(cmd)
            assert result.result == ValidationResult.DENIED
            assert result.risk_level == "critical"

    def test_multiple_safe_patterns(self, validator):
        """Test validation with multiple safe patterns."""
        safe_commands = ["ls -la", "dir /w", "cat file.txt", "echo hello world"]

        for cmd in safe_commands:
            result = validator.validate_command(cmd)
            assert result.result == ValidationResult.ALLOWED
            assert result.risk_level == "low"


class TestSafetyError:
    """Test SafetyError exception class."""

    def test_safety_error_creation(self):
        """Test creating SafetyError instances."""
        error = SafetyError("Test safety error")

        assert str(error) == "Test safety error"
        assert isinstance(error, Exception)

    def test_safety_error_inheritance(self):
        """Test SafetyError inheritance."""
        error = SafetyError("Test error")

        assert isinstance(error, Exception)
        assert type(error).__name__ == "SafetyError"

    def test_safety_error_raising(self):
        """Test raising SafetyError."""
        with pytest.raises(SafetyError) as exc_info:
            raise SafetyError("Critical safety violation")

        assert "Critical safety violation" in str(exc_info.value)


class TestSafetyValidatorIntegration:
    """Integration tests for safety validator components."""

    def test_end_to_end_validation_workflow(self):
        """Test complete validation workflow."""
        validator = ConcreteSafetyValidator(SafetyMode.CONFIRM)

        # Test dangerous command
        dangerous_cmd = "rm -rf /important"
        result = validator.validate_command(dangerous_cmd)
        assert result.result == ValidationResult.DENIED

        # Test safe command
        safe_cmd = "ls -la"
        result = validator.validate_command(safe_cmd)
        assert result.result == ValidationResult.ALLOWED

        # Test approval workflow
        approval_cmd = "custom-operation"
        result = validator.validate_command(approval_cmd)
        assert result.result == ValidationResult.REQUIRES_APPROVAL

        # Add approval and test again
        validator.add_approval(approval_cmd)
        assert validator.is_command_approved(approval_cmd) is True

        # Change safety mode
        validator.set_safety_mode(SafetyMode.AUTO)
        assert validator.get_safety_mode() == SafetyMode.AUTO
