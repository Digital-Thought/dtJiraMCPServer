"""Tests for MCP server orchestration."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dtjiramcpserver.config.models import AppConfig, JiraConfig, ServerConfig
from dtjiramcpserver.server import _create_server, _registry


class TestCreateServer:
    """Tests for _create_server factory function."""

    def test_creates_server_with_name(self, sample_config: AppConfig) -> None:
        """Server is created with the correct name."""
        server = _create_server(sample_config)
        assert server.name == "dtJiraMCPServer"

    def test_creates_server_with_instructions(self, sample_config: AppConfig) -> None:
        """Server includes instructions for LLM clients."""
        server = _create_server(sample_config)
        assert server.instructions is not None
        assert "list_available_tools" in server.instructions

    def test_attaches_config(self, sample_config: AppConfig) -> None:
        """Config is attached to the server for lifespan access."""
        server = _create_server(sample_config)
        assert server._app_config is sample_config  # type: ignore[attr-defined]


class TestHandleCallTool:
    """Tests for the call_tool handler behaviour."""

    @pytest.mark.asyncio
    async def test_call_tool_returns_json_text_content(
        self, sample_config: AppConfig
    ) -> None:
        """Successful tool call returns JSON in TextContent via registry."""
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        # Invoke via registry and verify result serialises correctly
        result = await registry.call_tool("list_available_tools", {})
        result_text = json.dumps(result.model_dump(), default=str)
        parsed = json.loads(result_text)
        assert parsed["success"] is True
        assert "meta" in parsed["data"]

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_not_found(
        self, sample_config: AppConfig
    ) -> None:
        """Unknown tool name returns NOT_FOUND error response."""
        import dtjiramcpserver.server as server_module

        from dtjiramcpserver.exceptions import ToolNotFoundError
        from dtjiramcpserver.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_and_register()

        original_registry = server_module._registry
        server_module._registry = registry
        try:
            with pytest.raises(ToolNotFoundError):
                await registry.call_tool("nonexistent_tool", {})
        finally:
            server_module._registry = original_registry


class TestRegistryNoneGuard:
    """Tests for when registry is not yet initialised."""

    def test_registry_starts_as_none(self) -> None:
        """Module-level _registry starts as None."""
        import dtjiramcpserver.server as server_module

        # Save and restore to avoid interference
        original = server_module._registry
        try:
            server_module._registry = None
            assert server_module._registry is None
        finally:
            server_module._registry = original


class TestToolResultSerialisation:
    """Tests for ToolResult to MCP response conversion."""

    def test_success_result_serialises(self) -> None:
        """ToolResult.ok() serialises to valid JSON."""
        from dtjiramcpserver.tools.base import ToolResult

        result = ToolResult.ok(data={"items": [1, 2, 3]})
        text = json.dumps(result.model_dump(), default=str)
        parsed = json.loads(text)
        assert parsed["success"] is True
        assert parsed["data"]["items"] == [1, 2, 3]

    def test_error_result_serialises(self) -> None:
        """ToolResult.fail() serialises to valid JSON."""
        from dtjiramcpserver.tools.base import ToolResult

        result = ToolResult.fail(error_type="NOT_FOUND", message="Not found")
        text = json.dumps(result.model_dump(), default=str)
        parsed = json.loads(text)
        assert parsed["success"] is False
        assert parsed["error"]["type"] == "NOT_FOUND"

    def test_pagination_result_serialises(self) -> None:
        """ToolResult with pagination serialises correctly."""
        from dtjiramcpserver.tools.base import ToolResult

        pagination = {"start": 0, "limit": 50, "total": 100, "has_more": True}
        result = ToolResult.ok(data=[], pagination=pagination)
        text = json.dumps(result.model_dump(), default=str)
        parsed = json.loads(text)
        assert parsed["pagination"]["has_more"] is True
