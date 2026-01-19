"""Claude Code hooks Python module.
Copyright (c) 2025 Haoyuan Li
MIT License

This module provides a comprehensive, type-safe interface for developing
Claude Code hooks with automatic hook type detection and specialized
contexts for each hook lifecycle.

Basic Usage:
    from cchooks import create_context

    context = create_context()

    if isinstance(context, PreToolUseContext):
        tool_name = context.tool_name
        tool_input = context.tool_input
        context.output.approve(reason="Safe operation")

Hook Types:
    - PreToolUse: Runs before tool execution, can approve/block
    - PostToolUse: Runs after tool execution, can only block
    - Notification: Processes notifications, no decision control
    - UserPromptSubmit: Runs before prompt processing, can block
    - Stop: Controls Claude stopping behavior
    - SubagentStart: Runs when subagent spawns, can add context
    - SubagentStop: Controls subagent stopping behavior
    - PreCompact: Runs before transcript compaction
    - SessionStart: Runs when Claude Code starts or resumes sessions
    - SessionEnd: Runs when Claude Code session ends
"""

import sys
from typing import TextIO, Union

from .master_switch import are_hooks_enabled, exit_if_hooks_disabled
from .contexts import (
    BaseHookContext,
    BaseHookOutput,
    NotificationContext,
    NotificationOutput,
    PostToolUseContext,
    PostToolUseOutput,
    PreCompactContext,
    PreCompactOutput,
    PreToolUseContext,
    PreToolUseOutput,
    SessionEndContext,
    SessionEndOutput,
    SessionStartContext,
    SessionStartOutput,
    StopContext,
    StopOutput,
    SubagentStartContext,
    SubagentStartOutput,
    SubagentStopContext,
    SubagentStopOutput,
    UserPromptSubmitContext,
    UserPromptSubmitOutput,
)
from .exceptions import (
    CCHooksError,
    HookValidationError,
    InvalidHookTypeError,
    ParseError,
)
from .output_utils import (
    clear_hook_errors,
    exit_block,
    exit_non_block,
    exit_success,
    format_errors_for_display,
    get_hook_errors,
    handle_context_error,
    handle_invalid_hook_type,
    handle_parse_error,
    handle_validation_error,
    output_json,
    safe_create_context,
)
from .utils import read_json_from_stdin, validate_required_fields
from .decorators import safe_hook_wrapper

# Type alias for all possible context types
HookContext = Union[
    PreToolUseContext,
    PostToolUseContext,
    NotificationContext,
    UserPromptSubmitContext,
    StopContext,
    SubagentStartContext,
    SubagentStopContext,
    PreCompactContext,
    SessionStartContext,
    SessionEndContext,
]

# Mapping of hook event names to context classes
_HOOK_TYPE_MAP: dict[str, type[HookContext]] = {
    "PreToolUse": PreToolUseContext,
    "PostToolUse": PostToolUseContext,
    "Notification": NotificationContext,
    "UserPromptSubmit": UserPromptSubmitContext,
    "Stop": StopContext,
    "SubagentStart": SubagentStartContext,
    "SubagentStop": SubagentStopContext,
    "PreCompact": PreCompactContext,
    "SessionStart": SessionStartContext,
    "SessionEnd": SessionEndContext,
}


def create_context(stdin: TextIO = sys.stdin) -> HookContext:
    """Create appropriate context based on input JSON.

    Reads JSON from stdin and automatically detects the hook type based on
    the 'hook_event_name' field, returning the appropriate specialized context.

    Note:
        If hooks are globally disabled via the master switch in
        ~/.claude/hooks/config/hook-categories.yaml (hooks_enabled: false),
        this function will exit early with code 0, silently allowing the
        operation without executing any hook logic.

    Returns:
        Context object specific to the detected hook type

    Raises:
        ParseError: If JSON is invalid
        InvalidHookTypeError: If hook_event_name is not recognized
        HookValidationError: If required fields are missing
    """
    # Check master switch first - exit early if hooks are disabled
    exit_if_hooks_disabled()

    input_data = read_json_from_stdin(stdin)

    hook_event_name = input_data.get("hook_event_name")
    if not hook_event_name:
        raise InvalidHookTypeError("Missing hook_event_name in input")

    context_class = _HOOK_TYPE_MAP.get(hook_event_name)
    if not context_class:
        raise InvalidHookTypeError(f"Unknown hook event type: {hook_event_name}")

    return context_class(input_data)


__all__ = [
    # Contexts
    "BaseHookContext",
    "BaseHookOutput",
    "PreToolUseContext",
    "PreToolUseOutput",
    "PostToolUseContext",
    "PostToolUseOutput",
    "NotificationContext",
    "NotificationOutput",
    "UserPromptSubmitContext",
    "UserPromptSubmitOutput",
    "StopContext",
    "StopOutput",
    "SubagentStartContext",
    "SubagentStartOutput",
    "SubagentStopContext",
    "SubagentStopOutput",
    "PreCompactContext",
    "PreCompactOutput",
    "SessionStartContext",
    "SessionStartOutput",
    "SessionEndContext",
    "SessionEndOutput",
    # Factory function
    "create_context",
    # Exceptions
    "CCHooksError",
    "HookValidationError",
    "ParseError",
    "InvalidHookTypeError",
    # Utilities
    "read_json_from_stdin",
    "validate_required_fields",
    # Output utilities
    "output_utils",
    "exit_success",
    "exit_non_block",
    "exit_block",
    "output_json",
    "handle_parse_error",
    "handle_validation_error",
    "handle_invalid_hook_type",
    "handle_context_error",
    "safe_create_context",
    # Error log reading
    "get_hook_errors",
    "format_errors_for_display",
    "clear_hook_errors",
    # Type aliases
    "HookContext",
    # Master switch
    "are_hooks_enabled",
    "exit_if_hooks_disabled",
    # Decorators
    "safe_hook_wrapper",
]
