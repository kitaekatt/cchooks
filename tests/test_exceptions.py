"""Tests for exception hierarchy in cchooks.exceptions module."""

import pytest

from cchooks.exceptions import (
    CCHooksError,
    HookValidationError,
    ParseError,
    InvalidHookTypeError,
)


class TestExceptionHierarchy:
    """Test the exception inheritance hierarchy."""

    def test_cchooks_error_base_class(self):
        """Test that CCHooksError is the base exception."""
        assert issubclass(HookValidationError, CCHooksError)
        assert issubclass(ParseError, CCHooksError)
        assert issubclass(InvalidHookTypeError, CCHooksError)

    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from Python's Exception."""
        assert issubclass(CCHooksError, Exception)
        assert issubclass(HookValidationError, Exception)
        assert issubclass(ParseError, Exception)
        assert issubclass(InvalidHookTypeError, Exception)


class TestExceptionMessages:
    """Test exception message formatting and content."""

    def test_cchooks_error_message(self):
        """Test CCHooksError message formatting."""
        error = CCHooksError("Test error message")
        assert str(error) == "Test error message"

    def test_hook_validation_error_message(self):
        """Test HookValidationError message formatting."""
        error = HookValidationError("Invalid field: tool_name")
        assert str(error) == "Invalid field: tool_name"

    def test_parse_error_message(self):
        """Test ParseError message formatting."""
        error = ParseError("Invalid JSON syntax")
        assert str(error) == "Invalid JSON syntax"

    def test_invalid_hook_type_error_message(self):
        """Test InvalidHookTypeError message formatting."""
        error = InvalidHookTypeError("Unknown hook type: CustomHook")
        assert str(error) == "Unknown hook type: CustomHook"


class TestExceptionBehavior:
    """Test exception behavior and usage patterns."""

    def test_cchooks_error_can_be_raised_and_caught(self):
        """Test that CCHooksError can be raised and caught."""
        with pytest.raises(CCHooksError) as exc_info:
            raise CCHooksError("Test error")
        assert str(exc_info.value) == "Test error"

    def test_specific_exceptions_can_be_caught_as_base(self):
        """Test that specific exceptions can be caught as CCHooksError."""

        with pytest.raises(CCHooksError):
            raise HookValidationError("Validation failed")

        with pytest.raises(CCHooksError):
            raise ParseError("Parse failed")

        with pytest.raises(CCHooksError):
            raise InvalidHookTypeError("Invalid type")

    def test_specific_exceptions_can_be_caught_individually(self):
        """Test that specific exceptions can be caught individually."""

        with pytest.raises(HookValidationError) as exc_info:
            raise HookValidationError("Validation failed")
        assert isinstance(exc_info.value, HookValidationError)

        with pytest.raises(ParseError) as exc_info:
            raise ParseError("Parse failed")
        assert isinstance(exc_info.value, ParseError)

        with pytest.raises(InvalidHookTypeError) as exc_info:
            raise InvalidHookTypeError("Invalid type")
        assert isinstance(exc_info.value, InvalidHookTypeError)


class TestExceptionAttributes:
    """Test exception attributes and properties."""

    def test_exception_args(self):
        """Test that exceptions properly store arguments."""
        error = CCHooksError("Test message", "additional_info")
        assert error.args == ("Test message", "additional_info")

    def test_exception_with_empty_message(self):
        """Test exception behavior with empty message."""
        error = CCHooksError("")
        assert str(error) == ""

    def test_exception_with_none_message(self):
        """Test exception behavior with None message."""
        error = CCHooksError(None)
        assert str(error) == "None"


class TestExceptionUsagePatterns:
    """Test common usage patterns for exceptions."""

    def test_hook_validation_error_with_field_info(self):
        """Test HookValidationError with field-specific information."""
        field_name = "tool_name"
        expected_value = "Write"
        actual_value = "write"

        error = HookValidationError(
            f"Invalid value for field '{field_name}': "
            f"expected '{expected_value}', got '{actual_value}'"
        )

        assert field_name in str(error)
        assert expected_value in str(error)
        assert actual_value in str(error)

    def test_parse_error_with_line_info(self):
        """Test ParseError with line and column information."""
        line_num = 3
        col_num = 15
        error_msg = "Unexpected character '}'"

        error = ParseError(
            f"JSON parsing failed at line {line_num}, column {col_num}: {error_msg}"
        )

        assert str(line_num) in str(error)
        assert str(col_num) in str(error)
        assert error_msg in str(error)

    def test_invalid_hook_type_error_with_suggestions(self):
        """Test InvalidHookTypeError with suggestions."""
        invalid_type = "PreTool"
        valid_types = ["PreToolUse", "PostToolUse"]

        error = InvalidHookTypeError(
            f"Invalid hook type '{invalid_type}'. "
            f"Valid types are: {', '.join(valid_types)}"
        )

        assert invalid_type in str(error)
        for valid_type in valid_types:
            assert valid_type in str(error)


class TestExceptionChaining:
    """Test exception chaining behavior."""

    def test_exception_with_cause(self):
        """Test exception chaining with __cause__."""
        original_error = ValueError("Original error")

        with pytest.raises(CCHooksError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise CCHooksError("Wrapped error") from e

        assert exc_info.value.__cause__ is original_error

    def test_exception_with_context(self):
        """Test exception chaining with __context__."""
        original_error = ValueError("Original error")

        try:
            raise original_error
        except ValueError:
            with pytest.raises(CCHooksError) as exc_info:
                raise CCHooksError("New error")

        assert exc_info.value.__context__ is original_error
