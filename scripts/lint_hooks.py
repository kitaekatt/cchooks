#!/usr/bin/env python3
"""Lint hooks for compliance with the safe hook pattern.

---META---
_schema_version: 1
required_skills: ['py-read', 'hooks-read']
---META---

Validates that hooks follow the self-protecting pattern that ensures
valid JSON output even when imports fail.

Usage:
    python lint_hooks.py <directory_or_file> [--verbose] [--fix-suggestions]

Checks:
    1. `import json` and `import sys` at module top (before other imports)
    2. `if __name__ == "__main__":` block exists
    3. Contains `try:` after `if __name__`
    4. Contains `except Exception` or `except:` in __main__ block
    5. Contains `print(json.dumps(` in except block
    6. Contains `sys.exit(0)` or `sys.exit(2)` in except block
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional


class LintResult(NamedTuple):
    """Result of linting a single hook file."""
    path: Path
    compliant: bool
    issues: List[str]
    suggestions: List[str]


def find_hook_files(path: Path) -> List[Path]:
    """Find all Python hook files in the given path."""
    if path.is_file():
        return [path] if path.suffix == ".py" else []

    # Recursively find .py files, excluding __pycache__, .venv, etc.
    hook_files = []
    exclude_dirs = {"__pycache__", ".venv", "venv", ".git", "node_modules", "dist", "build"}

    for py_file in path.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue
        hook_files.append(py_file)

    return sorted(hook_files)


def lint_hook(file_path: Path) -> LintResult:
    """Lint a single hook file for compliance."""
    issues = []
    suggestions = []

    try:
        content = file_path.read_text()
    except Exception as e:
        return LintResult(
            path=file_path,
            compliant=False,
            issues=[f"Could not read file: {e}"],
            suggestions=[]
        )

    lines = content.split("\n")

    # === Check 1: import json and import sys at module top ===
    # Find first non-comment, non-docstring, non-empty line that's an import
    in_docstring = False
    first_import_line = None
    json_import_line = None
    sys_import_line = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track docstrings
        if '"""' in stripped or "'''" in stripped:
            # Count quotes to determine if we're entering or exiting
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                in_docstring = not in_docstring
            continue

        if in_docstring:
            continue

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Check for imports
        if stripped.startswith("import ") or stripped.startswith("from "):
            if first_import_line is None:
                first_import_line = i

            if stripped == "import json" or stripped.startswith("import json "):
                json_import_line = i
            if stripped == "import sys" or stripped.startswith("import sys "):
                sys_import_line = i

    # Verify json and sys are imported at module level and early
    if json_import_line is None:
        issues.append("Missing `import json` at module top")
        suggestions.append("Add `import json` after shebang/docstring, before other imports")
    elif first_import_line is not None and json_import_line > first_import_line + 5:
        issues.append("`import json` should be among the first imports (found at line {})".format(json_import_line + 1))

    if sys_import_line is None:
        issues.append("Missing `import sys` at module top")
        suggestions.append("Add `import sys` after shebang/docstring, before other imports")
    elif first_import_line is not None and sys_import_line > first_import_line + 5:
        issues.append("`import sys` should be among the first imports (found at line {})".format(sys_import_line + 1))

    # === Check 2: if __name__ == "__main__": block exists ===
    main_block_match = re.search(r'^if\s+__name__\s*==\s*["\']__main__["\']\s*:', content, re.MULTILINE)
    if not main_block_match:
        issues.append('Missing `if __name__ == "__main__":` block')
        suggestions.append("Add entry point block at end of file")
        return LintResult(
            path=file_path,
            compliant=False,
            issues=issues,
            suggestions=suggestions
        )

    # Get content after __main__ block
    main_block_start = main_block_match.end()
    main_block_content = content[main_block_start:]

    # === Check 3: Contains try: in __main__ block ===
    # Look for try: that's indented (part of the __main__ block)
    try_match = re.search(r'^\s+try\s*:', main_block_content, re.MULTILINE)
    if not try_match:
        issues.append("Missing `try:` block in `__main__`")
        suggestions.append("Wrap main logic in try/except for safety")

    # === Check 4: Contains except Exception or except: ===
    except_match = re.search(r'^\s+except(\s+Exception|\s*:)', main_block_content, re.MULTILINE)
    if not except_match:
        issues.append("Missing `except Exception:` or `except:` in `__main__`")
        suggestions.append("Add except block to catch all errors")

    # === Check 5: Contains print(json.dumps( in except block ===
    # This is a bit tricky - we need to find it after an except
    json_output_pattern = r'print\s*\(\s*json\.dumps\s*\('
    if not re.search(json_output_pattern, main_block_content):
        issues.append("Missing `print(json.dumps(...))` for JSON output in `__main__`")
        suggestions.append('Add `print(json.dumps({"decision": "allow"}))` in except block')

    # === Check 6: Contains sys.exit(0) or sys.exit(2) ===
    exit_pattern = r'sys\.exit\s*\(\s*[02]\s*\)'
    if not re.search(exit_pattern, main_block_content):
        issues.append("Missing `sys.exit(0)` or `sys.exit(2)` in `__main__`")
        suggestions.append("Add `sys.exit(0)` for fail-open or `sys.exit(2)` for fail-closed")

    return LintResult(
        path=file_path,
        compliant=len(issues) == 0,
        issues=issues,
        suggestions=suggestions
    )


def main():
    parser = argparse.ArgumentParser(
        description="Lint hooks for compliance with safe hook pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s ~/.claude/hooks/production/
    %(prog)s my_hook.py --verbose
    %(prog)s . --fix-suggestions
        """
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Directory or file to lint"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed issues for each file"
    )
    parser.add_argument(
        "--fix-suggestions",
        action="store_true",
        help="Show suggestions for fixing issues"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show summary counts"
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)

    hook_files = find_hook_files(args.path)

    if not hook_files:
        print(f"No Python files found in: {args.path}")
        sys.exit(0)

    results: List[LintResult] = []
    for hook_file in hook_files:
        result = lint_hook(hook_file)
        results.append(result)

    # Output results
    compliant_count = sum(1 for r in results if r.compliant)
    non_compliant_count = len(results) - compliant_count

    if not args.summary_only:
        for result in results:
            if result.compliant:
                print(f"✓ {result.path.name} - compliant")
            else:
                print(f"✗ {result.path.name} - {len(result.issues)} issue(s)")
                if args.verbose:
                    for issue in result.issues:
                        print(f"    • {issue}")
                if args.fix_suggestions and result.suggestions:
                    print("    Suggestions:")
                    for suggestion in result.suggestions:
                        print(f"      → {suggestion}")

    # Summary
    print()
    print(f"Summary: {compliant_count}/{len(results)} hooks compliant")
    if non_compliant_count > 0:
        print(f"         {non_compliant_count} hooks need attention")
        sys.exit(1)
    else:
        print("         All hooks follow the safe pattern!")
        sys.exit(0)


if __name__ == "__main__":
    main()
