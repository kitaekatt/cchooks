"""Tests for SubagentStopContext and SubagentStopOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.subagent_stop import SubagentStopContext
from cchooks.exceptions import HookValidationError


class TestSubagentStopContext:
    """Test SubagentStopContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        assert context.hook_event_name == "SubagentStop"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.stop_hook_active is True

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
                SubagentStopContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
            "subagent_name": "code-analyzer",
            "reason": "Task completed",
        }

        context = SubagentStopContext(data)
        assert context.hook_event_name == "SubagentStop"
        assert context.stop_hook_active is True


class TestSubagentStopOutput:
    """Test SubagentStopOutput functionality."""

    def test_exit_success(self):
        """Test simple approve method."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Allow subagent to stop")
            mock_exit.assert_called_once_with(0)

    def test_exit_block(self):
        """Test simple block method."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Prevent subagent from stopping")
            mock_exit.assert_called_once_with(2)

    def test_halt(self):
        """Test stop processing method."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("Subagent completed all tasks")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "Subagent completed all tasks"
            assert "systemMessage" not in result

    def test_halt_with_system_message(self):
        """Test halt method with system message."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt(
                "Subagent completed all tasks",
                suppress_output=False,
                system_message="🤖 Subagent task completion: All objectives achieved",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "Subagent completed all tasks"
            assert (
                result["systemMessage"]
                == "🤖 Subagent task completion: All objectives achieved"
            )

    def test_prevent(self):
        """Test continue block method."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = SubagentStopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent("Subagent has more work to do")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["decision"] == "block"
            assert result["reason"] == "Subagent has more work to do"
            assert "systemMessage" not in result

    def test_prevent_with_system_message(self):
        """Test prevent method with system message."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = SubagentStopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent(
                "Subagent has more work to do",
                suppress_output=False,
                system_message="🔄 Subagent continues: Additional tasks pending",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["decision"] == "block"
            assert result["reason"] == "Subagent has more work to do"
            assert (
                result["systemMessage"]
                == "🔄 Subagent continues: Additional tasks pending"
            )

    def test_allow(self):
        """Test continue direct method."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

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
            "hook_event_name": "SubagentStop",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.allow(
                suppress_output=False,
                system_message="✅ Subagent stop approved: Task completion confirmed",
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert "decision" not in result
            assert (
                result["systemMessage"]
                == "✅ Subagent stop approved: Task completion confirmed"
            )


class TestSubagentStopRealWorldScenarios:
    """Test real-world subagent stopping scenarios."""

    def test_code_analysis_subagent_completion(self):
        """Test code analysis subagent completion."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "analysis-session-123",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        # Allow subagent to complete
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Code analysis completed")
            mock_exit.assert_called_once_with(0)

    def test_test_runner_subagent_completion(self):
        """Test test runner subagent completion."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "test-session-456",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        # Allow subagent to complete
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("All tests executed")
            mock_exit.assert_called_once_with(0)

    def test_prevent_subagent_stop_during_processing(self):
        """Test preventing subagent stop during active processing."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "processing-session-789",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": False,
        }

        context = SubagentStopContext(data)

        # Prevent subagent from stopping
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent("Subagent still processing data")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is True
            assert "processing data" in result["reason"]

    def test_subagent_workflow_management(self):
        """Test subagent workflow management scenarios."""
        workflows = [
            {
                "name": "Code Review",
                "description": "Code review subagent workflow",
                "should_stop": True,
                "reason": "Code review completed",
            },
            {
                "name": "Dependency Analysis",
                "description": "Dependency checking subagent",
                "should_stop": True,
                "reason": "Dependencies analyzed",
            },
            {
                "name": "Security Scan",
                "description": "Security scanning subagent",
                "should_stop": False,
                "reason": "Security scan in progress",
            },
        ]

        for workflow in workflows:
            data = {
                "hook_event_name": "SubagentStop",
                "session_id": f"{workflow['name'].lower()}-session",
                "transcript_path": "/tmp/transcript.json",
                "stop_hook_active": workflow["should_stop"],
            }

            context = SubagentStopContext(data)

            if workflow["should_stop"]:
                with patch("sys.exit") as mock_exit:
                    context.output.exit_success(workflow["reason"])
                    mock_exit.assert_called_once_with(0)
            else:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    context.output.prevent(workflow["reason"])

                    output = mock_stdout.getvalue().strip()
                    result = json.loads(output)
                    assert result["continue"] is True

    def test_subagent_timeout_handling(self):
        """Test subagent timeout handling."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "timeout-session",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        # Test timeout scenario
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("Subagent timed out after 30 minutes")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is False
            assert "timed out" in result["stopReason"]

    def test_subagent_error_recovery(self):
        """Test subagent error recovery scenarios."""
        data = {
            "hook_event_name": "SubagentStop",
            "session_id": "error-session",
            "transcript_path": "/tmp/transcript.json",
            "stop_hook_active": True,
        }

        context = SubagentStopContext(data)

        # Test error recovery
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("Subagent encountered fatal error")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is False
            assert "fatal error" in result["stopReason"]
