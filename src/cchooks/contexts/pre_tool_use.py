"""PreToolUse hook context and output."""

import json
import sys
from typing import Any, Dict, NoReturn, Optional

from .base import BaseHookContext, BaseHookOutput
from ..exceptions import HookValidationError


class PreToolUseContext(BaseHookContext):
    """Context for PreToolUse hooks."""

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize PreToolUse context."""
        super().__init__(input_data)
        self._validate_pre_tool_use_fields()

    def _validate_pre_tool_use_fields(self) -> None:
        """Validate PreToolUse-specific fields."""
        required_fields = ["tool_name", "tool_input", "cwd"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required PreToolUse fields: {', '.join(self._missing_fields)}"
            )

        if not isinstance(self._input_data["tool_input"], dict):
            raise HookValidationError("tool_input must be a JSON object")

    @property
    def tool_name(self) -> str:
        """Get the tool name."""
        return str(self._input_data["tool_name"])  # type: ignore

    @property
    def tool_input(self) -> Dict[str, Any]:
        """Get the tool input parameters."""
        return dict(self._input_data["tool_input"])

    @property
    def cwd(self) -> str:
        """Get the current working directory."""
        return str(self._input_data["cwd"])

    @property
    def output(self) -> "PreToolUseOutput":
        """Get the PreToolUse-specific output handler."""
        return PreToolUseOutput()


class PreToolUseOutput(BaseHookOutput):
    """Output handler for PreToolUse hooks."""

    def allow(
        self,
        reason: str = "",
        suppress_output: bool = False,
        system_message: Optional[str] = None,
        updated_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Allow the tool execution using unified SpecificOutput format.

        Args:
            reason (str): Reason for allowing, shown to user
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
            updated_input (Optional[Dict[str, Any]]): Modified tool input parameters (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        specific_output: Dict[str, Any] = {
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
        if updated_input is not None:
            specific_output["updatedInput"] = updated_input
        output = self._with_specific_output(output, "PreToolUse", **specific_output)
        print(json.dumps(output), file=sys.stdout)

    def deny(
        self,
        reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
        updated_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Deny the tool execution using unified SpecificOutput format.

        Args:
            reason (str): Reason for denying, shown to Claude for further reasoning
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
            updated_input (Optional[Dict[str, Any]]): Modified tool input parameters (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        specific_output: Dict[str, Any] = {
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        if updated_input is not None:
            specific_output["updatedInput"] = updated_input
        output = self._with_specific_output(output, "PreToolUse", **specific_output)
        print(json.dumps(output), file=sys.stdout)

    def ask(
        self,
        reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
        updated_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Ask user to confirm the tool call using unified SpecificOutput format.

        Args:
            reason (str): Reason for asking, shown to user
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional warning message shown to the user (default: None)
            updated_input (Optional[Dict[str, Any]]): Modified tool input parameters (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        specific_output: Dict[str, Any] = {
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
        if updated_input is not None:
            specific_output["updatedInput"] = updated_input
        output = self._with_specific_output(output, "PreToolUse", **specific_output)
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
