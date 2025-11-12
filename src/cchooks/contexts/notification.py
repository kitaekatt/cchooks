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
