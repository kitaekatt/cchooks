"""Base classes for hook contexts and outputs."""

import json
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, NoReturn, Optional, TextIO

from ..exceptions import ParseError
from ..types import CompleteOutput, HookEventType, CommonOutput


class BaseHookContext(ABC):
    """Base class for all hook contexts.

    Environment Variables Available to All Hooks:
        CLAUDE_PROJECT_DIR: Absolute path to the project root directory
        CLAUDE_CODE_REMOTE: "true" if running in remote web environment,
                           empty/unset if running in local CLI environment
        CLAUDE_PLUGIN_ROOT: Absolute path to the plugin directory (available for plugin hooks)
    """

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize the context with parsed input data."""
        self._input_data = input_data
        self._missing_fields: list[str] = []
        self._validate_common_fields()

    def _validate_common_fields(self) -> None:
        """Validate fields common to all hook types."""
        required_fields = ["session_id", "transcript_path", "hook_event_name"]
        for field in required_fields:
            if field not in self._input_data:
                self._missing_fields.append(field)

    @property
    def session_id(self) -> str:
        """Get the session ID."""
        return str(self._input_data["session_id"])

    @property
    def transcript_path(self) -> str:
        """Get the transcript file path."""
        return str(self._input_data["transcript_path"])

    @property
    def hook_event_name(self) -> HookEventType:
        """Get the hook event name."""
        return str(self._input_data["hook_event_name"])  # type: ignore

    @property
    def claude_project_dir(self) -> Optional[str]:
        """Get the Claude project directory from environment."""
        import os

        return os.environ.get("CLAUDE_PROJECT_DIR")

    @property
    def claude_code_remote(self) -> bool:
        """Check if running in remote web environment."""
        import os

        return os.environ.get("CLAUDE_CODE_REMOTE") == "true"

    @property
    def claude_plugin_root(self) -> Optional[str]:
        """Get the Claude plugin root directory from environment."""
        import os

        return os.environ.get("CLAUDE_PLUGIN_ROOT")

    @classmethod
    def from_stdin(cls, stdin: TextIO = sys.stdin) -> "BaseHookContext":
        """Create context from stdin JSON input."""
        try:
            input_data = json.load(stdin)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON input: {e}")

        if not isinstance(input_data, dict):
            raise ParseError("Input must be a JSON object")

        return cls(input_data)

    @property
    @abstractmethod
    def output(self) -> "BaseHookOutput":
        """Get the appropriate output handler for this hook type."""
        pass


class BaseHookOutput(ABC):
    """Base class for all hook outputs."""

    def __init__(self) -> None:
        """Initialize the output handler."""
        # self.base_json = base_json
        pass

    def _continue_flow(
        self, suppress_output: bool = False, system_message: Optional[str] = None
    ) -> CommonOutput:
        """Construct Json with continue is true"""
        result: CommonOutput = {
            "continue": True,
            "suppressOutput": suppress_output,
        }
        if system_message is not None:
            result["systemMessage"] = system_message
        return result

    def _stop_flow(
        self,
        stop_reason: str,
        suppress_output: bool = False,
        system_message: Optional[str] = None,
    ) -> CommonOutput:
        """Construct Json with continue is false"""
        result: CommonOutput = {
            "continue": False,
            "stopReason": stop_reason,
            "suppressOutput": suppress_output,
        }
        if system_message is not None:
            result["systemMessage"] = system_message
        return result

    def _with_specific_output(
        self, common_output: CommonOutput, hook_event_name: str, **specific_fields: Any
    ) -> CompleteOutput:
        """Add hook-specific output to base JSON structure."""
        common_output["hookSpecificOutput"] = {
            "hookEventName": hook_event_name,
            **specific_fields,
        }
        return common_output

    def _success(self, message: Optional[str] = None) -> NoReturn:
        """Exit with success (exit code 0)."""
        if message:
            print(message, file=sys.stdout)
        sys.exit(0)

    def _error(self, message: str, exit_code: int = 1) -> NoReturn:
        """Exit with error (non-blocking)."""
        print(message, file=sys.stderr)
        sys.exit(exit_code)

    def _block(self, reason: str) -> NoReturn:
        """Exit with blocking error (exit code 2)."""
        print(reason, file=sys.stderr)
        sys.exit(2)
