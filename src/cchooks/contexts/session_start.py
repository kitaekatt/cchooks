"""SessionStart hook context and output classes."""

import json
import sys
from typing import Any, Dict, Optional

from ..exceptions import HookValidationError
from ..types import SessionStartSource
from .base import BaseHookContext, BaseHookOutput


class SessionStartContext(BaseHookContext):
    """Context for SessionStart hooks.

    Runs when Claude Code starts a new session or resumes an existing session.
    Useful for loading in development context like existing issues or recent
    changes to your codebase, installing dependencies, or setting up environment variables.

    SessionStart hooks cannot block execution - they can only add context
    or exit with errors.

    Environment Variables:
        CLAUDE_ENV_FILE: Path to a file where hooks can persist environment variables
                        for subsequent bash commands during the session
                        (only available for SessionStart hooks)
        CLAUDE_PROJECT_DIR: Absolute path to the project root directory (available to all hooks)
        CLAUDE_CODE_REMOTE: "true" if running in remote web environment, empty/unset if local CLI (available to all hooks)
        CLAUDE_PLUGIN_ROOT: Absolute path to the plugin directory (available for plugin hooks)
    """

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize the SessionStart context.

        Args:
            input_data (Dict[str, Any]): Parsed JSON input from Claude Code
        """
        super().__init__(input_data)
        self._validate_session_start_fields()

    def _validate_session_start_fields(self) -> None:
        """Validate SessionStart-specific fields."""
        required_fields = ["source"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required SessionStart fields: {', '.join(self._missing_fields)}"
            )

    @property
    def source(self) -> SessionStartSource:
        """Get the session start source.

        Returns:
            SessionStartSource: One of 'startup', 'resume', 'clear', or 'compact'
        """
        return str(self._input_data["source"])  # type: ignore

    @property
    def output(self) -> "SessionStartOutput":
        """Get the output handler for this context.

        Returns:
            SessionStartOutput: Output handler for SessionStart hooks
        """
        return SessionStartOutput()


class SessionStartOutput(BaseHookOutput):
    """Output handler for SessionStart hooks.

    SessionStart hooks cannot make decisions or block execution. They can only:
    - Add context to the session via additionalContext
    - Exit with success (exit code 0) - stdout is added to session context
    - Exit with errors (exit codes 1 or 2) - stderr shown to user only

    Note: Unlike most hooks, SessionStart stdout from exit code 0 is added to
    the session context rather than shown in transcript mode.
    """

    def add_context(
        self,
        context: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Add additional context to the session using hookSpecificOutput.

        The context string will be added to Claude's context for the session.
        This is the primary functionality of SessionStart hooks.

        Args:
            context (str): Context string to add to the session
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        hook_specific_output = {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
        output = self._with_specific_output(
            output, "SessionStart", **hook_specific_output
        )
        print(json.dumps(output), file=sys.stdout)

    def exit_success(self, message: Optional[str] = None) -> None:
        """Exit with success (exit code 0).

        Alias for simple_success(). Any message provided will be added to
        the session context, not shown in transcript mode.

        Args:
            message (Optional[str]): Message to add to session context (default: None)
        """
        self._success(message)

    def exit_non_block(self, message: str) -> None:
        """Exit with non-blocking error (exit code 1).

        Shows error message to user via stderr but does not block execution.
        SessionStart hooks cannot block Claude processing.

        Args:
            message (str): Error message shown to user
        """
        self._error(message)

    def exit_block(self, message: str) -> None:
        """Exit with blocking error (exit code 2).

        For SessionStart hooks, this behaves the same as exit_non_block() since
        SessionStart hooks cannot block Claude processing. The error message
        is shown to user via stderr.

        Args:
            message (str): Error message shown to user
        """
        self._block(message)
