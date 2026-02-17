"""Tests for ToolRegistry auto-discovery and routing."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.exceptions import ToolNotFoundError
from dtjiramcpserver.tools.registry import ToolRegistry
from tests.conftest import EXPECTED_TOOL_COUNT


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_discover_finds_meta_tools(self, tool_registry: ToolRegistry) -> None:
        """Auto-discovery registers the meta tools."""
        assert tool_registry.get_tool("list_available_tools") is not None
        assert tool_registry.get_tool("get_tool_guide") is not None

    def test_discover_skips_empty_packages(self) -> None:
        """Empty stub packages do not cause errors."""
        registry = ToolRegistry()
        registry.discover_and_register()
        assert registry.tool_count == EXPECTED_TOOL_COUNT

    def test_list_tools_returns_mcp_types(self, tool_registry: ToolRegistry) -> None:
        """list_tools returns MCP Tool objects."""
        tools = tool_registry.list_tools()
        assert len(tools) >= 2
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_list_tools_includes_all_registered(self, tool_registry: ToolRegistry) -> None:
        """All registered tools appear in list_tools output."""
        tools = tool_registry.list_tools()
        names = {t.name for t in tools}
        assert "list_available_tools" in names
        assert "get_tool_guide" in names

    @pytest.mark.asyncio
    async def test_call_tool_routes_correctly(self, tool_registry: ToolRegistry) -> None:
        """call_tool invokes the correct tool's safe_execute."""
        result = await tool_registry.call_tool("list_available_tools", {})
        assert result.success is True
        assert isinstance(result.data, dict)

    @pytest.mark.asyncio
    async def test_call_tool_unknown_raises(self, tool_registry: ToolRegistry) -> None:
        """Unknown tool name raises ToolNotFoundError."""
        with pytest.raises(ToolNotFoundError, match="nonexistent"):
            await tool_registry.call_tool("nonexistent", {})

    def test_get_tool_returns_none_for_unknown(self, tool_registry: ToolRegistry) -> None:
        """get_tool returns None for unknown names."""
        assert tool_registry.get_tool("nonexistent") is None

    def test_get_tools_by_category(self, tool_registry: ToolRegistry) -> None:
        """Tools are grouped by category."""
        categories = tool_registry.get_tools_by_category()
        assert "meta" in categories
        meta_names = [t.name for t in categories["meta"]]
        assert "list_available_tools" in meta_names
        assert "get_tool_guide" in meta_names

    def test_tool_count(self, tool_registry: ToolRegistry) -> None:
        """tool_count returns correct number."""
        assert tool_registry.tool_count == EXPECTED_TOOL_COUNT
