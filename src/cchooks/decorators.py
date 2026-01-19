"""Hook decorators for safe execution.

Provides decorators that wrap hook functions to ensure:
1. All exceptions are logged to ~/.claude/tmp/hook-errors.log
2. Valid JSON is always output to stdout (prevents "hook error")
3. Appropriate exit codes are used
"""

import json
import sys
from functools import wraps
from typing import Callable, TypeVar

from .output_utils import _log_error_to_file

F = TypeVar('F', bound=Callable)


def safe_hook_wrapper(fail_open: bool = True) -> Callable[[F], F]:
    """Decorator ensuring hooks always output valid JSON on failure.

    Wraps a hook's main() function to catch any exception and:
    1. Log error to ~/.claude/tmp/hook-errors.log
    2. Output valid JSON to stdout (prevents "hook error" message)
    3. Exit with appropriate code

    This catches errors that occur before handle_context_error() can be
    reached, such as import errors or create_context() failures.

    Args:
        fail_open: If True, allow tool execution on error (exit 0).
                   If False, block tool execution on error (exit 2).
                   Default is True for safety - hooks should not block
                   Claude when they themselves are broken.

    Usage:
        from cchooks import safe_hook_wrapper, create_context

        @safe_hook_wrapper(fail_open=True)
        def main():
            context = create_context()
            # ... hook logic ...
            context.output.allow()

        if __name__ == "__main__":
            main()

    Note:
        The decorator should wrap main(), not individual functions.
        It's designed to be the outermost error boundary for the hook.
    """
    def decorator(hook_func: F) -> F:
        @wraps(hook_func)
        def wrapper(*args, **kwargs):
            try:
                return hook_func(*args, **kwargs)
            except Exception as e:
                # Log error to file for visibility
                hook_file = getattr(hook_func, '__code__', None)
                hook_name = hook_file.co_filename if hook_file else "unknown"
                _log_error_to_file(
                    hook_name=hook_name,
                    error=e,
                    hook_type="wrapper_caught"
                )

                # Output valid JSON to prevent Claude Code "hook error"
                decision = "allow" if fail_open else "block"
                print(json.dumps({"decision": decision}), file=sys.stdout)
                sys.exit(0 if fail_open else 2)
        return wrapper  # type: ignore
    return decorator
