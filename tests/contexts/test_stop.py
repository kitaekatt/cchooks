"""Tests for StopContext and StopOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.stop import StopContext
from cchooks.exceptions import HookValidationError


class TestStopContext:
    """Test StopContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        assert context.hook_event_name == "Stop"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.stop_hook_active is True

    def test_context_with_stop_hook_inactive(self):
        """Test creating context with stop_hook_active=False."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)
        assert context.stop_hook_active is False

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "stop_hook_active",
                ],
            ),
            (
                {"hook_event_name": "PostToolUse"},
                [
                    "session_id",
                    "transcript_path",
                    "stop_hook_active",
                ],
            ),
            (
                {"stop_hook_active": "manual"},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                ],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                StopContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
            "extra_field": "should_be_ignored",
            "reason": "User requested stop",
        }

        context = StopContext(data)

        # Should successfully create context
        assert context.hook_event_name == "Stop"
        assert context.stop_hook_active is True


class TestStopOutput:
    """Test StopOutput functionality."""

    def test_exit_success_with_stop_hook_active(self):
        """Test simple approve when stop hook is active."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Allow Claude to stop")
            mock_exit.assert_called_once_with(0)

    def test_exit_success_with_stop_hook_inactive(self):
        """Test simple approve when stop hook is inactive."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Allow stop (hook inactive)")
            mock_exit.assert_called_once_with(0)

    def test_exit_block(self):
        """Test simple block method."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Prevent Claude from stopping")
            mock_exit.assert_called_once_with(2)

    def test_halt(self):
        """Test stop processing method."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("User requested stop")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "User requested stop"
            assert "systemMessage" not in result

    def test_halt_with_system_message(self):
        """Test halt method with system message."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt(
                "User requested stop",
                suppress_output=False,
                system_message="⏹️ User initiated stop sequence",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "User requested stop"
            assert result["systemMessage"] == "⏹️ User initiated stop sequence"

    def test_prevent(self):
        """Test continue block method."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent("More tasks to complete")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["decision"] == "block"
            assert result["reason"] == "More tasks to complete"
            assert "systemMessage" not in result

    def test_prevent_with_system_message(self):
        """Test prevent method with system message."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent(
                "More tasks to complete",
                suppress_output=False,
                system_message="🚫 Stop prevented: Additional tasks remaining",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["decision"] == "block"
            assert result["reason"] == "More tasks to complete"
            assert (
                result["systemMessage"]
                == "🚫 Stop prevented: Additional tasks remaining"
            )

    def test_allow(self):
        """Test continue direct method."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow()

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert "decision" not in result
            assert "systemMessage" not in result

    def test_allow_with_system_message(self):
        """Test allow method with system message."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow(
                suppress_output=False, system_message="✅ Stop request approved by hook"
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert "decision" not in result
            assert result["systemMessage"] == "✅ Stop request approved by hook"


class TestStopRealWorldScenarios:
    """Test real-world stopping scenarios."""

    def test_user_initiated_stop(self):
        """Test user-initiated stop request."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "user-session-123",
            "transcript_path": "/home/user/.claude/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        # Test allowing stop
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("User requested stop")
            mock_exit.assert_called_once_with(0)

    def test_task_completion_stop(self):
        """Test stop after task completion."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "task-session-456",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = StopContext(data)

        # Test allowing stop after completion
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("All tasks completed")
            mock_exit.assert_called_once_with(0)

    def test_prevent_stop_with_pending_tasks(self):
        """Test preventing stop when tasks are pending."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "pending-session-789",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)

        # Test preventing stop
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent("Pending tasks not completed")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is True
            assert "Pending tasks" in result["reason"]

    def test_conditional_stop_based_on_context(self):
        """Test conditional stop based on conversation context."""
        scenarios = [
            {
                "description": "Allow stop after successful deployment",
                "data": {
                    "hook_event_name": "Stop",
                    "session_id": "deploy-session",
                    "transcript_path": "/tmp/transcript.json",
                    "stop_hook_active": True,
                },
                "should_stop": True,
                "reason": "Deployment completed successfully",
            },
            {
                "description": "Prevent stop during critical operation",
                "data": {
                    "hook_event_name": "Stop",
                    "session_id": "critical-session",
                    "transcript_path": "/tmp/transcript.json",
                    "stop_hook_active": False,
                },
                "should_stop": False,
                "reason": "Critical operation in progress",
            },
        ]

        for scenario in scenarios:
            context = StopContext(scenario["data"])

            if scenario["should_stop"]:
                with patch("sys.exit") as mock_exit:
                    context.output.exit_success(scenario["reason"])
                    mock_exit.assert_called_once_with(0)
            else:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    context.output.prevent(scenario["reason"])

                    output = mock_stdout.getvalue().strip()
                    result = json.loads(output)
                    assert result["continue"] is True

    def test_stop_hook_inactive_scenarios(self):
        """Test behavior when stop hook is inactive."""
        data = {
            "hook_event_name": "Stop",
            "session_id": "inactive-session",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = StopContext(data)

        # When hook is inactive, should allow stopping by default
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Stop hook inactive, allowing stop")
            mock_exit.assert_called_once_with(0)

    def test_json_mode_stop_decisions(self):
        """Test JSON mode stop decisions."""
        scenarios = [
            {
                "stop_hook_active": True,
                "decision": "stop",
                "method": "halt",
                "reason": "User completed all tasks",
            },
            {
                "stop_hook_active": True,
                "decision": "continue",
                "method": "allow",
                "reason": "Continue processing",
            },
            {
                "stop_hook_active": False,
                "decision": "block",
                "method": "prevent",
                "reason": "Prevent stopping for more work",
            },
        ]

        for scenario in scenarios:
            data = {
                "hook_event_name": "Stop",
                "session_id": "json-session",
                "transcript_path": "/tmp/transcript.json",
                "stop_hook_active": scenario["stop_hook_active"],
            }

            context = StopContext(data)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                method = getattr(context.output, scenario["method"])
                method(scenario["reason"])

                output = mock_stdout.getvalue().strip()
                result = json.loads(output)

                if scenario["decision"] == "stop":
                    assert result["continue"] is False
                else:
                    assert result["continue"] is True
