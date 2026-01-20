#!/usr/bin/env python3
"""[Hook Type] hook: [Brief description of what this hook does].

---META---
_schema_version: 1
required_skills: ['py-read', 'hooks-read']
---META---

[Detailed description of hook behavior, triggers, and outputs]

Hook type: [PreToolUse|PostToolUse|SessionStart|etc.]
Behavior: [Blocking|Advisory|Tracking]
"""

# =============================================================================
# SAFETY NET: These imports MUST be at module top (stdlib only, never fail)
# =============================================================================
import json
import sys


def _safe_main():
    """Main hook logic. All non-stdlib imports go here.

    This function contains all the actual hook logic. By putting imports
    inside this function, any import errors are caught by the safety net
    in the if __name__ == "__main__" block below.
    """
    from pathlib import Path

    # =========================================================================
    # PATH SETUP: Choose ONE of these patterns based on your hook location
    # =========================================================================

    # PATTERN A: For hooks in ~/.claude/hooks/production/
    # Uses the user's venv directly
    import glob
    venv_paths = glob.glob(str(Path.home() / ".claude/.venv/lib/python*/site-packages"))
    if venv_paths:
        sys.path.insert(0, venv_paths[0])

    # PATTERN B: For hooks in kitaekatt-plugins (uncomment if needed)
    # Uses the plugin cache
    # _cache_base = Path.home() / ".claude/plugins/cache/kitaekatt-plugins/cchooks"
    # _venv_paths = list(_cache_base.glob("*/.venv/lib/python*/site-packages"))
    # if _venv_paths:
    #     sys.path.insert(0, str(_venv_paths[0]))
    # _python_paths = list(_cache_base.glob("*/python"))
    # if _python_paths:
    #     sys.path.insert(0, str(_python_paths[0]))

    # =========================================================================
    # IMPORTS: cchooks and other dependencies
    # =========================================================================
    from cchooks import create_context, PreToolUseContext, handle_context_error

    # =========================================================================
    # HOOK LOGIC
    # =========================================================================
    try:
        context = create_context()

        # Type guard - adjust for your hook type
        if not isinstance(context, PreToolUseContext):
            context.output.allow()
            return

        # Your hook logic here...
        # Example: Check tool name
        tool_name = context.tool_name

        # Decision
        context.output.allow()

    except Exception as e:
        handle_context_error(e)


# =============================================================================
# ENTRY POINT: Safety net catches ALL errors including import failures
# =============================================================================
if __name__ == "__main__":
    try:
        _safe_main()
    except Exception as e:
        # Log error using stdlib only (no external dependencies)
        try:
            from pathlib import Path
            from datetime import datetime
            import traceback
            log_path = Path.home() / ".claude/tmp/hook-errors.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {__file__}: {e}\n{traceback.format_exc()}\n")
        except:
            pass  # Even logging failure shouldn't prevent JSON output

        # CRITICAL: Output valid JSON to prevent "hook error" message
        # Change to "block" and exit(2) for security-critical hooks
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)
