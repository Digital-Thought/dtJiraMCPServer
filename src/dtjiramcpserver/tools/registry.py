"""Tool registry with auto-discovery for MCP tool registration.

Scans configured packages for BaseTool subclasses, instantiates them
with the provided API clients, and provides the interface that maps
to the MCP protocol's tools/list and tools/call methods.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from typing import Any

from mcp import types as mcp_types

from dtjiramcpserver.exceptions import ToolNotFoundError
from dtjiramcpserver.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Packages to scan for tool classes. Empty packages are silently skipped.
TOOL_PACKAGES = [
    "dtjiramcpserver.tools.meta",
    "dtjiramcpserver.tools.issues",
    "dtjiramcpserver.tools.servicedesk",
    "dtjiramcpserver.tools.requesttypes",
    "dtjiramcpserver.tools.fields",
    "dtjiramcpserver.tools.workflows",
    "dtjiramcpserver.tools.knowledgebase",
    "dtjiramcpserver.tools.sla",
    "dtjiramcpserver.tools.assets",
    "dtjiramcpserver.tools.projects",
    "dtjiramcpserver.tools.lookup",
    "dtjiramcpserver.tools.groups",
]


class ToolRegistry:
    """Registry for auto-discovering and managing MCP tools.

    Provides the interface that maps directly to the MCP protocol's
    tools/list and tools/call methods.
    """

    def __init__(
        self,
        platform_client: Any = None,
        jsm_client: Any = None,
        read_only: bool = False,
    ) -> None:
        self._platform_client = platform_client
        self._jsm_client = jsm_client
        self._read_only = read_only
        self._tools: dict[str, BaseTool] = {}

    @property
    def read_only(self) -> bool:
        """Return whether the registry is in read-only mode."""
        return self._read_only

    def discover_and_register(self) -> None:
        """Scan TOOL_PACKAGES for BaseTool subclasses and register them.

        Each package's __init__.py should export its tool classes.
        Classes are instantiated with the API clients and registered
        by their name attribute.
        """
        for package_name in TOOL_PACKAGES:
            try:
                package = importlib.import_module(package_name)
            except ImportError:
                logger.debug("Package %s not found, skipping", package_name)
                continue

            for attr_name in dir(package):
                attr = getattr(package, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                    and hasattr(attr, "name")
                    and isinstance(getattr(attr, "name", None), str)
                ):
                    self._register_tool_class(attr)

    def _register_tool_class(self, tool_cls: type[BaseTool]) -> None:
        """Instantiate and register a single tool class."""
        if self._read_only and getattr(tool_cls, "mutates", False):
            logger.info(
                "Skipping mutating tool '%s' (read-only mode)",
                getattr(tool_cls, "name", "unknown"),
            )
            return

        tool = tool_cls(
            platform_client=self._platform_client,
            jsm_client=self._jsm_client,
            registry=self,
        )
        if tool.name in self._tools:
            logger.warning("Duplicate tool name '%s', overwriting", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s (category: %s)", tool.name, tool.category)

    def list_tools(self) -> list[mcp_types.Tool]:
        """Return MCP Tool objects for all registered tools.

        Maps directly to the MCP protocol's tools/list response.
        """
        return [
            mcp_types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            )
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Route a tool call to the appropriate handler.

        Maps directly to the MCP protocol's tools/call routing.

        Args:
            name: Tool name from the MCP client.
            arguments: Tool parameters from the MCP client.

        Returns:
            ToolResult from the tool's safe_execute() method.

        Raises:
            ToolNotFoundError: If no tool with the given name exists.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return await tool.safe_execute(arguments)

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool instance by name.

        Used by the get_tool_guide meta-tool.
        """
        return self._tools.get(name)

    def get_tools_by_category(self) -> dict[str, list[BaseTool]]:
        """Group registered tools by category.

        Used by the list_available_tools meta-tool.
        """
        categories: dict[str, list[BaseTool]] = {}
        for tool in self._tools.values():
            categories.setdefault(tool.category, []).append(tool)
        return categories

    @property
    def tool_count(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)
