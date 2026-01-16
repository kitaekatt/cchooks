"""SubagentStart hook context and output classes.

SubagentStart hooks run when a subagent is spawned via the Task tool.
This is the injection point for adding context to sub-agents.
"""

import json
import sys
from typing import Any, Dict, Optional

from ..exceptions import HookValidationError
from .base import BaseHookContext, BaseHookOutput


class SubagentStartContext(BaseHookContext):
    """Context for SubagentStart hooks.

    Runs when Claude Code spawns a subagent via the Task tool.
    Useful for injecting rules, context, or configuration into sub-agents.

    SubagentStart hooks cannot block execution - they can only add context
    or exit with errors.

    Input Fields:
        agent_id (str): Unique identifier for the subagent
        agent_type (str): Type of subagent being spawned (e.g., 'Explore', 'Plan')
    """

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize the SubagentStart context.

        Args:
            input_data (Dict[str, Any]): Parsed JSON input from Claude Code
        """
        super().__init__(input_data)
        self._validate_subagent_start_fields()

    def _validate_subagent_start_fields(self) -> None:
        """Validate SubagentStart-specific fields."""
        required_fields = ["agent_id", "agent_type"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required SubagentStart fields: {', '.join(self._missing_fields)}"
            )

    @property
    def agent_id(self) -> str:
        """Get the unique identifier for this subagent.

        Returns:
            str: Unique agent identifier
        """
        return str(self._input_data["agent_id"])

    @property
    def agent_type(self) -> str:
        """Get the type of subagent being spawned.

        Returns:
            str: Agent type (e.g., 'Explore', 'Plan', 'backend-developer')
        """
        return str(self._input_data["agent_type"])

    def is_subagent(self) -> bool:
        """Check if this hook is running in a sub-agent context.

        For SubagentStart hooks, this always returns True since
        this hook only fires for sub-agent spawning.

        Returns:
            bool: Always True for SubagentStart hooks
        """
        return True

    @property
    def output(self) -> "SubagentStartOutput":
        """Get the output handler for this context.

        Returns:
            SubagentStartOutput: Output handler for SubagentStart hooks
        """
        return SubagentStartOutput()


class SubagentStartOutput(BaseHookOutput):
    """Output handler for SubagentStart hooks.

    SubagentStart hooks cannot make decisions or block execution. They can only:
    - Add context to the subagent session via additionalContext
    - Exit with success (exit code 0)
    - Exit with errors (exit codes 1 or 2) - stderr shown to user only

    The primary use case is injecting rules, guidelines, or context into
    sub-agents that wouldn't otherwise have access to session-level context.
    """

    def add_context(
        self,
        context: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> None:
        """Add additional context to the subagent using hookSpecificOutput.

        The context string will be added to the subagent's context.
        This is the primary functionality of SubagentStart hooks.

        Args:
            context (str): Context string to add to the subagent
            suppress_output (bool): Hide stdout from transcript mode (default: False)
            system_message (Optional[str]): Optional message shown to the user (default: None)
        """
        output = self._continue_flow(suppress_output, system_message)
        hook_specific_output = {
            "hookEventName": "SubagentStart",
            "additionalContext": context,
        }
        output = self._with_specific_output(
            output, "SubagentStart", **hook_specific_output
        )
        print(json.dumps(output), file=sys.stdout)

    def exit_success(self, message: Optional[str] = None) -> None:
        """Exit with success (exit code 0).

        Args:
            message (Optional[str]): Message to add to context (default: None)
        """
        self._success(message)

    def exit_non_block(self, message: str) -> None:
        """Exit with non-blocking error (exit code 1).

        Shows error message to user via stderr but does not block execution.
        SubagentStart hooks cannot block subagent spawning.

        Args:
            message (str): Error message shown to user
        """
        self._error(message)

    def exit_block(self, message: str) -> None:
        """Exit with blocking error (exit code 2).

        For SubagentStart hooks, this behaves the same as exit_non_block() since
        SubagentStart hooks cannot block subagent spawning. The error message
        is shown to user via stderr.

        Args:
            message (str): Error message shown to user
        """
        self._block(message)
