"""Tests for workflow management tools (Phase 7)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from tests.conftest import EXPECTED_TOOL_COUNT
from dtjiramcpserver.tools.workflows.statuses import (
    StatusCreateTool,
    StatusGetTool,
    StatusListTool,
)
from dtjiramcpserver.tools.workflows.transitions import (
    TransitionGetTool,
    TransitionListTool,
)
from dtjiramcpserver.tools.workflows.workflows import (
    WorkflowCreateTool,
    WorkflowGetTool,
    WorkflowListTool,
)


@pytest.fixture
def platform_client() -> AsyncMock:
    """Mocked PlatformClient for workflow tools."""
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
# WorkflowListTool
# --------------------------------------------------------------------------- #


class TestWorkflowListTool:
    """Tests for workflow_list tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_workflows(self, platform_client: AsyncMock) -> None:
            """Lists workflows with pagination."""
            workflows = [
                {"id": {"name": "jira"}, "description": "Default workflow"},
                {"id": {"name": "Custom"}, "description": "Custom workflow"},
            ]
            platform_client.list_paginated.return_value = _paginated_response(
                workflows, total=2
            )
            tool = _make_tool(WorkflowListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            platform_client.list_paginated.assert_called_once_with(
                "/workflow/search", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "workflow_list"
            assert guide.category == "workflows"
            assert len(guide.examples) >= 1


# --------------------------------------------------------------------------- #
# WorkflowGetTool
# --------------------------------------------------------------------------- #


class TestWorkflowGetTool:
    """Tests for workflow_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_workflow_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_workflow(self, platform_client: AsyncMock) -> None:
            """Gets a workflow by name with expanded data."""
            platform_client.get.return_value = {
                "values": [
                    {
                        "id": {"name": "jira"},
                        "description": "Default workflow",
                        "transitions": [
                            {"id": "1", "name": "Create", "type": "initial"}
                        ],
                        "statuses": [{"id": "1", "name": "Open"}],
                    }
                ]
            }
            tool = _make_tool(WorkflowGetTool, platform_client)
            result = await tool.safe_execute({"workflow_name": "jira"})

            assert result.success is True
            assert result.data["id"]["name"] == "jira"
            assert len(result.data["transitions"]) == 1
            platform_client.get.assert_called_once_with(
                "/workflow/search",
                params={
                    "workflowName": "jira",
                    "expand": "transitions,statuses",
                },
            )

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            """Returns NOT_FOUND for non-existent workflow."""
            platform_client.get.return_value = {"values": []}
            tool = _make_tool(WorkflowGetTool, platform_client)
            result = await tool.safe_execute({"workflow_name": "nonexistent"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowGetTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "workflow_get"


# --------------------------------------------------------------------------- #
# WorkflowCreateTool
# --------------------------------------------------------------------------- #


class TestWorkflowCreateTool:
    """Tests for workflow_create tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowCreateTool, platform_client)
            result = await tool.safe_execute({
                "statuses": [{"id": "1"}],
                "transitions": [{"name": "Create", "type": "initial", "to": "1"}],
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_statuses(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Test",
                "transitions": [{"name": "Create", "type": "initial", "to": "1"}],
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_create_workflow(self, platform_client: AsyncMock) -> None:
            """Creates a workflow with statuses and transitions."""
            platform_client.post.return_value = {
                "workflows": [{"id": "wf-uuid", "name": "My Workflow"}]
            }
            tool = _make_tool(WorkflowCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "My Workflow",
                "statuses": [{"id": "1"}, {"id": "3"}],
                "transitions": [
                    {"name": "Create", "type": "initial", "to": "1"},
                    {"name": "Start", "type": "directed", "from": ["1"], "to": "3"},
                ],
                "scope_project_id": "10001",
            })

            assert result.success is True
            assert result.data["workflows"][0]["name"] == "My Workflow"
            call_body = platform_client.post.call_args.kwargs["json"]
            assert call_body["scope"]["type"] == "PROJECT"
            assert call_body["scope"]["project"]["id"] == "10001"
            assert len(call_body["workflows"]) == 1
            assert call_body["workflows"][0]["name"] == "My Workflow"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(WorkflowCreateTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "workflow_create"


# --------------------------------------------------------------------------- #
# StatusListTool
# --------------------------------------------------------------------------- #


class TestStatusListTool:
    """Tests for status_list tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_statuses(self, platform_client: AsyncMock) -> None:
            """Lists statuses with pagination."""
            statuses = [
                {"id": "1", "name": "Open", "statusCategory": "TODO"},
                {"id": "3", "name": "In Progress", "statusCategory": "IN_PROGRESS"},
            ]
            platform_client.list_paginated.return_value = _paginated_response(
                statuses, total=2
            )
            tool = _make_tool(StatusListTool, platform_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2

        @pytest.mark.asyncio
        async def test_filter_by_category(self, platform_client: AsyncMock) -> None:
            """Filters statuses by category."""
            platform_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(StatusListTool, platform_client)
            await tool.safe_execute({"status_category": "IN_PROGRESS"})

            call_kwargs = platform_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {
                "statusCategory": "IN_PROGRESS"
            }

        @pytest.mark.asyncio
        async def test_search_string(self, platform_client: AsyncMock) -> None:
            """Filters statuses by search string."""
            platform_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(StatusListTool, platform_client)
            await tool.safe_execute({"search_string": "progress"})

            call_kwargs = platform_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {
                "searchString": "progress"
            }

        @pytest.mark.asyncio
        async def test_invalid_category(self, platform_client: AsyncMock) -> None:
            """Invalid category returns validation error."""
            tool = _make_tool(StatusListTool, platform_client)
            result = await tool.safe_execute({"status_category": "INVALID"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "status_list"
            assert guide.category == "workflows"
            assert len(guide.examples) >= 2


# --------------------------------------------------------------------------- #
# StatusGetTool
# --------------------------------------------------------------------------- #


class TestStatusGetTool:
    """Tests for status_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_status_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusGetTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_status(self, platform_client: AsyncMock) -> None:
            """Gets a status by ID."""
            platform_client.get.return_value = {
                "id": "1",
                "name": "Open",
                "statusCategory": {"id": 2, "key": "new", "name": "To Do"},
            }
            tool = _make_tool(StatusGetTool, platform_client)
            result = await tool.safe_execute({"status_id_or_name": "1"})

            assert result.success is True
            assert result.data["name"] == "Open"
            platform_client.get.assert_called_once_with("/status/1")

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusGetTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "status_get"


# --------------------------------------------------------------------------- #
# StatusCreateTool
# --------------------------------------------------------------------------- #


class TestStatusCreateTool:
    """Tests for status_create tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusCreateTool, platform_client)
            result = await tool.safe_execute({"status_category": "TODO"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_category(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusCreateTool, platform_client)
            result = await tool.safe_execute({"name": "New Status"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_category(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Test",
                "status_category": "INVALID",
            })
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_create_status(self, platform_client: AsyncMock) -> None:
            """Creates a status with required fields."""
            platform_client.post.return_value = [
                {"id": "10100", "name": "Review", "statusCategory": "IN_PROGRESS"}
            ]
            tool = _make_tool(StatusCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Review",
                "status_category": "IN_PROGRESS",
                "scope_project_id": "10001",
            })

            assert result.success is True
            call_body = platform_client.post.call_args.kwargs["json"]
            assert call_body["statuses"][0]["name"] == "Review"
            assert call_body["statuses"][0]["statusCategory"] == "IN_PROGRESS"
            assert call_body["scope"]["project"]["id"] == "10001"

        @pytest.mark.asyncio
        async def test_create_with_description(self, platform_client: AsyncMock) -> None:
            """Creates a status with optional description."""
            platform_client.post.return_value = [{"id": "10101", "name": "Test"}]
            tool = _make_tool(StatusCreateTool, platform_client)
            result = await tool.safe_execute({
                "name": "Test",
                "status_category": "TODO",
                "description": "A test status",
            })

            assert result.success is True
            call_body = platform_client.post.call_args.kwargs["json"]
            assert call_body["statuses"][0]["description"] == "A test status"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(StatusCreateTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "status_create"


# --------------------------------------------------------------------------- #
# TransitionListTool
# --------------------------------------------------------------------------- #


class TestTransitionListTool:
    """Tests for transition_list tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_workflow_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(TransitionListTool, platform_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_transitions(self, platform_client: AsyncMock) -> None:
            """Lists transitions for a workflow."""
            platform_client.get.return_value = {
                "values": [
                    {
                        "id": {"name": "jira"},
                        "transitions": [
                            {"id": "1", "name": "Create", "type": "initial"},
                            {"id": "2", "name": "Start Progress", "type": "directed"},
                        ],
                    }
                ]
            }
            tool = _make_tool(TransitionListTool, platform_client)
            result = await tool.safe_execute({"workflow_name": "jira"})

            assert result.success is True
            assert len(result.data) == 2
            assert result.data[0]["name"] == "Create"
            platform_client.get.assert_called_once_with(
                "/workflow/search",
                params={"workflowName": "jira", "expand": "transitions"},
            )

        @pytest.mark.asyncio
        async def test_not_found(self, platform_client: AsyncMock) -> None:
            """Returns NOT_FOUND for non-existent workflow."""
            platform_client.get.return_value = {"values": []}
            tool = _make_tool(TransitionListTool, platform_client)
            result = await tool.safe_execute({"workflow_name": "nonexistent"})

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(TransitionListTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "transition_list"


# --------------------------------------------------------------------------- #
# TransitionGetTool
# --------------------------------------------------------------------------- #


class TestTransitionGetTool:
    """Tests for transition_get tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_workflow_name(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(TransitionGetTool, platform_client)
            result = await tool.safe_execute({"transition_id": "1"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_transition_id(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(TransitionGetTool, platform_client)
            result = await tool.safe_execute({"workflow_name": "jira"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_transition(self, platform_client: AsyncMock) -> None:
            """Gets a specific transition by ID."""
            platform_client.get.return_value = {
                "values": [
                    {
                        "id": {"name": "jira"},
                        "transitions": [
                            {"id": "1", "name": "Create", "type": "initial"},
                            {
                                "id": "2",
                                "name": "Start Progress",
                                "type": "directed",
                                "rules": {"conditions": [], "validators": []},
                            },
                        ],
                    }
                ]
            }
            tool = _make_tool(TransitionGetTool, platform_client)
            result = await tool.safe_execute({
                "workflow_name": "jira",
                "transition_id": "2",
            })

            assert result.success is True
            assert result.data["name"] == "Start Progress"
            assert "rules" in result.data

        @pytest.mark.asyncio
        async def test_workflow_not_found(self, platform_client: AsyncMock) -> None:
            """Returns NOT_FOUND for non-existent workflow."""
            platform_client.get.return_value = {"values": []}
            tool = _make_tool(TransitionGetTool, platform_client)
            result = await tool.safe_execute({
                "workflow_name": "nonexistent",
                "transition_id": "1",
            })

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

        @pytest.mark.asyncio
        async def test_transition_not_found(self, platform_client: AsyncMock) -> None:
            """Returns NOT_FOUND for non-existent transition in workflow."""
            platform_client.get.return_value = {
                "values": [
                    {
                        "id": {"name": "jira"},
                        "transitions": [
                            {"id": "1", "name": "Create", "type": "initial"},
                        ],
                    }
                ]
            }
            tool = _make_tool(TransitionGetTool, platform_client)
            result = await tool.safe_execute({
                "workflow_name": "jira",
                "transition_id": "999",
            })

            assert result.success is False
            assert result.error["type"] == "NOT_FOUND"

    class TestGuide:
        def test_guide_metadata(self, platform_client: AsyncMock) -> None:
            tool = _make_tool(TransitionGetTool, platform_client)
            guide = tool.get_guide()
            assert guide.name == "transition_get"


# --------------------------------------------------------------------------- #
# Registry Integration
# --------------------------------------------------------------------------- #


class TestWorkflowToolRegistration:
    """Tests for workflow tool auto-discovery."""

    def test_all_workflow_tools_discovered(self, tool_registry: Any) -> None:
        """All 8 workflow tools are discovered by the registry."""
        expected = {
            "workflow_list",
            "workflow_get",
            "workflow_create",
            "status_list",
            "status_get",
            "status_create",
            "transition_list",
            "transition_get",
        }
        for name in expected:
            assert tool_registry.get_tool(name) is not None, f"Tool {name} not found"

    def test_tool_count_includes_workflows(self, tool_registry: Any) -> None:
        """Total tool count includes workflow tools."""
        assert tool_registry.tool_count == EXPECTED_TOOL_COUNT
