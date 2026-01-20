"""Tests for hook error log reading functions."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from cchooks.output_utils import (
    get_hook_errors,
    format_errors_for_display,
    clear_hook_errors,
    _HOOK_ERROR_LOG,
    _LOG_ENTRY_PATTERN,
)


class TestLogEntryPattern:
    """Test the regex pattern for parsing log entries."""

    def test_matches_basic_entry(self):
        """Pattern should match basic log entry format."""
        line = "[2025-01-19T12:00:00] my-hook (PreToolUse): Error message"
        match = _LOG_ENTRY_PATTERN.match(line)
        assert match is not None
        assert match.group(1) == "2025-01-19T12:00:00"
        assert match.group(2) == "my-hook"
        assert match.group(3) == "PreToolUse"
        assert match.group(4) == "Error message"

    def test_matches_entry_with_microseconds(self):
        """Pattern should match timestamps with microseconds."""
        line = "[2025-01-19T12:00:00.123456] hook-name (parse_error): JSON parse failed"
        match = _LOG_ENTRY_PATTERN.match(line)
        assert match is not None
        assert match.group(1) == "2025-01-19T12:00:00.123456"

    def test_does_not_match_traceback_line(self):
        """Pattern should not match traceback lines."""
        line = "Traceback (most recent call last):"
        match = _LOG_ENTRY_PATTERN.match(line)
        assert match is None


class TestGetHookErrors:
    """Test get_hook_errors function."""

    @pytest.fixture
    def mock_log_file(self, tmp_path):
        """Create a temporary log file."""
        log_file = tmp_path / "hook-errors.log"
        with patch("cchooks.output_utils._HOOK_ERROR_LOG", log_file):
            yield log_file

    def test_returns_empty_when_no_file(self, tmp_path):
        """Should return empty list when log file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.log"
        with patch("cchooks.output_utils._HOOK_ERROR_LOG", nonexistent):
            errors = get_hook_errors()
            assert errors == []

    def test_parses_single_error(self, mock_log_file):
        """Should parse a single error entry."""
        ts = datetime.now().isoformat()
        mock_log_file.write_text(f"[{ts}] test-hook (PreToolUse): Test error\n")

        errors = get_hook_errors(since_minutes=5)
        assert len(errors) == 1
        assert errors[0]["hook_name"] == "test-hook"
        assert errors[0]["hook_type"] == "PreToolUse"
        assert errors[0]["error"] == "Test error"

    def test_parses_error_with_traceback(self, mock_log_file):
        """Should parse error and capture traceback."""
        ts = datetime.now().isoformat()
        content = f"""[{ts}] test-hook (PreToolUse): Test error
Traceback (most recent call last):
  File "test.py", line 1
Error details

"""
        mock_log_file.write_text(content)

        errors = get_hook_errors(since_minutes=5)
        assert len(errors) == 1
        assert "traceback" in errors[0]
        assert "Traceback" in errors[0]["traceback"]

    def test_filters_by_time(self, mock_log_file):
        """Should filter errors by since_minutes."""
        old_ts = (datetime.now() - timedelta(minutes=10)).isoformat()
        new_ts = datetime.now().isoformat()
        content = f"""[{old_ts}] old-hook (PreToolUse): Old error
[{new_ts}] new-hook (PreToolUse): New error
"""
        mock_log_file.write_text(content)

        errors = get_hook_errors(since_minutes=5)
        assert len(errors) == 1
        assert errors[0]["hook_name"] == "new-hook"

    def test_respects_limit(self, mock_log_file):
        """Should limit number of returned errors."""
        ts = datetime.now().isoformat()
        lines = [f"[{ts}] hook-{i} (PreToolUse): Error {i}\n" for i in range(10)]
        mock_log_file.write_text("".join(lines))

        errors = get_hook_errors(limit=3)
        assert len(errors) == 3
        # Should return the most recent (last) errors
        assert errors[-1]["hook_name"] == "hook-9"


class TestFormatErrorsForDisplay:
    """Test format_errors_for_display function."""

    def test_returns_empty_for_no_errors(self):
        """Should return empty string for empty list."""
        result = format_errors_for_display([])
        assert result == ""

    def test_formats_single_error(self):
        """Should format a single error."""
        errors = [{
            "hook_name": "test-hook",
            "hook_type": "PreToolUse",
            "error": "Test error message",
        }]
        result = format_errors_for_display(errors)
        assert "**Hook Errors (1)**" in result
        assert "`test-hook`" in result
        assert "(PreToolUse)" in result
        assert "Test error message" in result

    def test_truncates_long_messages(self):
        """Should truncate error messages over 100 chars."""
        errors = [{
            "hook_name": "test-hook",
            "hook_type": "PreToolUse",
            "error": "x" * 200,
        }]
        result = format_errors_for_display(errors)
        # The error message in the output should be truncated to 100 chars
        # Count x's after the colon
        assert result.count("x") == 100


class TestClearHookErrors:
    """Test clear_hook_errors function."""

    def test_removes_log_file(self, tmp_path):
        """Should delete the log file."""
        log_file = tmp_path / "hook-errors.log"
        log_file.write_text("test content")

        with patch("cchooks.output_utils._HOOK_ERROR_LOG", log_file):
            clear_hook_errors()

        assert not log_file.exists()

    def test_handles_nonexistent_file(self, tmp_path):
        """Should not raise error if file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.log"
        with patch("cchooks.output_utils._HOOK_ERROR_LOG", nonexistent):
            # Should not raise
            clear_hook_errors()
