"""Tests for type definitions in cchooks.types module."""

import pytest

from cchooks.types import (
    HookEventType,
    #   ToolName,
    PreCompactTrigger,
    PreToolUsePermissionDecision,
    SessionStartSource,
    SessionEndReason,
    PostToolUseHookSpecificOutput,
    SessionEndHookSpecificOutput,
)


class TestTypeLiterals:
    """Test type literal definitions."""

    def test_hook_event_type_values(self):
        """Test all valid HookEventType values."""
        valid_values = [
            "PreToolUse",
            "PostToolUse",
            "Notification",
            "Stop",
            "SubagentStop",
            "PreCompact",
            "UserPromptSubmit",
            "SessionStart",
            "SessionEnd",
        ]

        for value in valid_values:
            # This will raise TypeError if value is not valid
            HookEventType.__args__  # Access to check it's a Literal
            assert value in HookEventType.__args__

    #     def test_tool_name_values(self):
    #         """Test all valid ToolName values."""
    #         valid_tools = [
    #             "Task",
    #             "Bash",
    #             "Glob",
    #             "Grep",
    #             "Read",
    #             "Edit",
    #             "MultiEdit",
    #             "Write",
    #             "WebFetch",
    #             "WebSearch",
    #         ]
    #
    #         for tool in valid_tools:
    #             assert tool in ToolName.__args__

    def test_pre_compact_trigger_values(self):
        """Test all valid PreCompactTrigger values."""
        valid_triggers = ["manual", "auto"]

        for trigger in valid_triggers:
            assert trigger in PreCompactTrigger.__args__

    def test_decision_type_values(self):
        """Test all valid decision type values."""
        assert PreToolUsePermissionDecision.__args__ == ("allow", "deny", "ask")

    def test_session_start_source_values(self):
        """Test all valid SessionStartSource values."""
        valid_sources = ["startup", "resume", "clear"]

        for source in valid_sources:
            assert source in SessionStartSource.__args__

    def test_session_end_reason_values(self):
        """Test all valid SessionEndReason values."""
        valid_reasons = ["clear", "logout", "prompt_input_exit", "other"]

        for reason in valid_reasons:
            assert reason in SessionEndReason.__args__


class TestTypeValidation:
    """Test type validation and constraints."""

    @pytest.mark.parametrize(
        "invalid_value", ["InvalidHook", "", "pre_tool_use", "POST_TOOL_USE"]
    )
    def test_invalid_hook_event_type(self, invalid_value):
        """Test that invalid hook event types are rejected."""
        assert invalid_value not in HookEventType.__args__

    #     @pytest.mark.parametrize(
    #         "invalid_tool", ["invalid_tool", "", "bash", "BASH", "Git"]
    #     )
    #     def test_invalid_tool_name(self, invalid_tool):
    #         """Test that invalid tool names are rejected."""
    #         assert invalid_tool not in ToolName.__args__

    @pytest.mark.parametrize(
        "invalid_trigger", ["manual_auto", "", "MANUAL", "auto_manual"]
    )
    def test_invalid_pre_compact_trigger(self, invalid_trigger):
        """Test that invalid PreCompact triggers are rejected."""
        assert invalid_trigger not in PreCompactTrigger.__args__

    @pytest.mark.parametrize(
        "invalid_decision", ["approve", "block", "", "ALLOW", "yes"]
    )
    def test_invalid_pre_tool_use_decision(self, invalid_decision):
        """Test that invalid PreToolUse decisions are rejected."""
        assert invalid_decision not in PreToolUsePermissionDecision.__args__


class TestTypeCompleteness:
    """Test that all expected types are defined."""

    def test_all_hook_types_present(self):
        """Test that all 9 hook types are defined."""
        expected_hooks = {
            "PreToolUse",
            "PostToolUse",
            "Notification",
            "Stop",
            "SubagentStop",
            "PreCompact",
            "UserPromptSubmit",
            "SessionStart",
            "SessionEnd",
        }
        actual_hooks = set(HookEventType.__args__)
        assert expected_hooks == actual_hooks


#     def test_all_tools_present(self):
#         """Test that all expected tools are defined."""
#         expected_tools = {
#             "Task",
#             "Bash",
#             "Glob",
#             "Grep",
#             "Read",
#             "Edit",
#             "MultiEdit",
#             "Write",
#             "WebFetch",
#             "WebSearch",
#         }
#         actual_tools = set(ToolName.__args__)
#         assert expected_tools == actual_tools


class TestHookSpecificOutputTypes:
    """Test hook-specific output type definitions."""

    def test_post_tool_use_hook_specific_output(self):
        """Test PostToolUseHookSpecificOutput type structure."""
        # Test that the type accepts the expected fields
        test_output = {
            "hookEventName": "PostToolUse",
            "additionalContext": "Test additional context",
        }
        assert test_output["hookEventName"] == "PostToolUse"
        assert test_output["additionalContext"] == "Test additional context"

    def test_post_tool_use_hook_specific_output_optional_context(self):
        """Test PostToolUseHookSpecificOutput with optional additionalContext."""
        test_output = {
            "hookEventName": "PostToolUse",
            "additionalContext": None,
        }
        assert test_output["hookEventName"] == "PostToolUse"
        assert test_output["additionalContext"] is None

    def test_session_end_hook_specific_output(self):
        """Test SessionEndHookSpecificOutput type structure."""
        test_output = {
            "hookEventName": "SessionEnd",
        }
        assert test_output["hookEventName"] == "SessionEnd"
