"""Hook-specific contexts for Claude Code hooks."""

from .base import BaseHookContext, BaseHookOutput
from .pre_tool_use import PreToolUseContext, PreToolUseOutput
from .post_tool_use import PostToolUseContext, PostToolUseOutput
from .notification import NotificationContext, NotificationOutput
from .user_prompt_submit import UserPromptSubmitContext, UserPromptSubmitOutput
from .stop import StopContext, StopOutput
from .subagent_stop import SubagentStopContext, SubagentStopOutput
from .subagent_start import SubagentStartContext, SubagentStartOutput
from .pre_compact import PreCompactContext, PreCompactOutput
from .session_start import SessionStartContext, SessionStartOutput
from .session_end import SessionEndContext, SessionEndOutput

__all__ = [
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
    "SubagentStopContext",
    "SubagentStopOutput",
    "SubagentStartContext",
    "SubagentStartOutput",
    "PreCompactContext",
    "PreCompactOutput",
    "SessionStartContext",
    "SessionStartOutput",
    "SessionEndContext",
    "SessionEndOutput",
]
