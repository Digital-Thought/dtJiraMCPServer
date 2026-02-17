"""Tests for self-documentation meta-tools."""

from __future__ import annotations

import pytest

from dtjiramcpserver.tools.registry import ToolRegistry


class TestListAvailableTools:
    """Tests for list_available_tools meta-tool."""

    @pytest.mark.asyncio
    async def test_returns_categories(self, tool_registry: ToolRegistry) -> None:
        """Returns tools grouped by category."""
        result = await tool_registry.call_tool("list_available_tools", {})
        assert result.success is True
        assert "meta" in result.data
        meta_tools = result.data["meta"]
        assert len(meta_tools) == 2
        names = {t["name"] for t in meta_tools}
        assert "list_available_tools" in names
        assert "get_tool_guide" in names

    @pytest.mark.asyncio
    async def test_tool_entries_have_name_and_description(self, tool_registry: ToolRegistry) -> None:
        """Each tool entry has name and description."""
        result = await tool_registry.call_tool("list_available_tools", {})
        for category, tools in result.data.items():
            for tool in tools:
                assert "name" in tool
                assert "description" in tool

    def test_get_guide(self, tool_registry: ToolRegistry) -> None:
        """list_available_tools has a valid guide."""
        tool = tool_registry.get_tool("list_available_tools")
        assert tool is not None
        guide = tool.get_guide()
        assert guide.name == "list_available_tools"
        assert guide.category == "meta"
        assert "get_tool_guide" in (guide.related_tools or [])


class TestGetToolGuide:
    """Tests for get_tool_guide meta-tool."""

    @pytest.mark.asyncio
    async def test_valid_tool_returns_guide(self, tool_registry: ToolRegistry) -> None:
        """Returns guide data for a valid tool name."""
        result = await tool_registry.call_tool(
            "get_tool_guide", {"tool_name": "list_available_tools"}
        )
        assert result.success is True
        assert result.data["name"] == "list_available_tools"
        assert result.data["category"] == "meta"
        assert "description" in result.data

    @pytest.mark.asyncio
    async def test_missing_tool_returns_not_found(self, tool_registry: ToolRegistry) -> None:
        """Returns NOT_FOUND error for nonexistent tool."""
        result = await tool_registry.call_tool(
            "get_tool_guide", {"tool_name": "nonexistent_tool"}
        )
        assert result.success is False
        assert result.error is not None
        assert result.error["type"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_missing_tool_name_returns_validation_error(
        self, tool_registry: ToolRegistry
    ) -> None:
        """Returns VALIDATION_ERROR when tool_name is missing."""
        result = await tool_registry.call_tool("get_tool_guide", {})
        assert result.success is False
        assert result.error is not None
        assert result.error["type"] == "VALIDATION_ERROR"

    def test_get_guide(self, tool_registry: ToolRegistry) -> None:
        """get_tool_guide has a valid guide with examples."""
        tool = tool_registry.get_tool("get_tool_guide")
        assert tool is not None
        guide = tool.get_guide()
        assert guide.name == "get_tool_guide"
        assert len(guide.parameters) == 1
        assert guide.parameters[0].name == "tool_name"
        assert guide.parameters[0].required is True
        assert len(guide.examples) >= 1
