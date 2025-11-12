"""Integration tests for real-world cchooks usage scenarios."""

import json
from io import StringIO
from unittest.mock import patch

from cchooks import create_context
from cchooks.contexts import (
    PreToolUseContext,
    PostToolUseContext,
    NotificationContext,
    UserPromptSubmitContext,
    StopContext,
    SubagentStopContext,
    PreCompactContext,
    SessionStartContext,
)


class TestRealWorldSecurityScenarios:
    """Test real-world security-focused scenarios."""

    def test_sensitive_file_protection_workflow(self):
        """Test complete workflow for protecting sensitive files."""
        # Test 1: Block write to /etc/passwd
        sensitive_write_data = {
            "hook_event_name": "PreToolUse",
            "session_id": "security-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/etc/passwd",
                "content": "malicious_user:x:0:0:root:/root:/bin/bash",
            },
        }

        test_input = StringIO(json.dumps(sensitive_write_data))
        context = create_context(test_input)
        assert isinstance(context, PreToolUseContext)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Blocking write to system file /etc/passwd")
            mock_exit.assert_called_once_with(2)

    def test_config_file_approval_workflow(self):
        """Test config file modification approval workflow."""
        # Test 2: Approve safe config file write
        safe_config_data = {
            "hook_event_name": "PreToolUse",
            "session_id": "config-session-456",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/home/user/project/.env.example",
                "content": "API_KEY=your_api_key_here\nDEBUG=false",
            },
        }

        test_input = StringIO(json.dumps(safe_config_data))
        context = create_context(test_input)
        assert isinstance(context, PreToolUseContext)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Safe config file write approved")
            mock_exit.assert_called_once_with(0)

    def test_bash_command_safety_check(self):
        """Test bash command safety validation."""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /var/log",
            "mkfs.ext4 /dev/sda1",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",  # Fork bomb
        ]

        for command in dangerous_commands:
            bash_data = {
                "hook_event_name": "PreToolUse",
                "session_id": f"bash-session-{hash(command) % 1000}",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "tool_name": "Bash",
                "tool_input": {
                    "command": command,
                    "description": "Potentially dangerous system command",
                },
            }

            test_input = StringIO(json.dumps(bash_data))
            context = create_context(test_input)
            assert isinstance(context, PreToolUseContext)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                context.output.deny(f"Dangerous command detected: {command}")

                output = mock_stdout.getvalue().strip()
                result = json.loads(output)
                assert result["continue"] is True
                assert (
                    "Dangerous command"
                    in result["hookSpecificOutput"]["permissionDecisionReason"]
                )


class TestRealWorldDevelopmentWorkflows:
    """Test real-world development workflow scenarios."""

    def test_python_auto_formatting_workflow(self):
        """Test Python file auto-formatting after write."""
        # Step 1: Write Python file
        write_data = {
            "hook_event_name": "PostToolUse",
            "session_id": "dev-session-789",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/project/src/utils.py",
                "content": "def hello():\n    print('hello')\n",
            },
            "tool_response": {
                "success": True,
                "content": "Python file written successfully",
            },
        }

        test_input = StringIO(json.dumps(write_data))
        context = create_context(test_input)
        assert isinstance(context, PostToolUseContext)

        # Check if it's a Python file
        file_path = context.tool_input["file_path"]
        assert file_path.endswith(".py")

        # Allow processing to continue (for auto-formatting)
        context.output.accept(suppress_output=True)

    def test_build_notification_workflow(self):
        """Test build completion notification workflow."""
        build_notification_data = {
            "hook_event_name": "Notification",
            "session_id": "build-session-101",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Build completed successfully: 42 tests passed, 0 failed",
        }

        test_input = StringIO(json.dumps(build_notification_data))
        context = create_context(test_input)
        assert isinstance(context, NotificationContext)

        # Process notification
        assert "Build completed" in context.message
        assert "42 tests passed" in context.message

    def test_error_handling_workflow(self):
        """Test error handling and recovery workflow."""
        error_data = {
            "hook_event_name": "PostToolUse",
            "session_id": "error-session-202",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/protected/system.log",
                "content": "test log entry",
            },
            "tool_response": {
                "success": False,
                "error": "Permission denied: /protected/system.log",
            },
        }

        test_input = StringIO(json.dumps(error_data))
        context = create_context(test_input)
        assert isinstance(context, PostToolUseContext)

        # Handle error gracefully
        assert context.tool_response["success"] is False
        assert "Permission denied" in context.tool_response["error"]


class TestRealWorldConversationManagement:
    """Test real-world conversation management scenarios."""

    def test_stop_with_pending_tasks(self):
        """Test stopping behavior with pending tasks."""
        stop_data = {
            "hook_event_name": "Stop",
            "session_id": "conversation-303",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "stop_hook_active": False,  # Indicates pending tasks
        }

        test_input = StringIO(json.dumps(stop_data))
        context = create_context(test_input)
        assert isinstance(context, StopContext)
        assert context.stop_hook_active is False

        # Prevent stop due to pending tasks
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.prevent("Pending deployment tasks not completed")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is True
            assert "Pending deployment tasks" in result["reason"]

    def test_subagent_workflow_completion(self):
        """Test subagent workflow completion management."""
        subagent_stop_data = {
            "hook_event_name": "SubagentStop",
            "session_id": "subagent-404",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "stop_hook_active": True,  # Indicates completion
        }

        test_input = StringIO(json.dumps(subagent_stop_data))
        context = create_context(test_input)
        assert isinstance(context, SubagentStopContext)
        assert context.stop_hook_active is True

        # Allow subagent to stop
        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Code analysis subagent completed successfully")
            mock_exit.assert_called_once_with(0)

    def test_transcript_compaction_workflow(self):
        """Test transcript compaction workflow."""
        compaction_data = {
            "hook_event_name": "PreCompact",
            "session_id": "compaction-505",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "trigger": "auto",
            "custom_instructions": "Preserve security decisions and error messages",
        }

        test_input = StringIO(json.dumps(compaction_data))
        context = create_context(test_input)
        assert isinstance(context, PreCompactContext)
        assert context.trigger == "auto"
        assert "security decisions" in context.custom_instructions

        # Approve compaction with custom rules
        with patch("sys.exit") as mock_exit:
            context.output.acknowledge("Auto-compaction with security preservation")
            mock_exit.assert_called_once_with(0)


class TestRealWorldIntegrationScenarios:
    """Test complete real-world integration scenarios."""

    def test_complete_deployment_workflow(self):
        """Test complete deployment workflow with multiple hooks."""
        workflow_steps = [
            # Step 1: Check deployment script safety
            {
                "type": "PreToolUse",
                "data": {
                    "hook_event_name": "PreToolUse",
                    "session_id": "deploy-workflow-1",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": "./deploy.sh production",
                        "description": "Deploy to production environment",
                    },
                },
                "expected": "approve",
            },
            # Step 2: Log deployment success
            {
                "type": "PostToolUse",
                "data": {
                    "hook_event_name": "PostToolUse",
                    "session_id": "deploy-workflow-2",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": "./deploy.sh production",
                        "description": "Deploy to production environment",
                    },
                    "tool_response": {
                        "success": True,
                        "content": "Deployment completed successfully",
                    },
                },
                "expected": "continue",
            },
            # Step 3: Notify completion
            {
                "type": "Notification",
                "data": {
                    "hook_event_name": "Notification",
                    "session_id": "deploy-workflow-3",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "message": "Production deployment v2.1.0 completed successfully",
                },
                "expected": "process",
            },
        ]

        for step in workflow_steps:
            test_input = StringIO(json.dumps(step["data"]))
            context = create_context(test_input)

            # Verify context type
            expected_type = step["type"]
            if expected_type == "PreToolUse":
                assert isinstance(context, PreToolUseContext)
            elif expected_type == "PostToolUse":
                assert isinstance(context, PostToolUseContext)
            elif expected_type == "Notification":
                assert isinstance(context, NotificationContext)
            elif expected_type == "UserPromptSubmit":
                assert isinstance(context, UserPromptSubmitContext)

    def test_security_audit_workflow(self):
        """Test security audit workflow."""
        audit_scenarios = [
            {
                "description": "Block sensitive file access",
                "file_path": "/etc/shadow",
                "action": "read",
                "expected": "block",
            },
            {
                "description": "Allow safe config read",
                "file_path": "/home/user/project/config.json",
                "action": "read",
                "expected": "approve",
            },
            {
                "description": "Block dangerous command",
                "command": "sudo cat /etc/shadow",
                "action": "write",
                "expected": "block",
            },
        ]

        for scenario in audit_scenarios:
            if scenario["action"] == "read":
                data = {
                    "hook_event_name": "PreToolUse",
                    "session_id": "audit-session",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": "Read",
                    "tool_input": {"file_path": scenario["file_path"]},
                }
            else:  # bash command
                data = {
                    "hook_event_name": "PreToolUse",
                    "session_id": "audit-session",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": "Bash",
                    "tool_input": {
                        "command": scenario["command"],
                        "description": "Security audit command",
                    },
                }

            test_input = StringIO(json.dumps(data))
            context = create_context(test_input)
            assert isinstance(context, PreToolUseContext)

            if scenario["expected"] == "block":
                with patch("sys.exit") as mock_exit:
                    context.output.exit_block(
                        f"Security policy: {scenario['description']}"
                    )
                    mock_exit.assert_called_once_with(2)
            else:
                with patch("sys.exit") as mock_exit:
                    context.output.exit_success("Security audit approved")
                    mock_exit.assert_called_once_with(0)

    def test_development_cycle_workflow(self):
        """Test complete development cycle workflow."""
        dev_cycle = [
            # 1. User submits prompt
            {
                "hook": "UserPromptSubmit",
                "prompt": "Please help me write a Python function to calculate fibonacci numbers",
                "expected": "allow",
            },
            # 2. Write code
            {
                "hook": "PreToolUse",
                "tool": "Write",
                "input": {
                    "file_path": "/project/src/main.py",
                    "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                },
                "expected": "approve",
            },
            # 3. Auto-format Python file
            {
                "hook": "PostToolUse",
                "tool": "Write",
                "input": {
                    "file_path": "/project/src/main.py",
                    "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                },
                "response": {"success": True, "content": "File written"},
                "expected": "continue",
            },
            # 4. Run tests
            {
                "hook": "PreToolUse",
                "tool": "Bash",
                "input": {"command": "pytest tests/", "description": "Run test suite"},
                "expected": "approve",
            },
            # 5. Test results notification
            {
                "hook": "Notification",
                "message": "Test suite passed: 15/15 tests successful",
                "expected": "process",
            },
            # 6. Stop conversation
            {"hook": "Stop", "stop_hook_active": True, "expected": "allow"},
        ]

        for step in dev_cycle:
            if step["hook"] == "PreToolUse":
                data = {
                    "hook_event_name": "PreToolUse",
                    "session_id": "dev-cycle",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": step["tool"],
                    "tool_input": step["input"],
                }
            elif step["hook"] == "PostToolUse":
                data = {
                    "hook_event_name": "PostToolUse",
                    "session_id": "dev-cycle",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": step["tool"],
                    "tool_input": step["input"],
                    "tool_response": step["response"],
                }
            elif step["hook"] == "Notification":
                data = {
                    "hook_event_name": "Notification",
                    "session_id": "dev-cycle",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "message": step["message"],
                }
            elif step["hook"] == "UserPromptSubmit":
                data = {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "dev-cycle",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "prompt": step["prompt"],
                }
            else:
                data = {
                    "hook_event_name": "Stop",
                    "session_id": "dev-cycle",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "stop_hook_active": step["stop_hook_active"],
                }

            test_input = StringIO(json.dumps(data))
            context = create_context(test_input)

            # Basic validation that context was created
            assert context is not None
            assert hasattr(context, "hook_event_name")


class TestSessionStartIntegrationScenarios:
    """Test SessionStart hook integration scenarios."""

    def test_startup_context_loading(self):
        """Test loading development context on startup."""
        startup_data = {
            "hook_event_name": "SessionStart",
            "session_id": "startup-session-123",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        test_input = StringIO(json.dumps(startup_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)
        assert context.source == "startup"

        # Load project context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            project_context = """
Project: Web Application Framework
Language: Python 3.12
Framework: FastAPI
Database: PostgreSQL
Recent Changes:
- Added user authentication endpoints
- Fixed CORS configuration
- Updated API documentation
Open Issues: 5 (3 bugs, 2 features)
"""
            context.output.add_context(project_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is True
            assert (
                "Web Application Framework"
                in result["hookSpecificOutput"]["additionalContext"]
            )

    def test_resume_session_context(self):
        """Test resuming session with previous context."""
        resume_data = {
            "hook_event_name": "SessionStart",
            "session_id": "resume-session-456",
            "transcript_path": "/tmp/transcript.json",
            "source": "resume",
        }

        test_input = StringIO(json.dumps(resume_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)
        assert context.source == "resume"

        # Provide resume context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            resume_context = "Resuming work on OAuth2 implementation. Last task: Testing refresh token flow."
            context.output.add_context(resume_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == resume_context

    def test_clear_session_fresh_start(self):
        """Test fresh start after session clear."""
        clear_data = {
            "hook_event_name": "SessionStart",
            "session_id": "clear-session-789",
            "transcript_path": "/tmp/transcript.json",
            "source": "clear",
        }

        test_input = StringIO(json.dumps(clear_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)
        assert context.source == "clear"

        # Provide fresh context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            fresh_context = (
                "New session started. Current working directory: /home/user/project"
            )
            context.output.add_context(fresh_context)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == fresh_context

    def test_git_repository_context_loading(self):
        """Test loading git repository context on startup."""
        git_context_data = {
            "hook_event_name": "SessionStart",
            "session_id": "git-session-101",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        test_input = StringIO(json.dumps(git_context_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)

        # Load git context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            git_info = """
Git Repository: my-webapp
Current Branch: feature/user-auth
Recent Commits:
- feat: Add JWT authentication (HEAD)
- fix: Resolve login validation bug
- docs: Update API documentation
- style: Format code with black
Modified Files: src/auth/, tests/test_auth.py
Open Pull Requests: 2
"""
            context.output.add_context(git_info)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert (
                "Git Repository:" in result["hookSpecificOutput"]["additionalContext"]
            )
            assert (
                "feature/user-auth" in result["hookSpecificOutput"]["additionalContext"]
            )

    def test_development_environment_context(self):
        """Test loading development environment context."""
        env_context_data = {
            "hook_event_name": "SessionStart",
            "session_id": "env-session-202",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        test_input = StringIO(json.dumps(env_context_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)

        # Load environment context
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            env_info = """
Development Environment:
- Python: 3.12.0 (venv active)
- Node.js: 18.17.0
- Database: PostgreSQL 14.7 (localhost:5432)
- Redis: 7.0.5 (localhost:6379)
- Docker: 24.0.5
- Testing Framework: pytest with coverage
- Code Quality: ruff, mypy, black
"""
            context.output.add_context(env_info)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert (
                "Development Environment:"
                in result["hookSpecificOutput"]["additionalContext"]
            )
            assert "Python: 3.12.0" in result["hookSpecificOutput"]["additionalContext"]

    def test_error_handling_session_start(self):
        """Test error handling in SessionStart hooks."""
        error_context_data = {
            "hook_event_name": "SessionStart",
            "session_id": "error-session-303",
            "transcript_path": "/tmp/transcript.json",
            "source": "startup",
        }

        test_input = StringIO(json.dumps(error_context_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)

        # Test error handling
        with patch("sys.exit") as mock_exit:
            context.output.exit_non_block("Failed to load git repository context")
            mock_exit.assert_called_once_with(1)

    def test_session_start_with_suppressed_output(self):
        """Test SessionStart with suppressed output for cleaner transcript."""
        suppressed_data = {
            "hook_event_name": "SessionStart",
            "session_id": "suppressed-session-404",
            "transcript_path": "/tmp/transcript.json",
            "source": "resume",
        }

        test_input = StringIO(json.dumps(suppressed_data))
        context = create_context(test_input)
        assert isinstance(context, SessionStartContext)

        # Test suppressed output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            internal_context = "Internal session data loaded successfully"
            context.output.add_context(internal_context, suppress_output=True)

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["hookSpecificOutput"]["additionalContext"] == internal_context

    def test_complete_session_lifecycle(self):
        """Test complete session lifecycle with SessionStart."""
        session_lifecycle = [
            # 1. Session startup with context loading
            {
                "hook": "SessionStart",
                "source": "startup",
                "context": "Loading project: E-commerce platform\nTech stack: Python, FastAPI, PostgreSQL",
                "expected": "load_context",
            },
            # 2. User prompt submission
            {
                "hook": "UserPromptSubmit",
                "prompt": "Help me implement user registration",
                "expected": "allow",
            },
            # 3. Tool usage (write code)
            {
                "hook": "PreToolUse",
                "tool": "Write",
                "input": {
                    "file_path": "/project/src/auth/registration.py",
                    "content": "def register_user(email, password):\n    pass",
                },
                "expected": "approve",
            },
            # 4. Session resume
            {
                "hook": "SessionStart",
                "source": "resume",
                "context": "Resuming work on user registration. Current task: Implement password validation.",
                "expected": "load_context",
            },
        ]

        for step in session_lifecycle:
            if step["hook"] == "SessionStart":
                data = {
                    "hook_event_name": "SessionStart",
                    "session_id": "lifecycle-session",
                    "transcript_path": "/tmp/transcript.json",
                    "source": step["source"],
                }
            elif step["hook"] == "UserPromptSubmit":
                data = {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "lifecycle-session",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "prompt": step["prompt"],
                }
            elif step["hook"] == "PreToolUse":
                data = {
                    "hook_event_name": "PreToolUse",
                    "session_id": "lifecycle-session",
                    "transcript_path": "/tmp/transcript.json",
                    "cwd": "/home/user/project",
                    "tool_name": step["tool"],
                    "tool_input": step["input"],
                }

            test_input = StringIO(json.dumps(data))
            context = create_context(test_input)

            # Basic validation
            assert context is not None
            assert hasattr(context, "hook_event_name")

            # For SessionStart, test context loading
            if step["hook"] == "SessionStart":
                assert isinstance(context, SessionStartContext)
                if step["expected"] == "load_context":
                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                        context.output.add_context(step["context"])
                        output = mock_stdout.getvalue().strip()
                        result = json.loads(output)
                        assert result["continue"] is True
                        assert (
                            result["hookSpecificOutput"]["hookEventName"]
                            == "SessionStart"
                        )
