"""SessionEnd hook context and output classes."""

from typing import Any, Dict, Optional

from ..exceptions import HookValidationError
from ..types import SessionEndReason
from .base import BaseHookContext, BaseHookOutput


class SessionEndContext(BaseHookContext):
    """Context for SessionEnd hooks.

    Runs when a Claude Code session ends. Useful for cleanup tasks, logging session
    statistics, or saving session state.

    SessionEnd hooks cannot block session termination but can perform cleanup tasks.
    """

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize the SessionEnd context.

        Args:
            input_data (Dict[str, Any]): Parsed JSON input from Claude Code
        """
        super().__init__(input_data)
        self._validate_session_end_fields()

    def _validate_session_end_fields(self) -> None:
        """Validate SessionEnd-specific fields."""
        required_fields = ["reason", "cwd"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required SessionEnd fields: {', '.join(self._missing_fields)}"
            )

    @property
    def reason(self) -> SessionEndReason:
        """Get the session end reason.

        Returns:
            SessionEndReason: One of 'clear', 'logout', 'prompt_input_exit', or 'other'
        """
        return str(self._input_data["reason"])  # type: ignore

    @property
    def cwd(self) -> str:
        """Get the current working directory.

        Returns:
            str: Current working directory when the hook was invoked
        """
        return str(self._input_data["cwd"])

    @property
    def output(self) -> "SessionEndOutput":
        """Get the output handler for this context.

        Returns:
            SessionEndOutput: Output handler for SessionEnd hooks
        """
        return SessionEndOutput()


class SessionEndOutput(BaseHookOutput):
    """Output handler for SessionEnd hooks.

    SessionEnd hooks run when a session ends and cannot block session termination.
    They can only:
    - Exit with success (exit code 0) - logged to debug only
    - Exit with errors (exit codes 1 or 2) - stderr shown to user only

    SessionEnd hooks are primarily for cleanup tasks and cannot make decisions
    or block session termination.
    """

    def exit_success(self, message: Optional[str] = None) -> None:
        """Exit with success (exit code 0).

        For SessionEnd hooks, success output is logged to debug only and not
        shown to users or added to any context.

        Args:
            message (Optional[str]): Success message (default: None)
        """
        self._success(message)

    def exit_non_block(self, message: str) -> None:
        """Exit with non-blocking error (exit code 1).

        Shows error message to user via stderr but does not affect session
        termination since the session is already ending.

        Args:
            message (str): Error message shown to user
        """
        self._error(message)

    def exit_block(self, message: str) -> None:
        """Exit with blocking error (exit code 2).

        For SessionEnd hooks, this behaves the same as exit_non_block() since
        SessionEnd hooks cannot block session termination. The error message
        is shown to user via stderr.

        Args:
            message (str): Error message shown to user
        """
        self._block(message)
