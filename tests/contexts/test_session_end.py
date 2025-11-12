"""Tests for SessionEnd hook context and output classes."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cchooks.contexts.session_end import SessionEndContext, SessionEndOutput
from cchooks.exceptions import HookValidationError
from cchooks.types import SessionEndReason

from ..fixtures.sample_data import (
    SAMPLE_SESSION_END_CLEAR,
    SAMPLE_SESSION_END_LOGOUT,
    SAMPLE_SESSION_END_PROMPT_INPUT_EXIT,
    SAMPLE_SESSION_END_OTHER,
    INVALID_SESSION_END_MISSING_REASON,
    INVALID_SESSION_END_INVALID_REASON,
    INVALID_SESSION_END_MISSING_CWD,
)


class TestSessionEndContext:
    """Test SessionEndContext class."""

    def test_valid_context_creation_clear(self):
        """Test SessionEnd context creation with 'clear' reason."""
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        assert context.reason == "clear"
        assert context.cwd == "/Users/user/project"
        assert isinstance(context.output, SessionEndOutput)

    def test_valid_context_creation_logout(self):
        """Test SessionEnd context creation with 'logout' reason."""
        context = SessionEndContext(SAMPLE_SESSION_END_LOGOUT)
        assert context.reason == "logout"
        assert isinstance(context.output, SessionEndOutput)

    def test_valid_context_creation_prompt_input_exit(self):
        """Test SessionEnd context creation with 'prompt_input_exit' reason."""
        context = SessionEndContext(SAMPLE_SESSION_END_PROMPT_INPUT_EXIT)
        assert context.reason == "prompt_input_exit"
        assert isinstance(context.output, SessionEndOutput)

    def test_valid_context_creation_other(self):
        """Test SessionEnd context creation with 'other' reason."""
        context = SessionEndContext(SAMPLE_SESSION_END_OTHER)
        assert context.reason == "other"
        assert isinstance(context.output, SessionEndOutput)

    def test_missing_reason_field(self):
        """Test validation error when reason field is missing."""
        with pytest.raises(HookValidationError, match="Missing required SessionEnd fields: reason"):
            SessionEndContext(INVALID_SESSION_END_MISSING_REASON)

    def test_missing_cwd_field(self):
        """Test validation error when cwd field is missing."""
        with pytest.raises(HookValidationError, match="Missing required SessionEnd fields: cwd"):
            SessionEndContext(INVALID_SESSION_END_MISSING_CWD)

    def test_invalid_reason_field(self):
        """Test that invalid reason values are accepted (validation happens at type level)."""
        # The context accepts any string value for reason, type validation happens elsewhere
        context = SessionEndContext(INVALID_SESSION_END_INVALID_REASON)
        assert context.reason == "invalid_reason"

    def test_reason_property_returns_correct_type(self):
        """Test that reason property returns SessionEndReason type."""
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        reason = context.reason
        assert isinstance(reason, str)
        assert reason in ["clear", "logout", "prompt_input_exit", "other"]

    def test_cwd_property_returns_correct_value(self):
        """Test that cwd property returns the correct working directory."""
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        assert context.cwd == "/Users/user/project"
        assert isinstance(context.cwd, str)

    def test_cwd_property_with_different_reasons(self):
        """Test cwd property works with different session end reasons."""
        samples = [
            SAMPLE_SESSION_END_CLEAR,
            SAMPLE_SESSION_END_LOGOUT,
            SAMPLE_SESSION_END_PROMPT_INPUT_EXIT,
            SAMPLE_SESSION_END_OTHER,
        ]

        for sample_data in samples:
            context = SessionEndContext(sample_data)
            assert context.cwd == "/Users/user/project"

    def test_all_reason_types(self):
        """Test all valid SessionEnd reason types."""
        reasons: list[SessionEndReason] = ["clear", "logout", "prompt_input_exit", "other"]
        for reason in reasons:
            input_data = SAMPLE_SESSION_END_CLEAR.copy()
            input_data["reason"] = reason
            context = SessionEndContext(input_data)
            assert context.reason == reason

    def test_output_handler_type(self):
        """Test that output handler is correct type."""
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        assert isinstance(context.output, SessionEndOutput)

    def test_base_fields_inherited(self):
        """Test that base context fields are properly inherited."""
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        assert context.session_id == "sess_abc123def456"
        assert context.transcript_path == "/Users/user/.claude/transcript_20240716_143022.json"
        assert context.hook_event_name == "SessionEnd"


class TestSessionEndOutput:
    """Test SessionEndOutput class."""

    @patch("sys.stderr", new_callable=MagicMock)
    def test_exit_success_no_message(self, mock_stderr):
        """Test successful exit with no message."""
        output = SessionEndOutput()
        with pytest.raises(SystemExit) as exc_info:
            output.exit_success()
        assert exc_info.value.code == 0
        # SessionEnd success should not output to stderr
        mock_stderr.assert_not_called()

    @patch("sys.stderr", new_callable=MagicMock)
    def test_exit_success_with_message(self, mock_stderr):
        """Test successful exit with message."""
        output = SessionEndOutput()
        with pytest.raises(SystemExit) as exc_info:
            output.exit_success("Cleanup completed successfully")
        assert exc_info.value.code == 0
        # SessionEnd success should not output to stderr
        mock_stderr.assert_not_called()

    @patch("sys.stderr", new_callable=MagicMock)
    def test_exit_non_block(self, mock_stderr):
        """Test non-blocking error exit."""
        output = SessionEndOutput()
        with pytest.raises(SystemExit) as exc_info:
            output.exit_non_block("Cleanup failed")
        assert exc_info.value.code == 1
        # Check that stderr was written to (using write calls)
        mock_stderr.write.assert_any_call("Cleanup failed")

    @patch("sys.stderr", new_callable=MagicMock)
    def test_exit_block(self, mock_stderr):
        """Test blocking error exit (should behave like non_block for SessionEnd)."""
        output = SessionEndOutput()
        with pytest.raises(SystemExit) as exc_info:
            output.exit_block("Cleanup blocked")
        assert exc_info.value.code == 2
        # Check that stderr was written to (using write calls)
        mock_stderr.write.assert_any_call("Cleanup blocked")

    def test_json_output_with_system_message(self):
        """Test JSON output format when using system message."""
        output = SessionEndOutput()
        result = output._continue_flow(system_message="Warning: cleanup incomplete")

        assert result["continue"] is True
        assert result["systemMessage"] == "Warning: cleanup incomplete"

    def test_json_output_without_system_message(self):
        """Test JSON output format without system message."""
        output = SessionEndOutput()
        result = output._continue_flow()

        assert result["continue"] is True
        # systemMessage should be absent when not provided
        assert "systemMessage" not in result

    def test_json_output_with_suppress_output(self):
        """Test JSON output format with suppress output."""
        output = SessionEndOutput()
        result = output._continue_flow(suppress_output=True)

        assert result["continue"] is True
        assert result["suppressOutput"] is True

    def test_stop_flow_json_output(self):
        """Test stop flow JSON output format."""
        output = SessionEndOutput()
        result = output._stop_flow("Session ended due to error")

        assert result["continue"] is False
        assert result["stopReason"] == "Session ended due to error"

    def test_stop_flow_with_system_message(self):
        """Test stop flow JSON output with system message."""
        output = SessionEndOutput()
        result = output._stop_flow("Session ended due to error", system_message="Warning: data loss possible")

        assert result["continue"] is False
        assert result["stopReason"] == "Session ended due to error"
        assert result["systemMessage"] == "Warning: data loss possible"


class TestSessionEndIntegration:
    """Test SessionEnd integration scenarios."""

    def test_factory_function_integration(self):
        """Test SessionEnd context creation via factory function."""
        from cchooks import create_context
        from io import StringIO

        test_input = StringIO(json.dumps(SAMPLE_SESSION_END_CLEAR))
        context = create_context(test_input)

        assert isinstance(context, SessionEndContext)
        assert context.reason == "clear"
        assert isinstance(context.output, SessionEndOutput)

    def test_session_end_cannot_block_termination(self):
        """Test that SessionEnd hooks cannot block session termination."""
        # This is more of a behavioral test - SessionEnd hooks run after the
        # decision to end the session has been made, so they cannot block it
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)

        # All exit methods should be available but none can actually block
        # the session termination since it's already in progress
        assert hasattr(context.output, "exit_success")
        assert hasattr(context.output, "exit_non_block")
        assert hasattr(context.output, "exit_block")

    @pytest.mark.parametrize("reason", ["clear", "logout", "prompt_input_exit", "other"])
    def test_all_reason_types_parameterized(self, reason):
        """Test all SessionEnd reason types using parameterized test."""
        input_data = SAMPLE_SESSION_END_CLEAR.copy()
        input_data["reason"] = reason
        context = SessionEndContext(input_data)
        assert context.reason == reason

    def test_session_end_use_case_cleanup(self):
        """Test typical SessionEnd cleanup use case."""
        """This would be a typical SessionEnd hook implementation:

        def cleanup_hook():
            context = create_context()
            if isinstance(context, SessionEndContext):
                try:
                    # Perform cleanup tasks
                    save_session_state(context.session_id)
                    cleanup_temp_files()
                    context.output.exit_success("Cleanup completed")
                except Exception as e:
                    context.output.exit_non_block(f"Cleanup failed: {e}")
        """
        # Test that the context provides all needed information for cleanup
        context = SessionEndContext(SAMPLE_SESSION_END_CLEAR)
        assert context.session_id
        assert context.transcript_path
        assert context.reason
        assert hasattr(context.output, "exit_success")
        assert hasattr(context.output, "exit_non_block")
