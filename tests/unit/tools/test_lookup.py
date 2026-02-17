"""Tests for lookup tools (issue types, priorities, users)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.tools.lookup.issue_types import IssueTypeListTool
from dtjiramcpserver.tools.lookup.priorities import PriorityListTool
from dtjiramcpserver.tools.lookup.users import UserSearchTool
from tests.conftest import EXPECTED_TOOL_COUNT


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for lookup tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked platform client."""
    return tool_cls(platform_client=client)


# --------------------------------------------------------------------------- #
# IssueTypeListTool
# --------------------------------------------------------------------------- #


class TestIssueTypeListTool:
    """Tests for issue_type_list tool."""

    class TestExecution:

        @pytest.mark.asyncio
        async def test_list_issue_types(self, platform_client: AsyncMock) -> None:
            """Returns all issue types from the flat array response."""
            platform_client.get.return_value = [
                {"id": "10001", "name": "Story", "subtask": False},
                {"id": "10002", "name": "Bug", "subtask": False},
                {"id": "10003", "name": "Sub-task", "subtask": True},
            ]
            tool = _make_tool(IssueTypeListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 3
            assert result.data[0]["name"] == "Story"

        @pytest.mark.asyncio
        async def test_calls_correct_endpoint(self, platform_client: AsyncMock) -> None:
            """Calls GET /issuetype."""
            platform_client.get.return_value = []
            tool = _make_tool(IssueTypeListTool, platform_client)
            await tool.safe_execute({})

            platform_client.get.assert_called_once_with("/issuetype")

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = IssueTypeListTool()
            guide = tool.get_guide()
            assert guide.name == "issue_type_list"
            assert guide.category == "lookup"
            assert len(guide.parameters) == 0

    class TestMutates:

        def test_not_mutating(self) -> None:
            assert IssueTypeListTool.mutates is False


# --------------------------------------------------------------------------- #
# PriorityListTool
# --------------------------------------------------------------------------- #


class TestPriorityListTool:
    """Tests for priority_list tool."""

    class TestExecution:

        @pytest.mark.asyncio
        async def test_list_priorities(self, platform_client: AsyncMock) -> None:
            """Returns paginated priorities."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[
                    {"id": "1", "name": "Highest"},
                    {"id": "2", "name": "High"},
                    {"id": "3", "name": "Medium"},
                ],
                start=0,
                limit=50,
                total=5,
                has_more=True,
            )
            tool = _make_tool(PriorityListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 3
            assert result.pagination["total"] == 5
            assert result.pagination["has_more"] is True

        @pytest.mark.asyncio
        async def test_pagination_forwarded(self, platform_client: AsyncMock) -> None:
            """start and limit are forwarded to list_paginated."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[],
                start=10,
                limit=5,
                total=0,
                has_more=False,
            )
            tool = _make_tool(PriorityListTool, platform_client)
            await tool.safe_execute({"start": 10, "limit": 5})

            call_args = platform_client.list_paginated.call_args
            assert call_args.kwargs["start"] == 10
            assert call_args.kwargs["limit"] == 5

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = PriorityListTool()
            guide = tool.get_guide()
            assert guide.name == "priority_list"
            assert guide.category == "lookup"
            assert len(guide.parameters) == 2

    class TestMutates:

        def test_not_mutating(self) -> None:
            assert PriorityListTool.mutates is False


# --------------------------------------------------------------------------- #
# UserSearchTool
# --------------------------------------------------------------------------- #


class TestUserSearchTool:
    """Tests for user_search tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_query(self, platform_client: AsyncMock) -> None:
            """Missing query returns VALIDATION_ERROR."""
            tool = _make_tool(UserSearchTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_query(self, platform_client: AsyncMock) -> None:
            """Empty query returns VALIDATION_ERROR."""
            tool = _make_tool(UserSearchTool, platform_client)
            result = await tool.safe_execute({"query": ""})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_search_users(self, platform_client: AsyncMock) -> None:
            """Returns users from search results."""
            platform_client.get.return_value = [
                {
                    "accountId": "abc123",
                    "displayName": "Jane Smith",
                    "emailAddress": "jane@example.com",
                    "active": True,
                },
            ]
            tool = _make_tool(UserSearchTool, platform_client)
            result = await tool.safe_execute({"query": "Jane"})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["displayName"] == "Jane Smith"

        @pytest.mark.asyncio
        async def test_pagination_estimated(self, platform_client: AsyncMock) -> None:
            """Pagination is estimated from result count."""
            platform_client.get.return_value = [
                {"accountId": f"user{i}"} for i in range(50)
            ]
            tool = _make_tool(UserSearchTool, platform_client)
            result = await tool.safe_execute({"query": "test"})

            assert result.pagination["has_more"] is True
            assert result.pagination["total"] == 50

        @pytest.mark.asyncio
        async def test_no_more_results(self, platform_client: AsyncMock) -> None:
            """When fewer results than limit, has_more is False."""
            platform_client.get.return_value = [
                {"accountId": "user1"},
                {"accountId": "user2"},
            ]
            tool = _make_tool(UserSearchTool, platform_client)
            result = await tool.safe_execute({"query": "test"})

            assert result.pagination["has_more"] is False

        @pytest.mark.asyncio
        async def test_query_forwarded(self, platform_client: AsyncMock) -> None:
            """Query is passed to the API as a parameter."""
            platform_client.get.return_value = []
            tool = _make_tool(UserSearchTool, platform_client)
            await tool.safe_execute({"query": "smith"})

            call_args = platform_client.get.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["query"] == "smith"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = UserSearchTool()
            guide = tool.get_guide()
            assert guide.name == "user_search"
            assert guide.category == "lookup"
            assert guide.parameters[0].name == "query"
            assert guide.parameters[0].required is True

    class TestMutates:

        def test_not_mutating(self) -> None:
            assert UserSearchTool.mutates is False


# --------------------------------------------------------------------------- #
# Registry integration
# --------------------------------------------------------------------------- #


class TestLookupToolRegistration:
    """Tests for lookup tool auto-discovery via registry."""

    def test_all_lookup_tools_discovered(self) -> None:
        """All 3 lookup tools are discovered by the registry."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        expected_names = {
            "issue_type_list",
            "priority_list",
            "user_search",
        }

        categories = registry.get_tools_by_category()
        assert "lookup" in categories
        lookup_names = {t.name for t in categories["lookup"]}
        assert expected_names == lookup_names

    def test_tool_count_includes_lookup(self) -> None:
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT
