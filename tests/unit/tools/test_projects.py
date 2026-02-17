"""Tests for project management tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.exceptions import NotFoundError
from dtjiramcpserver.tools.projects.create_project import ProjectCreateTool
from dtjiramcpserver.tools.projects.delete_project import ProjectDeleteTool
from dtjiramcpserver.tools.projects.get_project import ProjectGetTool
from dtjiramcpserver.tools.projects.list_projects import ProjectListTool
from dtjiramcpserver.tools.projects.update_project import ProjectUpdateTool
from tests.conftest import EXPECTED_TOOL_COUNT


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for project tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked platform client."""
    return tool_cls(platform_client=client)


# --------------------------------------------------------------------------- #
# ProjectListTool
# --------------------------------------------------------------------------- #


class TestProjectListTool:
    """Tests for project_list tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_invalid_type_key(self, platform_client: AsyncMock) -> None:
            """Invalid type_key returns VALIDATION_ERROR."""
            tool = _make_tool(ProjectListTool, platform_client)
            result = await tool.safe_execute({"type_key": "invalid"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_list_all_projects(self, platform_client: AsyncMock) -> None:
            """Default listing returns paginated projects."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[
                    {"id": "10001", "key": "PROJ", "name": "My Project"},
                    {"id": "10002", "key": "TEST", "name": "Test Project"},
                ],
                start=0,
                limit=50,
                total=2,
                has_more=False,
            )
            tool = _make_tool(ProjectListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            assert result.pagination["has_more"] is False

        @pytest.mark.asyncio
        async def test_list_with_query_filter(self, platform_client: AsyncMock) -> None:
            """Query parameter is forwarded as extra_params."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[{"key": "SUPPORT"}],
                start=0,
                limit=50,
                total=1,
                has_more=False,
            )
            tool = _make_tool(ProjectListTool, platform_client)
            await tool.safe_execute({"query": "support"})

            call_args = platform_client.list_paginated.call_args
            assert call_args.kwargs["extra_params"]["query"] == "support"

        @pytest.mark.asyncio
        async def test_list_with_type_key(self, platform_client: AsyncMock) -> None:
            """type_key parameter is forwarded as typeKey."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[],
                start=0,
                limit=50,
                total=0,
                has_more=False,
            )
            tool = _make_tool(ProjectListTool, platform_client)
            await tool.safe_execute({"type_key": "software"})

            call_args = platform_client.list_paginated.call_args
            assert call_args.kwargs["extra_params"]["typeKey"] == "software"

        @pytest.mark.asyncio
        async def test_list_with_expand(self, platform_client: AsyncMock) -> None:
            """expand parameter is joined and forwarded."""
            platform_client.list_paginated.return_value = PaginatedResponse(
                results=[],
                start=0,
                limit=50,
                total=0,
                has_more=False,
            )
            tool = _make_tool(ProjectListTool, platform_client)
            await tool.safe_execute({"expand": ["description", "lead"]})

            call_args = platform_client.list_paginated.call_args
            assert call_args.kwargs["extra_params"]["expand"] == "description,lead"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = ProjectListTool()
            guide = tool.get_guide()
            assert guide.name == "project_list"
            assert guide.category == "projects"
            assert len(guide.parameters) == 5


# --------------------------------------------------------------------------- #
# ProjectGetTool
# --------------------------------------------------------------------------- #


class TestProjectGetTool:
    """Tests for project_get tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_project_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_empty_project_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectGetTool, platform_client)
            result = await tool.safe_execute({"project_key": ""})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_get_project(self, platform_client: AsyncMock) -> None:
            """Successful retrieval returns project data."""
            platform_client.get.return_value = {
                "id": "10001",
                "key": "PROJ",
                "name": "My Project",
                "projectTypeKey": "software",
            }
            tool = _make_tool(ProjectGetTool, platform_client)
            result = await tool.safe_execute({"project_key": "PROJ"})

            assert result.success is True
            assert result.data["key"] == "PROJ"

        @pytest.mark.asyncio
        async def test_get_with_expand(self, platform_client: AsyncMock) -> None:
            """expand parameter is forwarded as comma-separated params."""
            platform_client.get.return_value = {"key": "PROJ"}
            tool = _make_tool(ProjectGetTool, platform_client)
            await tool.safe_execute({
                "project_key": "PROJ",
                "expand": ["issueTypes", "lead"],
            })

            call_args = platform_client.get.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["expand"] == "issueTypes,lead"

    class TestErrorHandling:

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            platform_client.get.side_effect = NotFoundError(message="Project not found")
            tool = _make_tool(ProjectGetTool, platform_client)
            result = await tool.safe_execute({"project_key": "NOPE"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = ProjectGetTool()
            guide = tool.get_guide()
            assert guide.name == "project_get"
            assert guide.parameters[0].name == "project_key"
            assert guide.parameters[0].required is True


# --------------------------------------------------------------------------- #
# ProjectCreateTool
# --------------------------------------------------------------------------- #


class TestProjectCreateTool:
    """Tests for project_create tool."""

    _VALID_ARGS = {
        "key": "NEWPROJ",
        "name": "New Project",
        "project_type_key": "software",
        "lead_account_id": "abc123",
    }

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_required_fields(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectCreateTool, platform_client)
            result = await tool.safe_execute({"key": "PROJ"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_key_format(self, platform_client: AsyncMock) -> None:
            """Key with invalid format returns VALIDATION_ERROR."""
            tool = _make_tool(ProjectCreateTool, platform_client)
            result = await tool.safe_execute({
                "key": "1INVALID",
                "name": "Test",
                "project_type_key": "software",
                "lead_account_id": "abc123",
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_project_type(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectCreateTool, platform_client)
            result = await tool.safe_execute({
                "key": "PROJ",
                "name": "Test",
                "project_type_key": "invalid",
                "lead_account_id": "abc123",
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_single_char_key_rejected(self, platform_client: AsyncMock) -> None:
            """Single character key is too short."""
            tool = _make_tool(ProjectCreateTool, platform_client)
            result = await tool.safe_execute({
                "key": "P",
                "name": "Test",
                "project_type_key": "software",
                "lead_account_id": "abc123",
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_create_project(self, platform_client: AsyncMock) -> None:
            """Create with minimum required fields."""
            platform_client.post.return_value = {
                "id": 10001,
                "key": "NEWPROJ",
                "self": "https://test.atlassian.net/rest/api/3/project/10001",
            }
            tool = _make_tool(ProjectCreateTool, platform_client)
            result = await tool.safe_execute(TestProjectCreateTool._VALID_ARGS)

            assert result.success is True
            assert result.data["key"] == "NEWPROJ"

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["key"] == "NEWPROJ"
            assert json_body["projectTypeKey"] == "software"
            assert json_body["leadAccountId"] == "abc123"

        @pytest.mark.asyncio
        async def test_create_with_optional_fields(self, platform_client: AsyncMock) -> None:
            """Optional fields are included in the API payload."""
            platform_client.post.return_value = {"id": 10001, "key": "PROJ"}
            tool = _make_tool(ProjectCreateTool, platform_client)
            args = {
                **TestProjectCreateTool._VALID_ARGS,
                "description": "Test description",
                "assignee_type": "UNASSIGNED",
                "project_template_key": "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
            }
            result = await tool.safe_execute(args)

            assert result.success is True
            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["description"] == "Test description"
            assert json_body["assigneeType"] == "UNASSIGNED"
            assert "projectTemplateKey" in json_body

        @pytest.mark.asyncio
        async def test_key_uppercased(self, platform_client: AsyncMock) -> None:
            """Lowercase key is normalised to uppercase."""
            platform_client.post.return_value = {"id": 10001, "key": "PROJ"}
            tool = _make_tool(ProjectCreateTool, platform_client)
            args = {**TestProjectCreateTool._VALID_ARGS, "key": "proj"}
            await tool.safe_execute(args)

            call_args = platform_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["key"] == "PROJ"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            """project_create is marked as mutating."""
            assert ProjectCreateTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = ProjectCreateTool()
            guide = tool.get_guide()
            assert guide.name == "project_create"
            required = [p for p in guide.parameters if p.required]
            assert len(required) == 4


# --------------------------------------------------------------------------- #
# ProjectUpdateTool
# --------------------------------------------------------------------------- #


class TestProjectUpdateTool:
    """Tests for project_update tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_project_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectUpdateTool, platform_client)
            result = await tool.safe_execute({"name": "New Name"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_no_fields_to_update(self, platform_client: AsyncMock) -> None:
            """Empty update body returns VALIDATION_ERROR."""
            tool = _make_tool(ProjectUpdateTool, platform_client)
            result = await tool.safe_execute({"project_key": "PROJ"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_update_name(self, platform_client: AsyncMock) -> None:
            platform_client.put.return_value = None
            tool = _make_tool(ProjectUpdateTool, platform_client)
            result = await tool.safe_execute({
                "project_key": "PROJ",
                "name": "Updated Name",
            })

            assert result.success is True
            assert result.data["updated"] is True
            assert result.data["project_key"] == "PROJ"

            call_args = platform_client.put.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["name"] == "Updated Name"

        @pytest.mark.asyncio
        async def test_update_multiple_fields(self, platform_client: AsyncMock) -> None:
            platform_client.put.return_value = None
            tool = _make_tool(ProjectUpdateTool, platform_client)
            result = await tool.safe_execute({
                "project_key": "PROJ",
                "name": "New Name",
                "description": "New description",
                "lead_account_id": "newlead123",
            })

            assert result.success is True
            call_args = platform_client.put.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["name"] == "New Name"
            assert json_body["description"] == "New description"
            assert json_body["leadAccountId"] == "newlead123"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert ProjectUpdateTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = ProjectUpdateTool()
            guide = tool.get_guide()
            assert guide.name == "project_update"
            assert guide.parameters[0].name == "project_key"
            assert guide.parameters[0].required is True


# --------------------------------------------------------------------------- #
# ProjectDeleteTool
# --------------------------------------------------------------------------- #


class TestProjectDeleteTool:
    """Tests for project_delete tool."""

    class TestValidation:

        @pytest.mark.asyncio
        async def test_missing_project_key(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(ProjectDeleteTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:

        @pytest.mark.asyncio
        async def test_delete_project(self, platform_client: AsyncMock) -> None:
            platform_client.delete.return_value = None
            tool = _make_tool(ProjectDeleteTool, platform_client)
            result = await tool.safe_execute({"project_key": "PROJ"})

            assert result.success is True
            assert result.data["deleted"] is True
            assert result.data["project_key"] == "PROJ"

        @pytest.mark.asyncio
        async def test_delete_with_undo_disabled(self, platform_client: AsyncMock) -> None:
            """enable_undo=False passes 'false' to the API."""
            platform_client.delete.return_value = None
            tool = _make_tool(ProjectDeleteTool, platform_client)
            await tool.safe_execute({"project_key": "PROJ", "enable_undo": False})

            call_args = platform_client.delete.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["enableUndo"] == "false"

        @pytest.mark.asyncio
        async def test_delete_default_enables_undo(self, platform_client: AsyncMock) -> None:
            """Default enable_undo=True passes 'true' to the API."""
            platform_client.delete.return_value = None
            tool = _make_tool(ProjectDeleteTool, platform_client)
            await tool.safe_execute({"project_key": "PROJ"})

            call_args = platform_client.delete.call_args
            params = call_args.kwargs.get("params") or call_args[1].get("params")
            assert params["enableUndo"] == "true"

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            platform_client.delete.side_effect = NotFoundError(message="Project not found")
            tool = _make_tool(ProjectDeleteTool, platform_client)
            result = await tool.safe_execute({"project_key": "NOPE"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestMutates:

        def test_mutates_flag(self) -> None:
            assert ProjectDeleteTool.mutates is True

    class TestGuide:

        def test_guide_metadata(self) -> None:
            tool = ProjectDeleteTool()
            guide = tool.get_guide()
            assert guide.name == "project_delete"
            assert guide.parameters[1].name == "enable_undo"
            assert guide.parameters[1].default is True


# --------------------------------------------------------------------------- #
# Registry integration
# --------------------------------------------------------------------------- #


class TestProjectToolRegistration:
    """Tests for project tool auto-discovery via registry."""

    def test_all_project_tools_discovered(self) -> None:
        """All 5 project tools are discovered by the registry."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        expected_names = {
            "project_list",
            "project_get",
            "project_create",
            "project_update",
            "project_delete",
        }

        categories = registry.get_tools_by_category()
        assert "projects" in categories
        project_names = {t.name for t in categories["projects"]}
        assert expected_names == project_names

    def test_tool_count_includes_projects(self) -> None:
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT

    def test_mutating_tools_marked(self) -> None:
        """Mutating project tools have mutates=True."""
        assert ProjectCreateTool.mutates is True
        assert ProjectUpdateTool.mutates is True
        assert ProjectDeleteTool.mutates is True

    def test_read_only_tools_not_marked(self) -> None:
        """Read-only project tools have mutates=False."""
        assert ProjectListTool.mutates is False
        assert ProjectGetTool.mutates is False
