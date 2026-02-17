"""MCP server orchestration using the low-level Server API.

Creates the MCP Server instance, wires up list_tools and call_tool
handlers to the ToolRegistry, and provides the async run function
for stdio transport.

This module eliminates the need for a separate transports/ package
as the MCP SDK handles all stdio protocol details natively.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.server.stdio
import mcp.types as mcp_types
from mcp.server import Server

from dtjiramcpserver import __version__
from dtjiramcpserver.client.jsm import JsmClient
from dtjiramcpserver.client.platform import PlatformClient
from dtjiramcpserver.client.rate_limiter import RateLimiter
from dtjiramcpserver.config.models import AppConfig
from dtjiramcpserver.exceptions import ToolNotFoundError
from dtjiramcpserver.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# Module-level references populated during lifespan
_registry: ToolRegistry | None = None


@asynccontextmanager
async def _server_lifespan(server: Server) -> AsyncIterator[dict[str, Any]]:
    """Manage server startup and shutdown lifecycle.

    Creates HTTP clients, validates credentials, discovers tools.
    Cleans up clients on shutdown.
    """
    global _registry  # noqa: PLW0603

    config: AppConfig = server._app_config  # type: ignore[attr-defined]

    rate_limiter = RateLimiter()

    platform_client = PlatformClient(config.jira, rate_limiter)
    jsm_client = JsmClient(config.jira, rate_limiter)

    # Connect clients and validate credentials
    await platform_client.connect()
    user_info = await platform_client.validate_credentials()
    logger.info(
        "Authenticated as %s (%s)",
        user_info.get("displayName", "unknown"),
        user_info.get("emailAddress", "unknown"),
    )

    await jsm_client.connect()
    logger.info("JSM API client connected")

    # Discover and register tools
    registry = ToolRegistry(
        platform_client=platform_client,
        jsm_client=jsm_client,
    )
    registry.discover_and_register()
    logger.info("Tool registry populated with %d tools", registry.tool_count)

    _registry = registry

    try:
        yield {
            "platform_client": platform_client,
            "jsm_client": jsm_client,
            "registry": registry,
        }
    finally:
        _registry = None
        await jsm_client.disconnect()
        await platform_client.disconnect()
        logger.info("Clients disconnected")


def _create_server(config: AppConfig) -> Server:
    """Create and configure the MCP Server with tool handlers."""

    server = Server(
        name="dtJiraMCPServer",
        version=__version__,
        instructions=(
            "Jira Cloud and JSM Cloud administration server. "
            "Use list_available_tools to discover capabilities, "
            "then get_tool_guide for detailed usage of specific tools."
        ),
        lifespan=_server_lifespan,
    )

    # Attach config so the lifespan can access it
    server._app_config = config  # type: ignore[attr-defined]

    @server.list_tools()
    async def handle_list_tools() -> list[mcp_types.Tool]:
        """MCP protocol handler for tools/list."""
        if _registry is None:
            return []
        return _registry.list_tools()

    @server.call_tool()
    async def handle_call_tool(
        name: str,
        arguments: dict[str, Any] | None,
    ) -> list[mcp_types.TextContent]:
        """MCP protocol handler for tools/call."""
        if _registry is None:
            error_result = {"success": False, "error": {"type": "SERVER_ERROR", "message": "Server not ready"}}
            return [mcp_types.TextContent(type="text", text=json.dumps(error_result))]

        args = arguments or {}

        logger.info("Tool invoked: %s", name)
        logger.debug("Tool arguments: %s", args)

        try:
            result = await _registry.call_tool(name, args)
        except ToolNotFoundError:
            result_data = {
                "success": False,
                "error": {"type": "NOT_FOUND", "message": f"Tool '{name}' not found"},
            }
            return [mcp_types.TextContent(type="text", text=json.dumps(result_data))]

        result_text = json.dumps(result.model_dump(), default=str)
        return [mcp_types.TextContent(type="text", text=result_text)]

    return server


async def run_stdio_server(config: AppConfig) -> None:
    """Run the MCP server with stdio transport.

    This function blocks until the MCP client disconnects (stdin closes).
    """
    server = _create_server(config)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("stdio transport ready, awaiting MCP client connection")
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)

    logger.info("MCP client disconnected, server shutting down")
