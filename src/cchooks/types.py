"""Type definitions for Claude Code hooks."""

from typing import Any, Dict, Literal, Union, Optional

# Hook event types
HookEventType = Literal[
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
]

# Trigger types for PreCompact
PreCompactTrigger = Literal["manual", "auto"]

# Source types for SessionStart
SessionStartSource = Literal["startup", "resume", "clear", "compact"]

# Reason types for SessionEnd
SessionEndReason = Literal["clear", "logout", "prompt_input_exit", "other"]

# Permission decision types for PreToolUse
PreToolUsePermissionDecision = Literal["allow", "deny", "ask"]

# Notification types
NotificationType = Literal[
    "permission_prompt",
    "idle_prompt",
    "auth_success",
    "elicitation_dialog",
]

# Hook execution types
HookExecutionType = Literal["command", "prompt"]

# Prompt-based hook response schema
PromptHookResponse = Dict[
    str, Any
]  # { decision: "approve" | "block", reason: str, continue?: bool, stopReason?: str, systemMessage?: str }

# Common fields present in all hook inputs
CommonInputFields = Dict[str, Any]  # session_id, transcript_path, hook_event_name

# Hook-specific input types
PreToolUseInput = Dict[str, Any]  # + tool_name, tool_input, cwd
PostToolUseInput = Dict[str, Any]  # + tool_name, tool_input, tool_response, cwd
NotificationInput = Dict[str, Any]  # + message, cwd, notification_type
UserPromptSubmitInput = Dict[str, Any]  # + prompt, cwd
StopInput = Dict[str, Any]  # + stop_hook_active
SubagentStopInput = Dict[str, Any]  # + stop_hook_active
PreCompactInput = Dict[str, Any]  # + trigger, custom_instructions
SessionStartInput = Dict[str, Any]  # + source
SessionEndInput = Dict[str, Any]  # + reason, cwd

# Hook input union
HookInput = Union[
    PreToolUseInput,
    PostToolUseInput,
    NotificationInput,
    UserPromptSubmitInput,
    StopInput,
    SubagentStopInput,
    PreCompactInput,
    SessionStartInput,
    SessionEndInput,
]


# Hook-specific output types
class HookSpecificOutput(Dict[str, Any]):
    """Base class for hook-specific output."""

    pass


class PreToolUseHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for PreToolUse."""

    hookEventName: Literal["PreToolUse"]
    permissionDecision: PreToolUsePermissionDecision
    permissionDecisionReason: str
    updatedInput: Optional[Dict[str, Any]] = None


class UserPromptSubmitHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for UserPromptSubmit."""

    hookEventName: Literal["UserPromptSubmit"]
    additionalContext: Optional[str] = None


class PostToolUseHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for PostToolUse."""

    hookEventName: Literal["PostToolUse"]
    additionalContext: Optional[str] = None


class StopHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for Stop."""

    hookEventName: Literal["Stop"]


class SubagentStopHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for SubagentStop."""

    hookEventName: Literal["SubagentStop"]


class PreCompactHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for PreCompact."""

    hookEventName: Literal["PreCompact"]


class SessionStartHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for SessionStart."""

    hookEventName: Literal["SessionStart"]
    additionalContext: Optional[str] = None


class SessionEndHookSpecificOutput(HookSpecificOutput):
    """Hook-specific output for SessionEnd."""

    hookEventName: Literal["SessionEnd"]


# JSON output types
CompleteOutput = Dict[str, Any]
CommonOutput = Dict[
    str, Any
]  # continue, stopReason, suppressOutput, systemMessage, hookSpecificOutput
