"""Tests for NotificationContext and NotificationOutput."""

from unittest.mock import patch

import pytest

from cchooks.contexts.notification import NotificationContext
from cchooks.exceptions import HookValidationError


class TestNotificationContext:
    """Test NotificationContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Permission required for file modification",
        }

        context = NotificationContext(data)

        assert context.hook_event_name == "Notification"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.message == "Permission required for file modification"

    def test_context_with_different_message_types(self):
        """Test context with various message types."""
        messages = [
            "Permission required",
            "Operation completed successfully",
            "Warning: Large file detected",
            "Error: Network timeout",
            "Info: Auto-save enabled",
            "",  # Empty message
            "Message with special chars: @#$%^&*()",
            "Message with unicode: 你好世界 🌍",
        ]

        for message in messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert context.message == message

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "message",
                ],
            ),
            (
                {"hook_event_name": "Notification"},
                ["session_id", "transcript_path", "message"],
            ),
            (
                {"message": "test message"},
                ["session_id", "transcript_path", "hook_event_name"],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                NotificationContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg

    def test_context_with_extra_fields(self):
        """Test context creation with extra fields."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Test notification",
            "extra_field": "should_be_ignored",
            "priority": "high",
            "timestamp": 1234567890,
        }

        context = NotificationContext(data)

        # Should successfully create context
        assert context.hook_event_name == "Notification"
        assert context.message == "Test notification"


class TestNotificationOutput:
    """Test NotificationOutput functionality."""

    def test_simple_approve(self):
        """Test simple approve method (notification context only approves)."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Test notification",
        }

        context = NotificationContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.acknowledge("Notification processed")
            mock_exit.assert_called_once_with(0)

    def test_no_continue_method_available(self):
        """Test that notification context doesn't have continue methods."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Test notification",
        }

        context = NotificationContext(data)

        assert hasattr(context.output, "acknowledge")
        assert hasattr(context.output, "exit_block")
        assert not hasattr(context.output, "continue_approve")
        assert not hasattr(context.output, "continue_block")
        assert not hasattr(context.output, "continue_direct")


class TestNotificationRealWorldScenarios:
    """Test real-world notification scenarios."""

    def test_permission_notifications(self):
        """Test permission-related notifications."""
        permission_messages = [
            "Permission required: User needs to approve file modification in /etc/hosts",
            "Admin rights needed for system configuration changes",
            "Access denied: Insufficient permissions for /var/log/syslog",
            "User authorization required for Docker operations",
        ]

        for message in permission_messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert (
                "permission" in context.message.lower()
                or "access" in context.message.lower()
                or "rights" in context.message.lower()
                or "authorization" in context.message.lower()
            )

    def test_operation_status_notifications(self):
        """Test operation status notifications."""
        status_messages = [
            "Operation completed successfully",
            "File saved: /home/user/document.txt",
            "Build completed with warnings",
            "Test suite passed: 42/42 tests successful",
            "Deployment successful: v1.2.3 deployed to production",
        ]

        for message in status_messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert any(
                keyword in context.message.lower()
                for keyword in ["completed", "successful", "passed", "saved"]
            )

    def test_warning_notifications(self):
        """Test warning notifications."""
        warning_messages = [
            "Warning: Large file detected (>100MB)",
            "Caution: Potential security risk in command",
            "Warning: Deprecated API usage detected",
            "Alert: High memory usage during operation",
            "Warning: Network timeout occurred, retrying...",
        ]

        for message in warning_messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert any(
                keyword in context.message.lower()
                for keyword in ["warning", "caution", "alert", "risk"]
            )

    def test_error_notifications(self):
        """Test error notifications."""
        error_messages = [
            "Error: Network connection failed",
            "Failed to write file: Permission denied",
            "Docker build failed: Image not found",
            "Test failed: AssertionError in test_utils.py",
            "Error: Git repository not found",
        ]

        for message in error_messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert any(
                keyword in context.message.lower()
                for keyword in ["error", "failed", "exception"]
            )

    def test_system_notifications(self):
        """Test system-level notifications."""
        system_messages = [
            "Auto-save enabled: Files will be saved every 5 minutes",
            "Backup created: Automatic backup at 14:30",
            "System update available: Version 2.1.0 ready to install",
            "Disk space warning: Only 10% free space remaining",
            "Memory optimization: Cleared 500MB of cache",
        ]

        for message in system_messages:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert any(
                keyword in context.message.lower()
                for keyword in [
                    "auto",
                    "backup",
                    "update",
                    "warning",
                    "system",
                    "cache",
                ]
            )

    def test_empty_and_edge_case_messages(self):
        """Test edge cases for notification messages."""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "Message with \n newlines",
            "Message with \t tabs",
            "Message with \"quotes\" and 'apostrophes'",
            "Very long message " * 100,
            "Unicode: 你好世界 🌍 مرحبا بالعالم",
        ]

        for message in edge_cases:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": message,
            }

            context = NotificationContext(data)
            assert context.message == message

    def test_notification_processing_integration(self):
        """Test notification processing integration."""
        # Simulate processing different types of notifications
        notifications = [
            {
                "message": "Permission required: Write access to /etc/hosts",
                "handler": "permission_handler",
            },
            {
                "message": "Auto-formatting applied: /project/src/main.py",
                "handler": "formatting_handler",
            },
            {"message": "Build completed: 42 tests passed", "handler": "build_handler"},
        ]

        for notification in notifications:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": notification["message"],
            }

            context = NotificationContext(data)

            # Test that notification can be processed
            assert context.message == notification["message"]

            # Test simple approve (notification hooks always approve)
            with patch("sys.exit") as mock_exit:
                context.output.acknowledge("success")
                mock_exit.assert_called_once_with(0)

    def test_notification_with_type(self):
        """Test notification with notification_type field."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Permission required for file modification",
            "notification_type": "permission_prompt",
        }

        context = NotificationContext(data)

        assert context.hook_event_name == "Notification"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.message == "Permission required for file modification"
        assert context.notification_type == "permission_prompt"

    def test_notification_without_type(self):
        """Test notification without notification_type field (backward compatibility)."""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "message": "Operation completed successfully",
        }

        context = NotificationContext(data)

        assert context.hook_event_name == "Notification"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.message == "Operation completed successfully"
        assert context.notification_type is None

    def test_notification_types_variations(self):
        """Test various notification types."""
        notification_types = [
            "permission_prompt",
            "idle_prompt",
            "auth_success",
            "elicitation_dialog",
            "custom_type",
        ]

        for notification_type in notification_types:
            data = {
                "hook_event_name": "Notification",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "message": f"Test message for {notification_type}",
                "notification_type": notification_type,
            }

            context = NotificationContext(data)
            assert context.notification_type == notification_type
