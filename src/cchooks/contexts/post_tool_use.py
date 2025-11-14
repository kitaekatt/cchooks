"""PostToolUse hook context and output."""

import json
import sys
from typing import Any, Dict, NoReturn, Optional

from .base import BaseHookContext, BaseHookOutput
from ..exceptions import HookValidationError
# from ..types import ToolName


class PostToolUseContext(BaseHookContext):
    """Context for PostToolUse hooks."""

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize PostToolUse context."""
        super().__init__(input_data)
        self._validate_post_tool_use_fields()

    def _validate_post_tool_use_fields(self) -> None:
        """Validate PostToolUse-specific fields."""
        required_fields = ["tool_name", "tool_input", "tool_response", "cwd"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required PostToolUse fields: {', '.join(self._missing_fields)}"
            )

        if not isinstance(self._input_data["tool_input"], dict):
            raise HookValidationError("tool_input must be a JSON object")

        if not isinstance(self._input_data["tool_response"], dict):
            raise HookValidationError("tool_response must be a JSON object")

    @property
    def tool_name(self) -> str:
        """Get the tool name."""
        return str(self._input_data["tool_name"])  # type: ignore

    @property
    def tool_input(self) -> Dict[str, Any]:
        """Get the tool input parameters."""
        return dict(self._input_data["tool_input"])

    @property
    def tool_response(self) -> Dict[str, Any]:
        """Get the tool response data."""
        return dict(self._input_data["tool_response"])

    @property
    def cwd(self) -> str:
        """Get the current working directory."""
        return str(self._input_data["cwd"])

    def is_subagent(self) -> bool:
        """Check if this hook is running in a sub-agent context.

        Returns True if executed by a delegated Task, False if main Claude.
        Enables proper authorization and skill isolation patterns.

        Sub-agents are detected by checking if the transcript_path is in a
        different project directory than the main Claude project.
        """
        import os
        from pathlib import Path

        # Get the project directory containing this transcript
        transcript_path = Path(self.transcript_path)
        transcript_project_dir = transcript_path.parent.name

        # Check CLAUDE_PROJECT_DIR environment variable which indicates the
        # main project that is currently open in Claude Code
        main_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

        # Extract just the directory name from CLAUDE_PROJECT_DIR for comparison
        # (it's an absolute path, we need just the directory name)
        if main_project_dir:
            main_project_name = Path(main_project_dir).name
        else:
            # Fallback: assume main Claude uses "-home-christina--claude" pattern
            main_project_name = "-home-christina--claude"

        # Sub-agent is when the transcript is in a different project directory
        return transcript_project_dir != main_project_name

    @property
    def output(self) -> "PostToolUseOutput":
        """Get the PostToolUse-specific output handler."""
        return PostToolUseOutput()


class PostToolUseOutput(BaseHookOutput):
    """Output handler for PostToolUse hooks."""

    def accept(
        self, suppress_output: bool = False, system_message: Optional[str] = None
    ) -> None:
        """Accept the tool results and continue processing.

        Args:
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        print(json.dumps(output), file=sys.stdout)

    def challenge(
        self,
        reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Challenge the tool results and prompt Claude for review.

        Args:
            reason (str): Reason for challenging, shown to Claude for further reasoning
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        output.update({"decision": "block", "reason": reason})
        print(json.dumps(output), file=sys.stdout)

    def ignore(
        self, suppress_output: bool = False, system_message: Optional[str] = None
    ) -> None:
        """Ignore the tool results and continue processing.

        Args:
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        print(json.dumps(output), file=sys.stdout)

    def add_context(
        self,
        context: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Add additional context for Claude to consider using hookSpecificOutput.

        The context string will be provided to Claude for further reasoning
        after the tool execution.

        Args:
            context (str): Additional context for Claude to consider
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        hook_specific_output = {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
        output = self._with_specific_output(
            output, "PostToolUse", **hook_specific_output
        )
        print(json.dumps(output), file=sys.stdout)

    def halt(
        self,
        reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Stop all processing immediately.

        Args:
            reason (str): Reason for stopping, shown to user
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._stop_flow(reason, suppress_output, system_message)
        output.update({"decision": "block", "reason": ""})
        print(json.dumps(output), file=sys.stdout)

    def exit_success(self, message: Optional[str] = None) -> NoReturn:
        """Exit with success (exit code 0).

        Args:
            message (Optional[str]): Message shown to the user in transcript (default: None)
        """
        self._success(message)

    def exit_block(self, reason: str) -> NoReturn:
        """Exit with blocking error (exit code 2).

        Args:
            reason (str): Reason shown to Claude for further reasoning
        """
        self._block(reason)

    def exit_non_block(self, message: str) -> NoReturn:
        """Exit with non-blocking error (exit code 1).

        Args:
            message (str): Message shown to the user
        """
        self._error(message)
