"""Tests for read-only mode filtering."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.config.models import JiraConfig
from dtjiramcpserver.tools.registry import ToolRegistry
from tests.conftest import EXPECTED_TOOL_COUNT

# Number of read-only (non-mutating) tools.
# Total 61 - 23 mutating = 38 read-only.
EXPECTED_READ_ONLY_COUNT = 38

# Known mutating tools (23 total)
MUTATING_TOOL_NAMES = {
    # Issues (4)
    "issue_create",
    "issue_update",
    "issue_transition",
    "issue_delete",
    # Service Desk (4)
    "servicedesk_add_customers",
    "servicedesk_remove_customers",
    "servicedesk_add_organisation",
    "servicedesk_remove_organisation",
    # Request Types (2)
    "requesttype_create",
    "requesttype_delete",
    # Fields (4)
    "field_create",
    "field_update",
    "field_add_context",
    "screen_add_field",
    # Workflows (2)
    "workflow_create",
    "status_create",
    # Projects (3)
    "project_create",
    "project_update",
    "project_delete",
    # Groups (4)
    "group_create",
    "group_delete",
    "group_add_user",
    "group_remove_user",
}


class TestReadOnlyMode:
    """Tests for JIRA_READ_ONLY registry filtering."""

    def test_default_not_read_only(self) -> None:
        """Registry defaults to read_only=False."""
        registry = ToolRegistry()
        assert registry.read_only is False

    def test_all_tools_in_normal_mode(self) -> None:
        """Normal mode registers all tools."""
        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT

    def test_read_only_excludes_mutating(self) -> None:
        """Read-only mode excludes all mutating tools."""
        registry = ToolRegistry(read_only=True)
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_READ_ONLY_COUNT

    def test_read_only_preserves_read_tools(self) -> None:
        """Read-only mode preserves all read-only tools."""
        normal = ToolRegistry()
        normal.discover_and_register()

        readonly = ToolRegistry(read_only=True)
        readonly.discover_and_register()

        # All tools in read-only should exist in normal
        readonly_names = {t.name for t in readonly.list_tools()}
        normal_names = {t.name for t in normal.list_tools()}
        assert readonly_names.issubset(normal_names)

    def test_no_mutating_tools_in_read_only(self) -> None:
        """No mutating tool appears in read-only registry."""
        registry = ToolRegistry(read_only=True)
        registry.discover_and_register()

        registered_names = {t.name for t in registry.list_tools()}
        for mutating_name in MUTATING_TOOL_NAMES:
            assert mutating_name not in registered_names, (
                f"Mutating tool '{mutating_name}' found in read-only registry"
            )

    def test_all_mutating_tools_present_in_normal(self) -> None:
        """All known mutating tools are registered in normal mode."""
        registry = ToolRegistry()
        registry.discover_and_register()

        registered_names = {t.name for t in registry.list_tools()}
        for mutating_name in MUTATING_TOOL_NAMES:
            assert mutating_name in registered_names, (
                f"Mutating tool '{mutating_name}' not found in normal registry"
            )

    def test_mutating_tool_count_matches(self) -> None:
        """The difference between normal and read-only is exactly the mutating count."""
        normal = ToolRegistry()
        normal.discover_and_register()

        readonly = ToolRegistry(read_only=True)
        readonly.discover_and_register()

        assert normal.tool_count - readonly.tool_count == len(MUTATING_TOOL_NAMES)

    def test_read_only_property(self) -> None:
        """The read_only property reflects the configured value."""
        readonly = ToolRegistry(read_only=True)
        assert readonly.read_only is True

        normal = ToolRegistry(read_only=False)
        assert normal.read_only is False

    def test_config_read_only_default(self) -> None:
        """JiraConfig.read_only defaults to False."""
        config = JiraConfig(
            instance_url="https://test.atlassian.net",
            user_email="test@example.com",
            api_token="test-token",
        )
        assert config.read_only is False

    def test_get_tools_by_category_filtered(self) -> None:
        """Category listing reflects read-only filtering."""
        readonly = ToolRegistry(read_only=True)
        readonly.discover_and_register()
        categories = readonly.get_tools_by_category()

        # Issues category should exist but with only read-only tools
        if "issues" in categories:
            issue_names = {t.name for t in categories["issues"]}
            assert "issue_create" not in issue_names
            assert "issue_get" in issue_names
