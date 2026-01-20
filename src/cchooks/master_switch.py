"""Master switch check for global hook enable/disable.

This module provides functionality to check if hooks are globally disabled
via the master switch in ~/.claude/hooks/config/hook-categories.yaml.

When hooks_enabled: false, all hooks should silently allow/pass without
executing their logic.
"""

import sys
from pathlib import Path
from typing import NoReturn, Optional

# Path to the hook categories config file
_HOOK_CATEGORIES_PATH = Path.home() / ".claude" / "hooks" / "config" / "hook-categories.yaml"


def _check_master_switch_enabled() -> bool:
    """Check if hooks are enabled via the master switch.

    Returns:
        True if hooks are enabled (or config doesn't exist/can't be read),
        False if hooks are explicitly disabled.

    Note:
        Defaults to True (enabled) if:
        - Config file doesn't exist
        - Config file can't be read
        - Config file has no hooks_enabled key
        - Any error occurs during parsing

        This fail-open behavior ensures hooks work by default and only
        disable when explicitly configured.
    """
    if not _HOOK_CATEGORIES_PATH.exists():
        return True

    try:
        # Simple YAML parsing for just the hooks_enabled key
        # Avoids importing pyyaml to keep dependencies minimal
        with open(_HOOK_CATEGORIES_PATH, "r") as f:
            for line in f:
                # Strip whitespace and skip comments/empty lines
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                # Look for hooks_enabled key at root level (no leading whitespace)
                if line.startswith("hooks_enabled:"):
                    # Extract value after colon
                    value = stripped.split(":", 1)[1].strip().lower()
                    # Check for false/no values
                    if value in ("false", "no", "off", "0"):
                        return False
                    # Any other value (true, yes, on, 1, or anything else) means enabled
                    return True

        # Key not found, default to enabled
        return True

    except Exception:
        # On any error, default to enabled (fail-open)
        return True


def exit_if_hooks_disabled() -> Optional[NoReturn]:
    """Exit early with success if hooks are globally disabled.

    This should be called early in hook execution. If hooks are disabled,
    it outputs nothing and exits with code 0 (success/allow).

    Returns:
        None if hooks are enabled (hook should continue execution)
        NoReturn (exits) if hooks are disabled
    """
    if not _check_master_switch_enabled():
        # Exit cleanly with no output - this allows the operation to proceed
        sys.exit(0)
    return None


def are_hooks_enabled() -> bool:
    """Check if hooks are enabled via the master switch.

    This is a public API for hooks that want to check the master switch
    without exiting.

    Returns:
        True if hooks are enabled, False if disabled.
    """
    return _check_master_switch_enabled()
