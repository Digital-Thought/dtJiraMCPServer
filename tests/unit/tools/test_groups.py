"""Tests for group management tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.exceptions import NotFoundError
from dtjiramcpserver.tools.groups.groups import (
    GroupCreateTool,
    GroupDeleteTool,
    GroupListTool,
)
from dtjiramcpserver.tools.groups.members import (
    GroupAddUserTool,
    GroupGetMembersTool,
    GroupRemoveUserTool,
)
from tests.conftest import EXPECTED_TOOL_COUNT


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for group tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked platform client."""
    return tool_cls(platform_client=client)


# --------------------------------------------------------------------------- #
# GroupListTool
# --------------------------------------------------------------------------- #


class TestGroupListTool:
    """Tests for group_list tool."""

    class TestExecution:

        @pytest.mark.asyncio
        async def test_list_groups(self, platform_client: AsyncMock) -> None:
            """Returns paginated groups."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[
                    {"name": "jira-administrators", "groupId": "abc123"},
                    {"name": "developers", "groupId": "def456"},
                ],
                start=0,
                limit=50,
                total=2,
                has_more=False,
            )
            tool = _make_tool(GroupListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2

        @pytest.mark.asyncio
        async def test_calls_bulk_endpoint(self, platform_client: AsyncMock) -> None:
            """Uses /group/bulk endpoint."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[], start=0, limit=50, total=0, has_more=False,
            )
            tool = _make_tool(GroupListTool, platform_client)
            await tool.safe_execute({})

            call_args = platform_client.list_paginated.call_args
            assert call_args[0][0] == "/group/bulk"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupListTool()
            guide = tool.get_guide()
            assert guide.name == "group_list"
            assert guide.category == "groups"

    class TestMutates:

        def test_not_mutating(self) -> None:
            assert GroupListTool.mutates is False


# --------------------------------------------------------------------------- #
# GroupGetMembersTool
# --------------------------------------------------------------------------- #


class TestGroupGetMembersTool:
    """Tests for group_get_members tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_group_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupGetMembersTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_get_members(self, platform_client: AsyncMock) -> None:
            """Returns paginated group members."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[
                    {
                        "accountId": "abc123",
                        "displayName": "Jane Smith",
                        "active": True,
                    },
                ],
                start=0,
                limit=50,
                total=1,
                has_more=False,
            )
            tool = _make_tool(GroupGetMembersTool, platform_client)
            result = await tool.safe_execute({"group_name": "developers"})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["displayName"] == "Jane Smith"

        @pytest.mark.asyncio
        async def test_group_name_forwarded(self, platform_client: AsyncMock) -> None:
            """Group name is passed as extra_params."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[], start=0, limit=50, total=0, has_more=False,
            )
            tool = _make_tool(GroupGetMembersTool, platform_client)
            await tool.safe_execute({"group_name": "jira-administrators"})

            call_args = platform_client.list_paginated.call_args
            assert call_args.kwargs["extra_params"]["groupname"] == "jira-administrators"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupGetMembersTool()
            guide = tool.get_guide()
            assert guide.name == "group_get_members"
            assert guide.parameters[0].name == "group_name"
            assert guide.parameters[0].required is True

    class TestMutates:

        def test_not_mutating(self) -> None:
            assert GroupGetMembersTool.mutates is False


# --------------------------------------------------------------------------- #
# GroupCreateTool
# --------------------------------------------------------------------------- #


class TestGroupCreateTool:
    """Tests for group_create tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupCreateTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupCreateTool, platform_client)
            result = await tool.safe_execute({"name": ""})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_create_group(self, platform_client: AsyncMock) -> None:
            platform_client.post.return_value = {
                "name": "new-group",
                "groupId": "abc123",
            }
            tool = _make_tool(GroupCreateTool, platform_client)
            result = await tool.safe_execute({"name": "new-group"})

            assert result.success is True
            assert result.data["name"] == "new-group"

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["name"] == "new-group"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert GroupCreateTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupCreateTool()
            guide = tool.get_guide()
            assert guide.name == "group_create"
            assert guide.parameters[0].name == "name"
            assert guide.parameters[0].required is True


# --------------------------------------------------------------------------- #
# GroupAddUserTool
# --------------------------------------------------------------------------- #


class TestGroupAddUserTool:
    """Tests for group_add_user tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_group_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupAddUserTool, platform_client)
            result = await tool.safe_execute({"account_id": "abc123"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_account_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupAddUserTool, platform_client)
            result = await tool.safe_execute({"group_name": "developers"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_add_user(self, platform_client: AsyncMock) -> None:
            platform_client.post.return_value = {
                "accountId": "abc123",
                "displayName": "Jane Smith",
            }
            tool = _make_tool(GroupAddUserTool, platform_client)
            result = await tool.safe_execute({
                "group_name": "developers",
                "account_id": "abc123",
            })

            assert result.success is True
            assert result.data["accountId"] == "abc123"

        @pytest.mark.asyncio
        async def test_group_name_url_encoded(self, platform_client: AsyncMock) -> None:
            """Group name with spaces is URL-encoded in the path."""
            platform_client.post.return_value = {"accountId": "abc123"}
            tool = _make_tool(GroupAddUserTool, platform_client)
            await tool.safe_execute({
                "group_name": "my group",
                "account_id": "abc123",
            })

            call_args = platform_client.post.call_args
            path = call_args[0][0]
            assert "my%20group" in path

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert GroupAddUserTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupAddUserTool()
            guide = tool.get_guide()
            assert guide.name == "group_add_user"
            assert len(guide.parameters) == 2


# --------------------------------------------------------------------------- #
# GroupRemoveUserTool
# --------------------------------------------------------------------------- #


class TestGroupRemoveUserTool:
    """Tests for group_remove_user tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_group_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupRemoveUserTool, platform_client)
            result = await tool.safe_execute({"account_id": "abc123"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_account_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupRemoveUserTool, platform_client)
            result = await tool.safe_execute({"group_name": "developers"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_remove_user(self, platform_client: AsyncMock) -> None:
            platform_client.delete.return_value = None
            tool = _make_tool(GroupRemoveUserTool, platform_client)
            result = await tool.safe_execute({
                "group_name": "developers",
                "account_id": "abc123",
            })

            assert result.success is True
            assert result.data["removed"] is True
            assert result.data["group_name"] == "developers"
            assert result.data["account_id"] == "abc123"

        @pytest.mark.asyncio
        async def test_params_forwarded(self, platform_client: AsyncMock) -> None:
            """Both groupname and accountId are passed as params."""
            platform_client.delete.return_value = None
            tool = _make_tool(GroupRemoveUserTool, platform_client)
            await tool.safe_execute({
                "group_name": "developers",
                "account_id": "abc123",
            })

            call_args = platform_client.delete.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["groupname"] == "developers"
            assert params["accountId"] == "abc123"

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            platform_client.delete.side_effect = NotFoundError(message="Group not found")
            tool = _make_tool(GroupRemoveUserTool, platform_client)
            result = await tool.safe_execute({
                "group_name": "nonexistent",
                "account_id": "abc123",
            })

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert GroupRemoveUserTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupRemoveUserTool()
            guide = tool.get_guide()
            assert guide.name == "group_remove_user"
            assert len(guide.parameters) == 2


# --------------------------------------------------------------------------- #
# GroupDeleteTool
# --------------------------------------------------------------------------- #


class TestGroupDeleteTool:
    """Tests for group_delete tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_group_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(GroupDeleteTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_delete_group(self, platform_client: AsyncMock) -> None:
            platform_client.delete.return_value = None
            tool = _make_tool(GroupDeleteTool, platform_client)
            result = await tool.safe_execute({"group_name": "old-group"})

            assert result.success is True
            assert result.data["deleted"] is True
            assert result.data["group_name"] == "old-group"

        @pytest.mark.asyncio
        async def test_group_name_in_params(self, platform_client: AsyncMock) -> None:
            """Group name is passed as a query parameter."""
            platform_client.delete.return_value = None
            tool = _make_tool(GroupDeleteTool, platform_client)
            await tool.safe_execute({"group_name": "old-group"})

            call_args = platform_client.delete.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["groupname"] == "old-group"

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            platform_client.delete.side_effect = NotFoundError(message="Group not found")
            tool = _make_tool(GroupDeleteTool, platform_client)
            result = await tool.safe_execute({"group_name": "nonexistent"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert GroupDeleteTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = GroupDeleteTool()
            guide = tool.get_guide()
            assert guide.name == "group_delete"
            assert guide.parameters[0].name == "group_name"
            assert guide.parameters[0].required is True


# --------------------------------------------------------------------------- #
# Registry integration
# --------------------------------------------------------------------------- #


class TestGroupToolRegistration:
    """Tests for group tool auto-discovery via registry."""

    def test_all_group_tools_discovered(self) -> None:
        """All 6 group tools are discovered by the registry."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        expected_names = {
            "group_list",
            "group_get_members",
            "group_create",
            "group_add_user",
            "group_remove_user",
            "group_delete",
        }

        categories = registry.get_tools_by_category()
        assert "groups" in categories
        group_names = {t.name for t in categories["groups"]}
        assert expected_names == group_names

    def test_tool_count_includes_groups(self) -> None:
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT

    def test_mutating_tools_marked(self) -> None:
        """Mutating group tools have mutates=True."""
        assert GroupCreateTool.mutates is True
        assert GroupDeleteTool.mutates is True
        assert GroupAddUserTool.mutates is True
        assert GroupRemoveUserTool.mutates is True

    def test_read_only_tools_not_marked(self) -> None:
        """Read-only group tools have mutates=False."""
        assert GroupListTool.mutates is False
        assert GroupGetMembersTool.mutates is False
