"""Meta-tool: list_available_tools.

Lists all available tools grouped by feature category, enabling
the LLM to discover the server's capabilities (FR-001).
"""

from __future__ import annotations

from typing import Any

from dtjiramcpserver.tools.base import (
    BaseTool,
    ParameterGuide,
    ToolExample,
    ToolGuide,
    ToolResult,
)


class ListAvailableToolsTool(BaseTool):
    """Meta-tool that lists all available tools grouped by category."""

    name = "list_available_tools"
    category = "meta"
    description = "List all available tools grouped by feature category"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._registry = kwargs.get("registry")

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Return all tools grouped by category."""
        if self._registry is None:
            return ToolResult.fail(
                error_type="SERVER_ERROR",
                message="Tool registry not available",
            )

        categories = self._registry.get_tools_by_category()
        result: dict[str, list[dict[str, str]]] = {}
        for cat_name, tools in sorted(categories.items()):
            result[cat_name] = [
                {"name": t.name, "description": t.description}
                for t in sorted(tools, key=lambda t: t.name)
            ]
        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Lists all available tools grouped by feature category. "
                "Use this tool first to discover what operations are available, "
                "then use get_tool_guide to get detailed usage for a specific tool."
            ),
            parameters=[],
            response_format={
                "success": True,
                "data": {
                    "<category>": [
                        {"name": "<tool_name>", "description": "<brief_description>"}
                    ]
                },
            },
            examples=[
                ToolExample(
                    description="List all available tools",
                    parameters={},
                    expected_behaviour=(
                        "Returns a dictionary with category names as keys and "
                        "lists of tool summaries as values"
                    ),
                )
            ],
            related_tools=["get_tool_guide"],
            notes=[
                "This tool takes no parameters",
                "Use the returned tool names with get_tool_guide for detailed usage",
            ],
        )
