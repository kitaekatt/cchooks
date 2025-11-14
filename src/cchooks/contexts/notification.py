"""Notification hook context and output."""

from typing import Any, Dict, NoReturn, Optional

from .base import BaseHookContext, BaseHookOutput
from ..exceptions import HookValidationError


class NotificationContext(BaseHookContext):
    """Context for Notification hooks."""

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize Notification context."""
        super().__init__(input_data)
        self._validate_notification_fields()

    def _validate_notification_fields(self) -> None:
        """Validate Notification-specific fields."""
        required_fields = ["message", "cwd"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required fields: {', '.join(self._missing_fields)}"
            )

    @property
    def message(self) -> str:
        """Get the notification message."""
        return str(self._input_data["message"])

    @property
    def cwd(self) -> str:
        """Get the current working directory."""
        return str(self._input_data["cwd"])

    @property
    def notification_type(self) -> Optional[str]:
        """Get the notification type if available."""
        return self._input_data.get("notification_type")

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
    def output(self) -> "NotificationOutput":
        """Get the Notification-specific output handler."""
        return NotificationOutput()


class NotificationOutput(BaseHookOutput):
    """Output handler for Notification hooks.

    Note: Notification hooks cannot make decisions, they can only process.
    """

    def acknowledge(self, message: Optional[str]) -> NoReturn:  # type: ignore
        """Acknowledge the notification (exit code 0).

        Args:
            message(Optional[str]): Message shown to the user in transcript (default: None)
        """
        self._success(message)

    def exit_block(self, message: str) -> NoReturn:
        """Exit with blocking error (exit code 2). Same as exit_non_block()

        Args:
            message(str): Message shown to the user
        """
        self._block(message)

    def exit_non_block(self, message: str) -> NoReturn:
        """Exit with non-blocking error (exit code 1). Same as exit_block()

        Args:
            message (str): Message shown to the user
        """
        self._error(message)
