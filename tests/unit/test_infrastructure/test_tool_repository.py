"""Tests for tool repository infrastructure."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mentat.infrastructure.fs_tool_repository import FsToolRepository
from mentat.infrastructure.repositories import ToolSpec, _load_tool_toml


class TestToolSpec:
    """Test ToolSpec data class."""

    def test_tool_spec_creation(self):
        """Test creating ToolSpec instances."""
        spec = ToolSpec(name="test_tool", description="A test tool", command="echo hello")

        assert spec.name == "test_tool"
        assert spec.description == "A test tool"
        assert spec.command == "echo hello"

    def test_tool_spec_slots(self):
        """Test ToolSpec uses slots for memory efficiency."""
        spec = ToolSpec("test", "desc", "cmd")
        assert hasattr(spec, "__slots__")


class TestLoadToolToml:
    """Test _load_tool_toml function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_load_valid_tool_toml(self, temp_dir):
        """Test loading valid TOML tool configuration."""
        tool_file = temp_dir / "valid_tool.toml"
        tool_file.write_text("""
name = "test_tool"
description = "A test tool for testing"
command = "python -c 'print(hello)'"
""")

        spec = _load_tool_toml(tool_file)

        assert spec is not None
        assert spec.name == "test_tool"
        assert spec.description == "A test tool for testing"
        assert spec.command == "python -c 'print(hello)'"

    def test_load_minimal_tool_toml(self, temp_dir):
        """Test loading TOML with minimal required fields."""
        tool_file = temp_dir / "minimal_tool.toml"
        tool_file.write_text("""
name = "minimal"
command = "echo test"
""")

        spec = _load_tool_toml(tool_file)

        assert spec is not None
        assert spec.name == "minimal"
        assert spec.description == ""  # Default empty description
        assert spec.command == "echo test"

    def test_load_tool_toml_missing_name(self, temp_dir):
        """Test loading TOML missing required name field."""
        tool_file = temp_dir / "no_name.toml"
        tool_file.write_text("""
description = "Tool without name"
command = "echo test"
""")

        spec = _load_tool_toml(tool_file)
        assert spec is None

    def test_load_tool_toml_missing_command(self, temp_dir):
        """Test loading TOML missing required command field."""
        tool_file = temp_dir / "no_command.toml"
        tool_file.write_text("""
name = "no_command_tool"
description = "Tool without command"
""")

        spec = _load_tool_toml(tool_file)
        assert spec is None

    def test_load_tool_toml_invalid_syntax(self, temp_dir):
        """Test loading TOML with invalid syntax."""
        tool_file = temp_dir / "invalid.toml"
        tool_file.write_text("""
name = "invalid
description = "Missing quote"
command = "echo test"
""")

        spec = _load_tool_toml(tool_file)
        assert spec is None

    def test_load_tool_toml_nonexistent_file(self):
        """Test loading nonexistent TOML file."""
        nonexistent = Path("/does/not/exist.toml")

        spec = _load_tool_toml(nonexistent)
        assert spec is None

    def test_load_tool_toml_permission_error(self, temp_dir):
        """Test loading TOML file with permission issues."""
        tool_file = temp_dir / "permission_test.toml"
        tool_file.write_text("""
name = "permission_tool"
command = "echo test"
""")

        # Mock permission error
        with patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied")):
            spec = _load_tool_toml(tool_file)
            assert spec is None


class TestFsToolRepository:
    """Test filesystem-based tool repository."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def tools_dir(self, temp_dir):
        """Create tools directory with sample tools."""
        tools_dir = temp_dir / "tools"
        tools_dir.mkdir()

        # Create sample tools
        (tools_dir / "echo_tool.toml").write_text("""
name = "echo_tool"
description = "Simple echo tool"
command = "echo"
""")

        (tools_dir / "python_tool.toml").write_text("""
name = "python_tool"
description = "Python script runner"
command = "python -c"
""")

        return tools_dir

    @pytest.fixture
    def repository(self, tools_dir):
        """Create FsToolRepository instance."""
        return FsToolRepository(tools_dir)

    def test_repository_initialization(self, temp_dir):
        """Test repository initialization."""
        repo = FsToolRepository(temp_dir)
        assert repo.tools_dir == temp_dir

    def test_iter_tool_files_valid_directory(self, repository, tools_dir):
        """Test iterating tool files in valid directory."""
        files = list(repository._iter_tool_files())

        # Should find both TOML files, sorted
        assert len(files) == 2
        assert files[0].name == "echo_tool.toml"
        assert files[1].name == "python_tool.toml"

    def test_iter_tool_files_nonexistent_directory(self, temp_dir):
        """Test iterating tool files in nonexistent directory."""
        nonexistent_dir = temp_dir / "nonexistent"
        repo = FsToolRepository(nonexistent_dir)

        files = list(repo._iter_tool_files())
        assert files == []

    def test_iter_tool_files_not_directory(self, temp_dir):
        """Test iterating tool files when path is not a directory."""
        # Create a file instead of directory
        not_dir = temp_dir / "not_a_dir.txt"
        not_dir.write_text("not a directory")

        repo = FsToolRepository(not_dir)
        files = list(repo._iter_tool_files())
        assert files == []

    def test_list_tools(self, repository):
        """Test listing all tools."""
        tools = list(repository.list_tools())

        assert len(tools) == 2
        tool_names = {tool.name for tool in tools}
        assert "echo_tool" in tool_names
        assert "python_tool" in tool_names

    def test_list_tools_empty_directory(self, temp_dir):
        """Test listing tools in empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        repo = FsToolRepository(empty_dir)
        tools = list(repo.list_tools())
        assert tools == []

    def test_list_tools_with_invalid_files(self, temp_dir):
        """Test listing tools with some invalid TOML files."""
        tools_dir = temp_dir / "mixed_tools"
        tools_dir.mkdir()

        # Valid tool
        (tools_dir / "valid.toml").write_text("""
name = "valid_tool"
command = "echo valid"
""")

        # Invalid tool (missing name)
        (tools_dir / "invalid.toml").write_text("""
description = "Invalid tool"
command = "echo invalid"
""")

        # Corrupted TOML
        (tools_dir / "corrupted.toml").write_text("""
name = "corrupted
command = echo corrupted"
""")

        repo = FsToolRepository(tools_dir)
        tools = list(repo.list_tools())

        # Should only return valid tools
        assert len(tools) == 1
        assert tools[0].name == "valid_tool"

    def test_get_tool_existing(self, repository):
        """Test getting existing tool by name."""
        tool = repository.get_tool("echo_tool")

        assert tool is not None
        assert tool.name == "echo_tool"
        assert tool.description == "Simple echo tool"
        assert tool.command == "echo"

    def test_get_tool_nonexistent(self, repository):
        """Test getting nonexistent tool."""
        tool = repository.get_tool("nonexistent_tool")
        assert tool is None

    def test_get_tool_case_sensitive(self, repository):
        """Test that tool names are case sensitive."""
        tool = repository.get_tool("ECHO_TOOL")  # Different case
        assert tool is None

    @patch("subprocess.run")
    def test_run_tool_success(self, mock_run, repository):
        """Test running existing tool successfully."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        exit_code = repository.run_tool("echo_tool", ["hello", "world"])

        assert exit_code == 0
        mock_run.assert_called_once_with(["echo", "hello", "world"])

    @patch("subprocess.run")
    def test_run_tool_with_error(self, mock_run, repository):
        """Test running tool that returns error code."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        exit_code = repository.run_tool("echo_tool", ["hello"])

        assert exit_code == 1
        mock_run.assert_called_once_with(["echo", "hello"])

    def test_run_tool_nonexistent(self, repository):
        """Test running nonexistent tool."""
        exit_code = repository.run_tool("nonexistent_tool", [])
        assert exit_code == 2  # Not found error code

    @patch("subprocess.run")
    def test_run_tool_complex_command(self, mock_run, temp_dir):
        """Test running tool with complex command that needs shell parsing."""
        tools_dir = temp_dir / "tools"
        tools_dir.mkdir()

        # Tool with complex command
        (tools_dir / "complex.toml").write_text("""
name = "complex_tool"
command = "python -c 'import sys; print(sys.argv)'"
""")

        repo = FsToolRepository(tools_dir)

        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        exit_code = repo.run_tool("complex_tool", ["arg1", "arg2"])

        assert exit_code == 0
        # Should properly parse the command using shlex
        expected_cmd = ["python", "-c", "import sys; print(sys.argv)", "arg1", "arg2"]
        mock_run.assert_called_once_with(expected_cmd)

    @patch("subprocess.run")
    def test_run_tool_no_args(self, mock_run, repository):
        """Test running tool with no arguments."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        exit_code = repository.run_tool("echo_tool", [])

        assert exit_code == 0
        mock_run.assert_called_once_with(["echo"])

    def test_repository_with_nested_toml_files(self, temp_dir):
        """Test that repository doesn't find TOML files in subdirectories."""
        tools_dir = temp_dir / "tools"
        tools_dir.mkdir()

        # Top-level tool (should be found)
        (tools_dir / "top_level.toml").write_text("""
name = "top_level"
command = "echo top"
""")

        # Nested tool (should not be found)
        nested_dir = tools_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested_tool.toml").write_text("""
name = "nested_tool"
command = "echo nested"
""")

        repo = FsToolRepository(tools_dir)
        tools = list(repo.list_tools())

        # Should only find top-level tool
        assert len(tools) == 1
        assert tools[0].name == "top_level"

    def test_repository_ignores_non_toml_files(self, temp_dir):
        """Test that repository ignores non-TOML files."""
        tools_dir = temp_dir / "tools"
        tools_dir.mkdir()

        # Valid TOML file
        (tools_dir / "valid.toml").write_text("""
name = "valid"
command = "echo valid"
""")

        # Non-TOML files (should be ignored)
        (tools_dir / "readme.txt").write_text("This is not a tool")
        (tools_dir / "config.json").write_text('{"not": "toml"}')
        (tools_dir / "script.py").write_text("print('not toml')")

        repo = FsToolRepository(tools_dir)
        tools = list(repo.list_tools())

        # Should only find TOML file
        assert len(tools) == 1
        assert tools[0].name == "valid"


class TestToolRepositoryIntegration:
    """Integration tests for tool repository functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_full_tool_lifecycle(self, temp_dir):
        """Test complete tool lifecycle: create, list, get, run."""
        tools_dir = temp_dir / "tools"
        tools_dir.mkdir()

        # Create a real tool that we can actually run
        tool_file = tools_dir / "test_tool.toml"
        tool_file.write_text("""
name = "test_tool"
description = "A tool for testing"
command = "python -c 'print(\\"Tool executed successfully\\")'"
""")

        repo = FsToolRepository(tools_dir)

        # Test listing
        tools = list(repo.list_tools())
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

        # Test getting
        tool = repo.get_tool("test_tool")
        assert tool is not None
        assert tool.description == "A tool for testing"

        # Test running (with subprocess mock to avoid actual execution)
        with patch("subprocess.run") as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            exit_code = repo.run_tool("test_tool", [])
            assert exit_code == 0
