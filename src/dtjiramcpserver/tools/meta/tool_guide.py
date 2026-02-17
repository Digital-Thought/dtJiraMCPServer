"""Meta-tool: get_tool_guide.

Returns detailed usage documentation for a specific tool,
including parameters, examples, and prerequisites (FR-002).
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
from dtjiramcpserver.validation.validators import validate_required


class GetToolGuideTool(BaseTool):
    """Meta-tool that returns detailed usage guide for a specific tool."""

    name = "get_tool_guide"
    category = "meta"
    description = (
        "Get detailed usage guide for a specific tool including "
        "parameters, examples, and prerequisites"
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to get the guide for",
            }
        },
        "required": ["tool_name"],
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._registry = kwargs.get("registry")

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Look up a tool by name and return its guide."""
        validate_required(arguments, "tool_name")

        if self._registry is None:
            return ToolResult.fail(
                error_type="SERVER_ERROR",
                message="Tool registry not available",
            )

        tool = self._registry.get_tool(arguments["tool_name"])
        if tool is None:
            return ToolResult.fail(
                error_type="NOT_FOUND",
                message=f"Tool '{arguments['tool_name']}' not found",
            )

        guide = tool.get_guide()
        return ToolResult.ok(data=guide.model_dump())

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Returns detailed usage documentation for a specific tool. "
                "The guide includes parameter descriptions, type information, "
                "constraints, example invocations, prerequisites, and related tools."
            ),
            parameters=[
                ParameterGuide(
                    name="tool_name",
                    type="string",
                    required=True,
                    description="Name of the tool to get the guide for",
                )
            ],
            response_format={
                "success": True,
                "data": {
                    "name": "<tool_name>",
                    "category": "<category>",
                    "description": "<detailed_description>",
                    "parameters": [
                        {
                            "name": "<param_name>",
                            "type": "<type>",
                            "required": True,
                            "description": "<description>",
                        }
                    ],
                    "examples": [
                        {
                            "description": "<example_description>",
                            "parameters": {},
                            "expected_behaviour": "<what_happens>",
                        }
                    ],
                },
            },
            examples=[
                ToolExample(
                    description="Get the guide for the jql_search tool",
                    parameters={"tool_name": "jql_search"},
                    expected_behaviour=(
                        "Returns the full usage guide for jql_search including "
                        "all parameters, examples, and prerequisites"
                    ),
                ),
                ToolExample(
                    description="Get the guide for list_available_tools",
                    parameters={"tool_name": "list_available_tools"},
                    expected_behaviour=(
                        "Returns the usage guide for the list_available_tools meta-tool"
                    ),
                ),
            ],
            related_tools=["list_available_tools"],
            notes=[
                "Use list_available_tools first to discover tool names",
                "Returns NOT_FOUND if the tool name does not exist",
            ],
        )
