"""Tests for SessionStartContext and SessionStartOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.session_start import SessionStartContext, SessionStartOutput
from cchooks.exceptions import HookValidationError


class TestSessionStartContext:
    """Test SessionStartContext functionality."""

    def test_valid_context_creation_startup(self):
        """Test creating context with startup source."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        assert context.hook_event_name == "SessionStart"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.source == "startup"

    def test_valid_context_creation_resume(self):
        """Test creating context with resume source."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-session-456",
            "transcript_path": "/tmp/transcript.json",
            "source": "resume",
        }

        context = SessionStartContext(data)

        assert context.hook_event_name == "SessionStart"
        assert context.session_id == "test-session-456"
        assert context.source == "resume"

    def test_valid_context_creation_clear(self):
        """Test creating context with clear source."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-session-789",
            "transcript_path": "/tmp/transcript.json",
            "source": "clear",
        }

        context = SessionStartContext(data)

        assert context.hook_event_name == "SessionStart"
        assert context.session_id == "test-session-789"
        assert context.source == "clear"

    def test_valid_context_creation_compact(self):
        """Test creating context with compact source."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-session-compact",
            "transcript_path": "/tmp/transcript.json",
            "source": "compact",
        }

        context = SessionStartContext(data)

        assert context.hook_event_name == "SessionStart"
        assert context.session_id == "test-session-compact"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.source == "compact"

    def test_context_properties(self):
        """Test that all context properties are accessible."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "sess_abc123def456",
            "transcript_path": "/Users/user/.claude/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test that output is properly initialized
        assert isinstance(context.output, SessionStartOutput)

    def test_context_with_different_sources(self):
        """Test context creation with different session start sources."""
        sources = ["startup", "resume", "clear", "compact"]

        for source in sources:
            data = {
                "hook_event_name": "SessionStart",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "source": source,
            }

            context = SessionStartContext(data)
            assert context.source == source

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                ["session_id", "transcript_path", "hook_event_name", "source"],
            ),
            (
                {"hook_event_name": "SessionStart"},
                ["session_id", "transcript_path", "source"],
            ),
            (
                {"source": "startup"},
                ["session_id", "transcript_path", "hook_event_name"],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                SessionStartContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields (should be ignored)."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "hook_event_name": "SessionStart",
            "source": "startup",
            "extra_field": "should_be_ignored",
            "another_extra": 123,
        }

        context = SessionStartContext(data)

        # Should successfully create context and ignore extra fields
        assert context.hook_event_name == "SessionStart"
        assert context.source == "startup"

    def test_source_property_type(self):
        """Test that source property returns correct type."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)
        assert isinstance(context.source, str)
        assert context.source == "startup"


class TestSessionStartOutput:
    """Test SessionStartOutput functionality."""

    def test_add_context(self):
        """Test add_context method."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.add_context("Loading project context and recent changes")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "SessionStart"
            assert result["hookSpecificOutput"]["additionalContext"] == "Loading project context and recent changes"
            assert "systemMessage" not in result

    def test_add_context_with_system_message(self):
        """Test add_context method with system message."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.add_context(
                "Loading project context and recent changes",
                suppress_output=False,
                system_message="🚀 Session initialized: Loading project environment"
            )

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "SessionStart"
            assert result["hookSpecificOutput"]["additionalContext"] == "Loading project context and recent changes"
            assert result["systemMessage"] == "🚀 Session initialized: Loading project environment"

    def test_add_context_with_suppress_output(self):
        """Test add_context method with suppress_output=True."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "resume",
        }

        context = SessionStartContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.add_context("Resuming previous session context", suppress_output=True)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["hookSpecificOutput"]["hookEventName"] == "SessionStart"
            assert result["hookSpecificOutput"]["additionalContext"] == "Resuming previous session context"

    def test_exit_success(self):
        """Test exit_success method."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Session context loaded")
            mock_exit.assert_called_once_with(0)

    def test_continue_json_output_no_stop_reason(self):
        """Test that continue=true JSON output doesn't include stopReason field."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.add_context("Test context")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            # When continue=true, stopReason should NOT be included
            assert "stopReason" not in result

    def test_exit_non_block(self):
        """Test exit_non_block method."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_non_block("Non-blocking warning")
            mock_exit.assert_called_once_with(1)

    def test_exit_block(self):
        """Test exit_block method."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Blocking error")
            mock_exit.assert_called_once_with(2)


class TestSessionStartRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_load_project_context_on_startup(self):
        """Test loading project context on startup."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test loading project context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            project_context = """
Current project: Python web application
Recent changes: Added authentication module
Open issues: 3 (2 bugs, 1 feature request)
Last commit: feat: Add JWT authentication
"""
            context.output.add_context(project_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == project_context

    def test_resume_session_context(self):
        """Test resuming session context."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "resume",
        }

        context = SessionStartContext(data)

        # Test resuming with previous context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            resume_context = "Resuming work on user authentication module. Previous task: implementing OAuth2 flow."
            context.output.add_context(resume_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == resume_context

    def test_clear_session_context(self):
        """Test clear session context."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "clear",
        }

        context = SessionStartContext(data)

        # Test providing fresh context after clear
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            fresh_context = "Starting fresh session. Current working directory: /home/user/project"
            context.output.add_context(fresh_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == fresh_context

    def test_load_git_context(self):
        """Test loading git repository context."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test loading git context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            git_context = """
Git repository: my-project
Current branch: main
Recent commits:
- feat: Add user authentication (HEAD)
- fix: Resolve login bug
- docs: Update API documentation
Modified files: src/auth.py, tests/test_auth.py
"""
            context.output.add_context(git_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert "Git repository:" in result["hookSpecificOutput"]["additionalContext"]

    def test_load_development_environment(self):
        """Test loading development environment context."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test loading development environment
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            env_context = """
Development Environment:
- Python 3.12.0
- Virtual environment: venv (active)
- Database: PostgreSQL 14 (local)
- Redis: 6.2 (local)
- Testing: pytest with coverage
"""
            context.output.add_context(env_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert "Development Environment:" in result["hookSpecificOutput"]["additionalContext"]

    def test_error_handling_context_loading(self):
        """Test error handling when context loading fails."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test error handling
        with patch("sys.exit") as mock_exit:
            context.output.exit_non_block("Failed to load git repository context")
            mock_exit.assert_called_once_with(1)

    def test_context_loading_with_suppressed_output(self):
        """Test context loading with suppressed output for cleaner transcript."""
        data = {
            "hook_event_name": "SessionStart",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        context = SessionStartContext(data)

        # Test suppressed output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.add_context("Internal context data", suppress_output=True)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == "Internal context data"
