"""pytest configuration and shared fixtures for cchooks tests."""

import json
from io import StringIO
from typing import Any, Dict
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_stdin():
    """Mock stdin for testing JSON input."""

    def _mock_stdin(data: Dict[str, Any]) -> StringIO:
        return StringIO(json.dumps(data))

    return _mock_stdin


@pytest.fixture
def mock_stdin_context():
    """Context manager for mocking stdin."""

    @patch("sys.stdin", new_callable=StringIO)
    def _mock_context(mock_stdin, data: Dict[str, Any]):
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)
        return mock_stdin

    return _mock_context


@pytest.fixture
def sample_pre_tool_use_data():
    """Sample PreToolUse hook input data."""
    return {
        "hook_event_name": "PreToolUse",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "tool_name": "Write",
        "tool_input": {"file_path": "/tmp/test.txt", "content": "Hello World"},
    }


@pytest.fixture
def sample_post_tool_use_data():
    """Sample PostToolUse hook input data."""
    return {
        "hook_event_name": "PostToolUse",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "tool_name": "Write",
        "tool_input": {"file_path": "/tmp/test.txt", "content": "Hello World"},
        "tool_response": {"success": True, "content": "File written successfully"},
    }


@pytest.fixture
def sample_notification_data():
    """Sample Notification hook input data."""
    return {
        "hook_event_name": "Notification",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "message": "Permission required for file modification",
    }


@pytest.fixture
def sample_stop_data():
    """Sample Stop hook input data."""
    return {
        "hook_event_name": "Stop",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "stop_hook_active": True,
    }


@pytest.fixture
def sample_subagent_stop_data():
    """Sample SubagentStop hook input data."""
    return {
        "hook_event_name": "SubagentStop",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "stop_hook_active": False,
    }


@pytest.fixture
def sample_pre_compact_data():
    """Sample PreCompact hook input data."""
    return {
        "hook_event_name": "PreCompact",
        "session_id": "test-session-123",
        "transcript_path": "/tmp/transcript.json",
        "trigger": "manual",
        "custom_instructions": "Preserve important decisions",
    }


@pytest.fixture
def capture_stdout():
    """Capture stdout for testing output."""

    def _capture():
        return patch("sys.stdout", new_callable=StringIO)

    return _capture


@pytest.fixture
def capture_stderr():
    """Capture stderr for testing error output."""

    def _capture():
        return patch("sys.stderr", new_callable=StringIO)

    return _capture
