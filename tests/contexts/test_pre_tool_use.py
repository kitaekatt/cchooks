"""Tests for PreToolUseContext and PreToolUseOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.pre_tool_use import PreToolUseContext, PreToolUseOutput
from cchooks.exceptions import HookValidationError


class TestPreToolUseContext:
    """Test PreToolUseContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "PreToolUse",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "Hello World"},
        }

        context = PreToolUseContext(data)

        assert context.hook_event_name == "PreToolUse"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.tool_name == "Write"
        assert context.tool_input == {
            "file_path": "/tmp/test.txt",
            "content": "Hello World",
        }

    def test_context_properties(self):
        """Test that all context properties are accessible."""
        data = {
            "hook_event_name": "PreToolUse",
            "session_id": "sess_abc123def456",
            "transcript_path": "/Users/user/.claude/transcript.json",
            "cwd": "/Users/user/project",
            "tool_name": "Bash",
            "tool_input": {
                "command": "ls -la",
                "description": "List directory contents",
            },
        }

        context = PreToolUseContext(data)

        # Test that output is properly initialized
        assert isinstance(context.output, PreToolUseOutput)

    def test_context_with_different_tools(self):
        """Test context creation with different tool types."""
        tools_and_inputs = [
            ("Write", {"file_path": "/tmp/test.py", "content": "print('hello')"}),
            ("Bash", {"command": "ls -la", "description": "List files"}),
            ("Read", {"file_path": "/tmp/config.json"}),
            (
                "Edit",
                {"file_path": "/tmp/main.py", "old_text": "old", "new_text": "new"},
            ),
            ("Glob", {"pattern": "**/*.py"}),
        ]

        for tool_name, tool_input in tools_and_inputs:
            data = {
                "hook_event_name": "PreToolUse",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/tmp",
                "tool_name": tool_name,
                "tool_input": tool_input,
            }

            context = PreToolUseContext(data)
            assert context.tool_name == tool_name
            assert context.tool_input == tool_input

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_name",
                    "tool_input",
                ],
            ),
            (
                {"hook_event_name": "PostToolUse"},
                [
                    "session_id",
                    "transcript_path",
                    "tool_name",
                    "tool_input",
                ],
            ),
            (
                {"tool_name": "Write"},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_input",
                ],
            ),
            (
                {"tool_input": {}},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_name",
                ],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                PreToolUseContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields (should be ignored)."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt"},
            "extra_field": "should_be_ignored",
            "another_extra": 123,
        }

        context = PreToolUseContext(data)

        # Should successfully create context and ignore extra fields
        assert context.hook_event_name == "PreToolUse"
        assert context.tool_name == "Write"
        assert context.tool_input == {"file_path": "/tmp/test.txt"}


class TestPreToolUseOutput:
    """Test PreToolUseOutput functionality."""

    def test_exit_success(self):
        """Test exit success method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/safe.txt", "content": "safe content"},
        }

        context = PreToolUseContext(data)

        # Mock sys.exit to prevent actual exit
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Approved for safe file")
            mock_exit.assert_called_once_with(0)

    def test_exit_block(self):
        """Test exit block method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/etc/passwd", "content": "malicious content"},
        }

        context = PreToolUseContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Blocking write to system file")
            mock_exit.assert_called_once_with(2)

    def test_allow(self):
        """Test allow method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/safe.txt"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow("Safe read operation approved")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Safe read operation approved"
            )
            assert "systemMessage" not in result

    def test_allow_with_system_message(self):
        """Test allow method with system message."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/safe.txt"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow(
                "Safe read operation approved",
                suppress_output=False,
                system_message="This operation will read a file",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Safe read operation approved"
            )
            assert result["systemMessage"] == "This operation will read a file"

    def test_deny(self):
        """Test deny method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/test"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.deny("Potentially dangerous command blocked")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Potentially dangerous command blocked"
            )
            assert "systemMessage" not in result

    def test_deny_with_system_message(self):
        """Test deny method with system message."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/test"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.deny(
                "Potentially dangerous command blocked",
                suppress_output=False,
                system_message="⚠️ This command could delete files",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Potentially dangerous command blocked"
            )
            assert result["systemMessage"] == "⚠️ This command could delete files"

    def test_halt(self):
        """Test halt method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/etc/shadow", "content": "root password"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("Security violation detected")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "Security violation detected"
            assert "systemMessage" not in result

    def test_halt_with_system_message(self):
        """Test halt method with system message."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/etc/shadow", "content": "root password"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt(
                "Security violation detected",
                suppress_output=False,
                system_message="🚨 Critical security alert: Attempted to write to system file",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "Security violation detected"
            assert (
                result["systemMessage"]
                == "🚨 Critical security alert: Attempted to write to system file"
            )

    def test_ask(self):
        """Test ask method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/log.txt"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.ask("Please confirm this read operation")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "ask"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Please confirm this read operation"
            )
            assert "systemMessage" not in result

    def test_ask_with_system_message(self):
        """Test ask method with system message."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/log.txt"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.ask(
                "Please confirm this read operation",
                suppress_output=False,
                system_message="ℹ️ This operation requires user confirmation",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "ask"
            assert (
                result["hookSpecificOutput"]["permissionDecisionReason"]
                == "Please confirm this read operation"
            )
            assert (
                result["systemMessage"] == "ℹ️ This operation requires user confirmation"
            )


class TestPreToolUseRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_block_sensitive_file_write(self):
        """Test blocking write to sensitive files."""
        sensitive_files = ["/etc/passwd", "/etc/shadow", "/etc/hosts", "~/.ssh/id_rsa"]

        for file_path in sensitive_files:
            data = {
                "hook_event_name": "PreToolUse",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "tool_name": "Write",
                "tool_input": {"file_path": file_path, "content": "malicious"},
            }

            context = PreToolUseContext(data)

            # Test blocking decision
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                context.output.deny(f"Blocking write to sensitive file: {file_path}")

                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_approve_safe_operations(self):
        """Test approving safe operations."""
        safe_operations = [
            ("Read", {"file_path": "/tmp/README.md"}),
            ("Write", {"file_path": "/tmp/test.txt", "content": "test"}),
            ("Bash", {"command": "pwd"}),
            ("Glob", {"pattern": "*.py"}),
        ]

        for tool_name, tool_input in safe_operations:
            data = {
                "hook_event_name": "PreToolUse",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/tmp",
                "tool_name": tool_name,
                "tool_input": tool_input,
            }

            context = PreToolUseContext(data)

            # Test approval
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                context.output.allow("Safe operation approved")

                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_conditional_approval_based_on_content(self):
        """Test conditional approval based on file content patterns."""
        dangerous_patterns = [
            "rm -rf /",
            "del /q /f C:\\Windows\\System32\\",
            "sudo rm -rf /",
            "format C: /q",
        ]

        for dangerous_command in dangerous_patterns:
            data = {
                "hook_event_name": "PreToolUse",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "tool_name": "Bash",
                "tool_input": {"command": dangerous_command},
            }

            context = PreToolUseContext(data)

            # Test blocking dangerous commands
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                context.output.deny("Dangerous command detected")

                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert result["continue"] is True
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert (
                    "Dangerous command detected"
                    in result["hookSpecificOutput"]["permissionDecisionReason"]
                )

    def test_allow_with_updated_input(self):
        """Test allow with updated input parameters."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "original content"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            updated_input = {
                "file_path": "/tmp/safer.txt",
                "content": "modified content",
            }
            context.output.allow(
                "File path updated for safety", updated_input=updated_input
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
            assert result["hookSpecificOutput"]["updatedInput"] == updated_input

    def test_deny_with_updated_input(self):
        """Test deny with updated input parameters."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /", "description": "Dangerous command"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            updated_input = {
                "command": "rm -rf /tmp/test",
                "description": "Safer command",
            }
            context.output.deny(
                "Command modified for safety", updated_input=updated_input
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert result["hookSpecificOutput"]["updatedInput"] == updated_input

    def test_ask_with_updated_input(self):
        """Test ask with updated input parameters."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/etc/config.txt",
                "content": "sensitive config",
            },
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            updated_input = {
                "file_path": "/tmp/config.txt",
                "content": "sensitive config",
            }
            context.output.ask(
                "Please confirm this sensitive operation", updated_input=updated_input
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "ask"
            assert result["hookSpecificOutput"]["updatedInput"] == updated_input

    def test_allow_without_updated_input(self):
        """Test allow without updated input (backward compatibility)."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "content"},
        }

        context = PreToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow("Safe operation approved")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
            assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
            assert "updatedInput" not in result["hookSpecificOutput"]
