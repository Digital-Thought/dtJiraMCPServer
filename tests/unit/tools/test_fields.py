"""Tests for field management tools (Phase 6)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.tools.fields.contexts import (
    FieldAddContextTool,
    FieldGetContextsTool,
)
from dtjiramcpserver.tools.fields.custom_fields import (
    FieldCreateTool,
    FieldListTool,
    FieldUpdateTool,
)
from dtjiramcpserver.tools.fields.schemes import (
    ScreenSchemeGetTool,
    ScreenSchemeListTool,
)
from dtjiramcpserver.tools.fields.screens import (
    ScreenAddFieldTool,
    ScreenGetTool,
    ScreenListTool,
)


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for field tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked platform client."""
    return tool_cls(platform_client=client)


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
# FieldListTool
# --------------------------------------------------------------------------- #


class TestFieldListTool:
    """Tests for field_list tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_all_fields(self, platform_client: AsyncMock) -> None:
            """Lists all fields (system and custom)."""
            fields = [
                {"id": "summary", "name": "Summary", "custom": False},
                {"id": "customfield_10001", "name": "Story Points", "custom": True},
            ]
            platform_client.get.return_value = fields
            tool = _make_tool(FieldListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            platform_client.get.assert_called_once_with("/field")

        @pytest.mark.asyncio
        async def test_filter_custom_fields(self, platform_client: AsyncMock) -> None:
            """Filters to only custom fields."""
            fields = [
                {"id": "summary", "name": "Summary", "custom": False},
                {"id": "customfield_10001", "name": "Story Points", "custom": True},
                {"id": "customfield_10002", "name": "Sprint", "custom": True},
            ]
            platform_client.get.return_value = fields
            tool = _make_tool(FieldListTool, platform_client)
            result = await tool.safe_execute({"type_filter": "custom"})

            assert result.success is True
            assert len(result.data) == 2
            assert all(f["custom"] for f in result.data)

        @pytest.mark.asyncio
        async def test_filter_system_fields(self, platform_client: AsyncMock) -> None:
            """Filters to only system fields."""
            fields = [
                {"id": "summary", "name": "Summary", "custom": False},
                {"id": "customfield_10001", "name": "Story Points", "custom": True},
            ]
            platform_client.get.return_value = fields
            tool = _make_tool(FieldListTool, platform_client)
            result = await tool.safe_execute({"type_filter": "system"})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["id"] == "summary"

        @pytest.mark.asyncio
        async def test_invalid_type_filter(self, platform_client: AsyncMock) -> None:
            """Invalid type_filter returns validation error."""
            tool = _make_tool(FieldListTool, platform_client)
            result = await tool.safe_execute({"type_filter": "invalid"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_handles_non_list_response(self, platform_client: AsyncMock) -> None:
            """Handles unexpected response format gracefully."""
            platform_client.get.return_value = {"unexpected": "format"}
            tool = _make_tool(FieldListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert result.data == []

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "field_list"
            assert guide.category == "fields"
            assert len(guide.examples) >= 1


# --------------------------------------------------------------------------- #
# FieldCreateTool
# --------------------------------------------------------------------------- #


class TestFieldCreateTool:
    """Tests for field_create tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldCreateTool, platform_client)
            result = await tool.safe_execute(
                {"field_type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield"}
            )
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_field_type(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldCreateTool, platform_client)
            result = await tool.safe_execute({"name": "My Field"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_create_simple(self, platform_client: AsyncMock) -> None:
            """Creates a field with required fields only."""
            platform_client.post.return_value = {
                "id": "customfield_10100",
                "name": "Release Notes",
            }
            tool = _make_tool(FieldCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Release Notes",
                "field_type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
            })

            assert result.success is True
            assert result.data["id"] == "customfield_10100"
            platform_client.post.assert_called_once_with(
                "/field",
                json={
                    "name": "Release Notes",
                    "type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
                },
            )

        @pytest.mark.asyncio
        async def test_create_with_optional_fields(self, platform_client: AsyncMock) -> None:
            """Creates a field with description and searcher key."""
            platform_client.post.return_value = {"id": "customfield_10101", "name": "Notes"}
            tool = _make_tool(FieldCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Notes",
                "field_type": "com.atlassian.jira.plugin.system.customfieldtypes:textarea",
                "description": "Release notes field",
                "searcher_key": "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher",
            })

            assert result.success is True
            call_body = platform_client.post.call_args.kwargs["json"]
            assert call_body["description"] == "Release notes field"
            assert call_body["searcherKey"] == "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldCreateTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "field_create"
            assert guide.category == "fields"


# --------------------------------------------------------------------------- #
# FieldUpdateTool
# --------------------------------------------------------------------------- #


class TestFieldUpdateTool:
    """Tests for field_update tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_field_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldUpdateTool, platform_client)
            result = await tool.safe_execute({"name": "New Name"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_no_fields_to_update(self, platform_client: AsyncMock) -> None:
            """Must provide at least one update field."""
            tool = _make_tool(FieldUpdateTool, platform_client)
            result = await tool.safe_execute({"field_id": "customfield_10001"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_update_name(self, platform_client: AsyncMock) -> None:
            """Updates a field's name."""
            platform_client.put.return_value = None
            tool = _make_tool(FieldUpdateTool, platform_client)
            result = await tool.safe_execute({
                "field_id": "customfield_10001",
                "name": "Story Points v2",
            })

            assert result.success is True
            assert result.data["updated"] is True
            platform_client.put.assert_called_once_with(
                "/field/customfield_10001",
                json={"name": "Story Points v2"},
            )

        @pytest.mark.asyncio
        async def test_update_multiple_fields(self, platform_client: AsyncMock) -> None:
            """Updates name and description together."""
            platform_client.put.return_value = None
            tool = _make_tool(FieldUpdateTool, platform_client)
            result = await tool.safe_execute({
                "field_id": "customfield_10001",
                "name": "Story Points v2",
                "description": "Updated description",
            })

            assert result.success is True
            call_body = platform_client.put.call_args.kwargs["json"]
            assert call_body["name"] == "Story Points v2"
            assert call_body["description"] == "Updated description"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldUpdateTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "field_update"


# --------------------------------------------------------------------------- #
# FieldGetContextsTool
# --------------------------------------------------------------------------- #


class TestFieldGetContextsTool:
    """Tests for field_get_contexts tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_field_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldGetContextsTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_contexts(self, platform_client: AsyncMock) -> None:
            """Gets contexts for a custom field."""
            contexts = [
                {"id": "10100", "name": "Default Context", "isGlobalContext": True},
            ]
            platform_client.list_paginated.return_value = _paginated_response(
                contexts, total=1
            )
            tool = _make_tool(FieldGetContextsTool, platform_client)
            result = await tool.safe_execute({"field_id": "customfield_10001"})

            assert result.success is True
            assert len(result.data) == 1
            assert result.pagination["total"] == 1
            platform_client.list_paginated.assert_called_once_with(
                "/field/customfield_10001/context", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldGetContextsTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "field_get_contexts"
            assert guide.category == "fields"


# --------------------------------------------------------------------------- #
# FieldAddContextTool
# --------------------------------------------------------------------------- #


class TestFieldAddContextTool:
    """Tests for field_add_context tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_field_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldAddContextTool, platform_client)
            result = await tool.safe_execute({"name": "Test Context"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldAddContextTool, platform_client)
            result = await tool.safe_execute({"field_id": "customfield_10001"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_add_global_context(self, platform_client: AsyncMock) -> None:
            """Adds a global context (no project/issue type scoping)."""
            platform_client.post.return_value = {
                "id": "10200",
                "name": "Global Context",
            }
            tool = _make_tool(FieldAddContextTool, platform_client)
            result = await tool.safe_execute({
                "field_id": "customfield_10001",
                "name": "Global Context",
            })

            assert result.success is True
            assert result.data["id"] == "10200"
            platform_client.post.assert_called_once_with(
                "/field/customfield_10001/context",
                json={"name": "Global Context"},
            )

        @pytest.mark.asyncio
        async def test_add_scoped_context(self, platform_client: AsyncMock) -> None:
            """Adds a project-scoped context."""
            platform_client.post.return_value = {"id": "10201", "name": "Scoped"}
            tool = _make_tool(FieldAddContextTool, platform_client)
            result = await tool.safe_execute({
                "field_id": "customfield_10001",
                "name": "Project ABC",
                "description": "For project ABC",
                "project_ids": ["10001"],
                "issue_type_ids": ["10000"],
            })

            assert result.success is True
            call_body = platform_client.post.call_args.kwargs["json"]
            assert call_body["name"] == "Project ABC"
            assert call_body["description"] == "For project ABC"
            assert call_body["projectIds"] == ["10001"]
            assert call_body["issueTypeIds"] == ["10000"]

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(FieldAddContextTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "field_add_context"


# --------------------------------------------------------------------------- #
# ScreenListTool
# --------------------------------------------------------------------------- #


class TestScreenListTool:
    """Tests for screen_list tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_screens(self, platform_client: AsyncMock) -> None:
            """Lists screens with pagination."""
            screens = [
                {"id": 1, "name": "Default Screen"},
                {"id": 2, "name": "Bug Screen"},
            ]
            platform_client.list_paginated.return_value = _paginated_response(
                screens, total=2
            )
            tool = _make_tool(ScreenListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            platform_client.list_paginated.assert_called_once_with(
                "/screens", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "screen_list"
            assert guide.category == "fields"


# --------------------------------------------------------------------------- #
# ScreenGetTool
# --------------------------------------------------------------------------- #


class TestScreenGetTool:
    """Tests for screen_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_screen_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_screen_tabs(self, platform_client: AsyncMock) -> None:
            """Gets screen tabs and fields."""
            tabs = [
                {
                    "id": 10001,
                    "name": "Field Tab",
                    "fields": [
                        {"id": "summary", "name": "Summary"},
                        {"id": "description", "name": "Description"},
                    ],
                }
            ]
            platform_client.get.return_value = tabs
            tool = _make_tool(ScreenGetTool, platform_client)
            result = await tool.safe_execute({"screen_id": 1})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["name"] == "Field Tab"
            platform_client.get.assert_called_once_with("/screens/1/tabs")

        @pytest.mark.asyncio
        async def test_handles_non_list_response(self, platform_client: AsyncMock) -> None:
            """Handles unexpected response format."""
            platform_client.get.return_value = {"unexpected": True}
            tool = _make_tool(ScreenGetTool, platform_client)
            result = await tool.safe_execute({"screen_id": 1})

            assert result.success is True
            assert result.data == []

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenGetTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "screen_get"


# --------------------------------------------------------------------------- #
# ScreenAddFieldTool
# --------------------------------------------------------------------------- #


class TestScreenAddFieldTool:
    """Tests for screen_add_field tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_screen_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenAddFieldTool, platform_client)
            result = await tool.safe_execute({"tab_id": 1, "field_id": "summary"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_field_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenAddFieldTool, platform_client)
            result = await tool.safe_execute({"screen_id": 1, "tab_id": 1})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_add_field_to_tab(self, platform_client: AsyncMock) -> None:
            """Adds a field to a screen tab."""
            platform_client.post.return_value = {
                "id": "customfield_10001",
                "name": "Story Points",
            }
            tool = _make_tool(ScreenAddFieldTool, platform_client)
            result = await tool.safe_execute({
                "screen_id": 1,
                "tab_id": 10001,
                "field_id": "customfield_10001",
            })

            assert result.success is True
            assert result.data["id"] == "customfield_10001"
            platform_client.post.assert_called_once_with(
                "/screens/1/tabs/10001/fields",
                json={"fieldId": "customfield_10001"},
            )

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenAddFieldTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "screen_add_field"


# --------------------------------------------------------------------------- #
# ScreenSchemeListTool
# --------------------------------------------------------------------------- #


class TestScreenSchemeListTool:
    """Tests for screen_scheme_list tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_screen_schemes(self, platform_client: AsyncMock) -> None:
            """Lists screen schemes with pagination."""
            schemes = [
                {"id": 1, "name": "Default Screen Scheme"},
            ]
            platform_client.list_paginated.return_value = _paginated_response(
                schemes, total=1
            )
            tool = _make_tool(ScreenSchemeListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 1
            assert result.pagination["total"] == 1
            platform_client.list_paginated.assert_called_once_with(
                "/screenscheme", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenSchemeListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "screen_scheme_list"
            assert guide.category == "fields"


# --------------------------------------------------------------------------- #
# ScreenSchemeGetTool
# --------------------------------------------------------------------------- #


class TestScreenSchemeGetTool:
    """Tests for screen_scheme_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_screen_scheme_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenSchemeGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_screen_scheme(self, platform_client: AsyncMock) -> None:
            """Gets a screen scheme by ID."""
            platform_client.get.return_value = {
                "values": [
                    {
                        "id": 1,
                        "name": "Default Screen Scheme",
                        "screens": {"default": {"id": 1, "name": "Default Screen"}},
                    }
                ]
            }
            tool = _make_tool(ScreenSchemeGetTool, platform_client)
            result = await tool.safe_execute({"screen_scheme_id": 1})

            assert result.success is True
            assert result.data["name"] == "Default Screen Scheme"
            platform_client.get.assert_called_once_with(
                "/screenscheme", params={"id": 1}
            )

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            """Returns NOT_FOUND error when scheme doesn't exist."""
            platform_client.get.return_value = {"values": []}
            tool = _make_tool(ScreenSchemeGetTool, platform_client)
            result = await tool.safe_execute({"screen_scheme_id": 999})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ScreenSchemeGetTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "screen_scheme_get"


# --------------------------------------------------------------------------- #
# Registry Integration
# --------------------------------------------------------------------------- #


class TestFieldToolRegistration:
    """Tests for field tool auto-discovery."""

    def test_all_field_tools_discovered(self, tool_registry: Any) -> None:
        """All 10 field tools are discovered by the registry."""
        expected = {
            "field_list",
            "field_create",
            "field_update",
            "field_get_contexts",
            "field_add_context",
            "screen_list",
            "screen_get",
            "screen_add_field",
            "screen_scheme_list",
            "screen_scheme_get",
        }
        for name in expected:
            assert tool_registry.get_tool(name) is not None, f"Tool {name} not found"

    def test_tool_count_includes_fields(self, tool_registry: Any) -> None:
        """Total tool count includes field tools."""
        # meta (2) + issues (7) + servicedesk (10) + requesttypes (6) + fields (10) + workflows (8) + kb (1) + sla (2) + assets (1) = 47
        assert tool_registry.tool_count == 47
