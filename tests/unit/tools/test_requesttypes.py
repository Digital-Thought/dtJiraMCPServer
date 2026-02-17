"""Tests for request type management tools (Phase 5)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.tools.requesttypes.fields import RequestTypeGetFieldsTool
from dtjiramcpserver.tools.requesttypes.groups import RequestTypeGetGroupsTool
from dtjiramcpserver.tools.requesttypes.types import (
    RequestTypeCreateTool,
    RequestTypeDeleteTool,
    RequestTypeGetTool,
    RequestTypeListTool,
)


@pytest.fixture
def jsm_client() -> AsyncMock:
    """Mocked JsmClient for request type tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/servicedeskapi"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked JSM client."""
    return tool_cls(jsm_client=client)


def _paginated_response(
    results: list[Any],
    start: int = 0,
    limit: int = 50,
    total: int | None = None,
    has_more: bool = False,
) -> PaginatedResponse:
    """Create a PaginatedResponse for mocking list_paginated."""
    return PaginatedResponse(
        results=results,
        start=start,
        limit=limit,
        total=total if total is not None else len(results),
        has_more=has_more,
    )


# --------------------------------------------------------------------------- #
# RequestTypeListTool
# --------------------------------------------------------------------------- #


class TestRequestTypeListTool:
    """Tests for requesttype_list tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeListTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_request_types(self, jsm_client: AsyncMock) -> None:
            """Lists request types with pagination."""
            types = [
                {"id": "1", "name": "Get IT Help", "issueTypeId": "10001"},
                {"id": "2", "name": "New Hardware", "issueTypeId": "10001"},
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                types, total=2
            )
            tool = _make_tool(RequestTypeListTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2

        @pytest.mark.asyncio
        async def test_search_query_filter(self, jsm_client: AsyncMock) -> None:
            """search_query is passed as extra_params."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(RequestTypeListTool, jsm_client)
            await tool.safe_execute(
                {"service_desk_id": 1, "search_query": "hardware"}
            )

            call_kwargs = jsm_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {
                "searchQuery": "hardware"
            }

        @pytest.mark.asyncio
        async def test_group_id_filter(self, jsm_client: AsyncMock) -> None:
            """group_id is passed as extra_params."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(RequestTypeListTool, jsm_client)
            await tool.safe_execute(
                {"service_desk_id": 1, "group_id": 3}
            )

            call_kwargs = jsm_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {"groupId": 3}

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeListTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_list"
            assert guide.category == "requesttypes"
            assert len(guide.examples) >= 1


# --------------------------------------------------------------------------- #
# RequestTypeGetTool
# --------------------------------------------------------------------------- #


class TestRequestTypeGetTool:
    """Tests for requesttype_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_request_type_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_request_type(self, jsm_client: AsyncMock) -> None:
            """Gets a request type by ID."""
            rt = {"id": "5", "name": "Get IT Help", "issueTypeId": "10001"}
            jsm_client.get.return_value = rt
            tool = _make_tool(RequestTypeGetTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "request_type_id": 5}
            )

            assert result.success is True
            assert result.data["name"] == "Get IT Help"
            jsm_client.get.assert_called_once_with(
                "/servicedesk/1/requesttype/5"
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_get"


# --------------------------------------------------------------------------- #
# RequestTypeCreateTool
# --------------------------------------------------------------------------- #


class TestRequestTypeCreateTool:
    """Tests for requesttype_create tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_name(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeCreateTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "issue_type_id": "10001"}
            )
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_issue_type_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeCreateTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "name": "Test"}
            )
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_create_simple(self, jsm_client: AsyncMock) -> None:
            """Creates a request type with required fields only."""
            jsm_client.post.return_value = {
                "id": "10",
                "name": "VPN Access",
                "issueTypeId": "10001",
            }
            tool = _make_tool(RequestTypeCreateTool, jsm_client)
            result = await tool.safe_execute(
                {
                    "service_desk_id": 1,
                    "name": "VPN Access",
                    "issue_type_id": "10001",
                }
            )

            assert result.success is True
            assert result.data["id"] == "10"
            jsm_client.post.assert_called_once_with(
                "/servicedesk/1/requesttype",
                json={"name": "VPN Access", "issueTypeId": "10001"},
            )

        @pytest.mark.asyncio
        async def test_create_with_optional_fields(self, jsm_client: AsyncMock) -> None:
            """Creates a request type with description and help text."""
            jsm_client.post.return_value = {"id": "11", "name": "Test"}
            tool = _make_tool(RequestTypeCreateTool, jsm_client)
            result = await tool.safe_execute(
                {
                    "service_desk_id": 1,
                    "name": "Test",
                    "issue_type_id": "10001",
                    "description": "A test request",
                    "help_text": "Fill in the form",
                }
            )

            assert result.success is True
            call_body = jsm_client.post.call_args.kwargs["json"]
            assert call_body["description"] == "A test request"
            assert call_body["helpText"] == "Fill in the form"

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeCreateTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_create"


# --------------------------------------------------------------------------- #
# RequestTypeDeleteTool
# --------------------------------------------------------------------------- #


class TestRequestTypeDeleteTool:
    """Tests for requesttype_delete tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_request_type_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeDeleteTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_delete_request_type(self, jsm_client: AsyncMock) -> None:
            """Deletes a request type."""
            jsm_client.delete.return_value = None
            tool = _make_tool(RequestTypeDeleteTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "request_type_id": 5}
            )

            assert result.success is True
            assert result.data["deleted"] is True
            jsm_client.delete.assert_called_once_with(
                "/servicedesk/1/requesttype/5"
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeDeleteTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_delete"


# --------------------------------------------------------------------------- #
# RequestTypeGetFieldsTool
# --------------------------------------------------------------------------- #


class TestRequestTypeGetFieldsTool:
    """Tests for requesttype_get_fields tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_request_type_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetFieldsTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_fields(self, jsm_client: AsyncMock) -> None:
            """Gets fields for a request type."""
            jsm_client.get.return_value = {
                "requestTypeFields": [
                    {"fieldId": "summary", "name": "Summary", "required": True},
                    {"fieldId": "description", "name": "Description", "required": False},
                ]
            }
            tool = _make_tool(RequestTypeGetFieldsTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "request_type_id": 5}
            )

            assert result.success is True
            assert len(result.data) == 2
            assert result.data[0]["fieldId"] == "summary"
            jsm_client.get.assert_called_once_with(
                "/servicedesk/1/requesttype/5/field"
            )

        @pytest.mark.asyncio
        async def test_get_fields_values_format(self, jsm_client: AsyncMock) -> None:
            """Handles values format from API."""
            jsm_client.get.return_value = {
                "values": [
                    {"fieldId": "summary", "name": "Summary", "required": True},
                ]
            }
            tool = _make_tool(RequestTypeGetFieldsTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "request_type_id": 5}
            )

            assert result.success is True
            assert len(result.data) == 1

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetFieldsTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_get_fields"


# --------------------------------------------------------------------------- #
# RequestTypeGetGroupsTool
# --------------------------------------------------------------------------- #


class TestRequestTypeGetGroupsTool:
    """Tests for requesttype_get_groups tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetGroupsTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_groups(self, jsm_client: AsyncMock) -> None:
            """Lists request type groups."""
            groups = [
                {"id": "1", "name": "General"},
                {"id": "2", "name": "Access & Permissions"},
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                groups, total=2
            )
            tool = _make_tool(RequestTypeGetGroupsTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert len(result.data) == 2
            jsm_client.list_paginated.assert_called_once_with(
                "/servicedesk/1/requesttypegroup", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(RequestTypeGetGroupsTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "requesttype_get_groups"


# --------------------------------------------------------------------------- #
# Registry Integration
# --------------------------------------------------------------------------- #


class TestRequestTypeToolRegistration:
    """Tests for request type tool auto-discovery."""

    def test_all_requesttype_tools_discovered(
        self, tool_registry: Any
    ) -> None:
        """All 6 request type tools are discovered by the registry."""
        expected = {
            "requesttype_list",
            "requesttype_get",
            "requesttype_create",
            "requesttype_delete",
            "requesttype_get_fields",
            "requesttype_get_groups",
        }
        for name in expected:
            assert tool_registry.get_tool(name) is not None, f"Tool {name} not found"

    def test_tool_count_includes_requesttypes(
        self, tool_registry: Any
    ) -> None:
        """Total tool count includes request type tools."""
        # meta (2) + issues (7) + servicedesk (10) + requesttypes (6) + fields (10) + workflows (8) + kb (1) + sla (2) + assets (1) = 47
        assert tool_registry.tool_count == 47
