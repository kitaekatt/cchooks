"""Stop hook context and output."""

import json
import sys
from typing import Any, Dict, NoReturn, Optional

from .base import BaseHookContext, BaseHookOutput
from ..exceptions import HookValidationError


class StopContext(BaseHookContext):
    """Context for Stop hooks."""

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize Stop context."""
        super().__init__(input_data)
        self._validate_stop_fields()

    def _validate_stop_fields(self) -> None:
        """Validate Stop-specific fields."""
        if "stop_hook_active" not in self._input_data:
            self._missing_fields.append("stop_hook_active")

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required Stop fields: {', '.join(self._missing_fields)}"
            )

    @property
    def stop_hook_active(self) -> bool:
        """stop_hook_active is true when Claude Code is already continuing as a result of a stop hook"""
        return bool(self._input_data["stop_hook_active"])

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
    def output(self) -> "StopOutput":
        """Get the Stop-specific output handler."""
        return StopOutput()


class StopOutput(BaseHookOutput):
    """Output handler for Stop hooks."""

    def halt(
        self,
        stop_reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Stop all processing immediately with JSON response.

        Args:
            stop_reason (str): Stopping reason shown to the user, not shown to Claude
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._stop_flow(stop_reason, suppress_output, system_message)
        print(json.dumps(output), file=sys.stdout)

    def prevent(
        self,
        reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Prevent Claude from stopping and Prompt Claude with JSON response.

        Args:
            reason (str): Reason shown to Clade for further reasoning
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        output.update({"decision": "block", "reason": reason})
        print(json.dumps(output), file=sys.stdout)

    def allow(
        self, suppress_output: bool = False, system_message: Optional[str] = None
    ) -> None:
        """Allow Claude to stop and Do nothing with JSON response.

        Args:
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
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
