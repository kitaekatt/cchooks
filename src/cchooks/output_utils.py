"""Standalone output utilities for graceful error handling.

This module provides standalone functions for handling errors and producing output
when context objects are not available (e.g., during `create_context()` failures).

All errors are automatically logged to ~/.claude/tmp/hook-errors.log for visibility.
This module also provides functions to read and display those errors.
"""

import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, TextIO

# Simple log path for hook error visibility
_HOOK_ERROR_LOG = Path.home() / ".claude" / "tmp" / "hook-errors.log"


def _log_error_to_file(hook_name: str, error: Exception, hook_type: str = "unknown") -> None:
    """Log error to simple file for Claude visibility.

    This runs silently - errors in logging should never break hooks.
    """
    try:
        _HOOK_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        tb = traceback.format_exc()
        log_entry = f"[{timestamp}] {hook_name} ({hook_type}): {error}\n{tb}\n"
        with open(_HOOK_ERROR_LOG, "a") as f:
            f.write(log_entry)
    except Exception:
        pass  # Never let logging break the hook


def exit_success(message: Optional[str] = None, file: TextIO = sys.stdout) -> NoReturn:
    """Exit with success (exit code 0).

    Args:
        message: Optional success message to print
        file: Output file (defaults to stdout)
    """
    if message:
        print(message, file=file)
    sys.exit(0)


def exit_non_block(
    message: str, exit_code: int = 1, file: TextIO = sys.stderr
) -> NoReturn:
    """Exit with error (non-blocking).

    Args:
        message: Error message to print
        exit_code: Exit code (defaults to 1 for non-blocking error)
        file: Output file (defaults to stderr)
    """
    print(message, file=file)
    sys.exit(exit_code)


def exit_block(reason: str, file: TextIO = sys.stderr) -> NoReturn:
    """Exit with blocking error (exit code 2).

    Args:
        reason: Blocking reason to print
        file: Output file (defaults to stderr)
    """
    print(reason, file=file)
    sys.exit(2)


def output_json(data: Dict[str, Any], file: TextIO = sys.stdout) -> None:
    """Output JSON data to the specified file.

    Args:
        data: JSON-serializable data to output
        file: Output file (defaults to stdout)
    """
    print(json.dumps(data, ensure_ascii=False), file=file)


def handle_parse_error(
    error: Exception,
    file: TextIO = sys.stderr,
    hook_name: str = "unknown"
) -> NoReturn:
    """Handle JSON parsing errors gracefully.

    Args:
        error: The JSON parsing exception
        file: Output file for error message
        hook_name: Name of the hook (for logging)
    """
    _log_error_to_file(hook_name, error, "parse_error")
    exit_non_block(f"Failed to parse JSON input: {error}", exit_code=1, file=file)


def handle_validation_error(
    error: Exception,
    file: TextIO = sys.stderr,
    hook_name: str = "unknown"
) -> NoReturn:
    """Hook validation errors gracefully.

    Args:
        error: The validation exception
        file: Output file for error message
        hook_name: Name of the hook (for logging)
    """
    _log_error_to_file(hook_name, error, "validation_error")
    exit_non_block(f"Hook validation failed: {error}", exit_code=1, file=file)


def handle_invalid_hook_type(
    error: Exception,
    file: TextIO = sys.stderr,
    hook_name: str = "unknown"
) -> NoReturn:
    """Handle invalid hook type errors gracefully.

    Args:
        error: The invalid hook type exception
        file: Output file for error message
        hook_name: Name of the hook (for logging)
    """
    _log_error_to_file(hook_name, error, "invalid_hook_type")
    exit_non_block(f"Invalid hook type: {error}", exit_code=1, file=file)


def handle_context_error(
    error: Exception,
    file: TextIO = sys.stderr,
    hook_name: str = "unknown",
    hook_type: str = "unknown"
) -> NoReturn:
    """Unified handler for all context creation errors.

    Automatically logs errors to ~/.claude/tmp/hook-errors.log for visibility.

    Args:
        error: Exception from create_context()
        file: Output file for error message
        hook_name: Name of the hook (for logging)
        hook_type: Type of hook event (for logging)
    """
    from .exceptions import ParseError, InvalidHookTypeError, HookValidationError

    # Log error to file for Claude visibility
    _log_error_to_file(hook_name, error, hook_type)

    if isinstance(error, ParseError):
        handle_parse_error(error, file, hook_name)
    elif isinstance(error, InvalidHookTypeError):
        handle_invalid_hook_type(error, file, hook_name)
    elif isinstance(error, HookValidationError):
        handle_validation_error(error, file, hook_name)
    else:
        # Fallback for any other exceptions
        exit_non_block(f"Unexpected error: {error}", exit_code=1, file=file)


def safe_create_context(
    stdin: TextIO = sys.stdin, error_file: TextIO = sys.stderr
) -> Any:
    """Safe wrapper around create_context() with built-in error handling.

    Args:
        stdin: Input stream (defaults to sys.stdin)
        error_file: Output file for error messages

    Returns:
        Context object on success, or exits with appropriate error code on failure
    """
    from . import create_context

    try:
        return create_context(stdin)
    except Exception as e:
        handle_context_error(e, error_file)


# =============================================================================
# Error Log Reading Functions
# =============================================================================

# Regex to parse log entries: [timestamp] hook_name (hook_type): error
_LOG_ENTRY_PATTERN = re.compile(
    r"^\[([^\]]+)\]\s+(\S+)\s+\(([^)]+)\):\s+(.+)$"
)


def get_hook_errors(since_minutes: int = 5, limit: int = 10) -> List[Dict[str, Any]]:
    """Parse the hook error log and return recent errors.

    Parses entries in format: [timestamp] hook_name (hook_type): error

    Args:
        since_minutes: Only return errors from last N minutes
        limit: Maximum number of errors to return

    Returns:
        List of error dictionaries with keys: timestamp, hook_name, hook_type, error
    """
    if not _HOOK_ERROR_LOG.exists():
        return []

    errors: List[Dict[str, Any]] = []
    cutoff = datetime.now().timestamp() - (since_minutes * 60)

    try:
        with open(_HOOK_ERROR_LOG, "r") as f:
            current_entry: Optional[Dict[str, Any]] = None
            traceback_lines: List[str] = []

            for line in f:
                # Try to match a new log entry
                match = _LOG_ENTRY_PATTERN.match(line.rstrip())
                if match:
                    # Save previous entry if exists
                    if current_entry is not None:
                        if traceback_lines:
                            current_entry["traceback"] = "\n".join(traceback_lines)
                        errors.append(current_entry)

                    # Parse new entry
                    timestamp_str, hook_name, hook_type, error_msg = match.groups()
                    try:
                        ts = datetime.fromisoformat(timestamp_str).timestamp()
                    except ValueError:
                        ts = 0

                    if ts >= cutoff:
                        current_entry = {
                            "timestamp": timestamp_str,
                            "hook_name": hook_name,
                            "hook_type": hook_type,
                            "error": error_msg,
                        }
                        traceback_lines = []
                    else:
                        current_entry = None
                        traceback_lines = []
                elif current_entry is not None and line.strip():
                    # Accumulate traceback lines
                    traceback_lines.append(line.rstrip())

            # Don't forget the last entry
            if current_entry is not None:
                if traceback_lines:
                    current_entry["traceback"] = "\n".join(traceback_lines)
                errors.append(current_entry)

    except Exception:
        return []

    # Return most recent errors up to limit
    return errors[-limit:]


def format_errors_for_display(errors: List[Dict[str, Any]]) -> str:
    """Format errors as markdown for display in system messages.

    Args:
        errors: List of error dictionaries from get_hook_errors()

    Returns:
        Formatted markdown string for display
    """
    if not errors:
        return ""

    lines = [f"**Hook Errors ({len(errors)})**"]

    for err in errors:
        hook = err.get("hook_name", "unknown")
        hook_type = err.get("hook_type", "")
        msg = err.get("error", "")[:100]  # Truncate long messages

        lines.append(f"- `{hook}` ({hook_type}): {msg}")

    return "\n".join(lines)


def clear_hook_errors() -> None:
    """Clear/truncate the hook error log file."""
    try:
        if _HOOK_ERROR_LOG.exists():
            _HOOK_ERROR_LOG.unlink()
    except Exception:
        pass  # Never let clearing break anything
