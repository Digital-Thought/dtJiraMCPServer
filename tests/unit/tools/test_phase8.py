"""Tests for knowledge base, SLA, and asset tools (Phase 8)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.tools.assets.workspaces import AssetsGetWorkspacesTool
from dtjiramcpserver.tools.knowledgebase.articles import KnowledgeBaseSearchTool
from dtjiramcpserver.tools.sla.metrics import SlaGetDetailTool, SlaGetMetricsTool


@pytest.fixture
def jsm_client() -> AsyncMock:
    """Mocked JsmClient for Phase 8 tools."""
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
# KnowledgeBaseSearchTool
# --------------------------------------------------------------------------- #


class TestKnowledgeBaseSearchTool:
    """Tests for knowledgebase_search tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_query(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(KnowledgeBaseSearchTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_search_all(self, jsm_client: AsyncMock) -> None:
            """Searches across all service desks."""
            articles = [
                {"title": "Password Reset", "excerpt": "How to reset..."},
                {"title": "VPN Setup", "excerpt": "Configure your VPN..."},
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                articles, total=2
            )
            tool = _make_tool(KnowledgeBaseSearchTool, jsm_client)
            result = await tool.safe_execute({"query": "password"})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2

            call_args = jsm_client.list_paginated.call_args
            assert call_args.args[0] == "/knowledgebase/article"
            assert call_args.kwargs["extra_params"]["query"] == "password"

        @pytest.mark.asyncio
        async def test_search_scoped_to_desk(self, jsm_client: AsyncMock) -> None:
            """Searches within a specific service desk."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(KnowledgeBaseSearchTool, jsm_client)
            await tool.safe_execute({"query": "VPN", "service_desk_id": 3})

            call_args = jsm_client.list_paginated.call_args
            assert call_args.args[0] == "/servicedesk/3/knowledgebase/article"

        @pytest.mark.asyncio
        async def test_highlight_param(self, jsm_client: AsyncMock) -> None:
            """Highlight param is passed correctly."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(KnowledgeBaseSearchTool, jsm_client)
            await tool.safe_execute({"query": "test", "highlight": False})

            call_kwargs = jsm_client.list_paginated.call_args.kwargs
            assert call_kwargs["extra_params"]["highlight"] == "false"

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(KnowledgeBaseSearchTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "knowledgebase_search"
            assert guide.category == "knowledgebase"
            assert len(guide.examples) >= 2


# --------------------------------------------------------------------------- #
# SlaGetMetricsTool
# --------------------------------------------------------------------------- #


class TestSlaGetMetricsTool:
    """Tests for sla_get_metrics tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_issue_key(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetMetricsTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_issue_key(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetMetricsTool, jsm_client)
            result = await tool.safe_execute({"issue_key": "invalid"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_metrics(self, jsm_client: AsyncMock) -> None:
            """Gets SLA metrics for a request."""
            metrics = [
                {
                    "id": "10001",
                    "name": "Time to first response",
                    "ongoingCycle": {"breached": False},
                },
                {
                    "id": "10002",
                    "name": "Time to resolution",
                    "ongoingCycle": {"breached": False},
                },
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                metrics, total=2
            )
            tool = _make_tool(SlaGetMetricsTool, jsm_client)
            result = await tool.safe_execute({"issue_key": "HELP-123"})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            jsm_client.list_paginated.assert_called_once_with(
                "/request/HELP-123/sla", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetMetricsTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "sla_get_metrics"
            assert guide.category == "sla"


# --------------------------------------------------------------------------- #
# SlaGetDetailTool
# --------------------------------------------------------------------------- #


class TestSlaGetDetailTool:
    """Tests for sla_get_detail tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_issue_key(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetDetailTool, jsm_client)
            result = await tool.safe_execute({"metric_id": 10001})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_metric_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetDetailTool, jsm_client)
            result = await tool.safe_execute({"issue_key": "HELP-123"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_detail(self, jsm_client: AsyncMock) -> None:
            """Gets detailed SLA information."""
            detail = {
                "id": "10001",
                "name": "Time to first response",
                "ongoingCycle": {
                    "breached": False,
                    "remainingTime": {"millis": 3600000, "friendly": "1h"},
                },
                "completedCycles": [],
            }
            jsm_client.get.return_value = detail
            tool = _make_tool(SlaGetDetailTool, jsm_client)
            result = await tool.safe_execute({
                "issue_key": "HELP-123",
                "metric_id": 10001,
            })

            assert result.success is True
            assert result.data["name"] == "Time to first response"
            assert result.data["ongoingCycle"]["breached"] is False
            jsm_client.get.assert_called_once_with(
                "/request/HELP-123/sla/10001"
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(SlaGetDetailTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "sla_get_detail"


# --------------------------------------------------------------------------- #
# AssetsGetWorkspacesTool
# --------------------------------------------------------------------------- #


class TestAssetsGetWorkspacesTool:
    """Tests for assets_get_workspaces tool."""

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_workspaces(self, jsm_client: AsyncMock) -> None:
            """Gets asset workspaces."""
            workspaces = {
                "values": [
                    {"workspaceId": "abc-123", "name": "My Workspace"},
                ]
            }
            jsm_client.get.return_value = workspaces
            tool = _make_tool(AssetsGetWorkspacesTool, jsm_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert result.data["values"][0]["workspaceId"] == "abc-123"
            jsm_client.get.assert_called_once_with("/assets/workspace")

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(AssetsGetWorkspacesTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "assets_get_workspaces"
            assert guide.category == "assets"


# --------------------------------------------------------------------------- #
# Registry Integration
# --------------------------------------------------------------------------- #


class TestPhase8ToolRegistration:
    """Tests for Phase 8 tool auto-discovery."""

    def test_all_phase8_tools_discovered(self, tool_registry: Any) -> None:
        """All 4 Phase 8 tools are discovered by the registry."""
        expected = {
            "knowledgebase_search",
            "sla_get_metrics",
            "sla_get_detail",
            "assets_get_workspaces",
        }
        for name in expected:
            assert tool_registry.get_tool(name) is not None, f"Tool {name} not found"

    def test_tool_count_includes_phase8(self, tool_registry: Any) -> None:
        """Total tool count includes Phase 8 tools."""
        # meta (2) + issues (7) + servicedesk (10) + requesttypes (6) + fields (10) + workflows (8) + kb (1) + sla (2) + assets (1) = 47
        assert tool_registry.tool_count == 47
