"""Lookup tools: issue_type_list.

Issue type enumeration via the Jira Platform REST API v3.
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


class IssueTypeListTool(BaseTool):
    """List all available issue types."""

    name = "issue_type_list"
    category = "lookup"
    description = "List all available issue types in the Jira instance"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List all issue types.

        GET /issuetype returns all issue types as a flat array (no pagination).
        """
        result = await self._platform_client.get("/issuetype")

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all available issue types in the Jira instance, including "
                "standard types such as Epic, Story, Task, Bug, and Sub-task, as "
                "well as any custom issue types that have been configured. The "
                "returned issue type IDs are required when creating issues with "
                "issue_create."
            ),
            parameters=[],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "10001",
                        "name": "Story",
                        "description": "A user story",
                        "subtask": False,
                        "hierarchyLevel": 0,
                    },
                    {
                        "id": "10002",
                        "name": "Bug",
                        "description": "A problem which impairs or prevents the functions of the product",
                        "subtask": False,
                        "hierarchyLevel": 0,
                    },
                    {
                        "id": "10003",
                        "name": "Sub-task",
                        "description": "A sub-task of an issue",
                        "subtask": True,
                        "hierarchyLevel": -1,
                    },
                ],
            },
            examples=[
                ToolExample(
                    description="List all issue types",
                    parameters={},
                    expected_behaviour=(
                        "Returns all issue types including Epic, Story, Task, Bug, "
                        "Sub-task, and any custom issue types"
                    ),
                ),
            ],
            related_tools=["issue_create", "field_list", "priority_list"],
            notes=[
                "Returns all issue types in a single response (no pagination)",
                "Issue type IDs are required by issue_create to specify the type of issue",
                "Sub-tasks have 'subtask' set to true and a negative hierarchyLevel",
                "Custom issue types configured by Jira administrators will also appear",
            ],
        )
