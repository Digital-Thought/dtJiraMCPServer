"""Lookup tools: priority_list.

Priority enumeration via the Jira Platform REST API v3.
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
from dtjiramcpserver.validation.validators import validate_pagination


class PriorityListTool(BaseTool):
    """List all available priorities."""

    name = "priority_list"
    category = "lookup"
    description = "List all available priorities in the Jira instance"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "start": {
                "type": "integer",
                "description": "Starting index for pagination (default: 0)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
        },
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List all priorities.

        GET /priority/search returns priorities with standard pagination.
        """
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/priority/search",
            start=start,
            limit=limit,
        )

        pagination = {
            "start": paginated.start,
            "limit": paginated.limit,
            "total": paginated.total,
            "has_more": paginated.has_more,
        }

        return ToolResult.ok(data=paginated.results, pagination=pagination)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all available priorities in the Jira instance. Standard "
                "priorities include Highest, High, Medium, Low, and Lowest, but "
                "additional custom priorities may be configured. Priority IDs "
                "are used when creating or updating issues to set their priority."
            ),
            parameters=[
                ParameterGuide(
                    name="start",
                    type="integer",
                    required=False,
                    description="Starting index for pagination",
                    default=0,
                ),
                ParameterGuide(
                    name="limit",
                    type="integer",
                    required=False,
                    description="Maximum number of results to return",
                    default=50,
                    constraints="Must be between 1 and 100",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "1",
                        "name": "Highest",
                        "iconUrl": "https://example.atlassian.net/images/icons/priorities/highest.svg",
                    },
                    {
                        "id": "2",
                        "name": "High",
                        "iconUrl": "https://example.atlassian.net/images/icons/priorities/high.svg",
                    },
                    {
                        "id": "3",
                        "name": "Medium",
                        "iconUrl": "https://example.atlassian.net/images/icons/priorities/medium.svg",
                    },
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 5,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all priorities",
                    parameters={},
                    expected_behaviour=(
                        "Returns all priorities (Highest, High, Medium, Low, Lowest, etc.) "
                        "with pagination metadata"
                    ),
                ),
                ToolExample(
                    description="List priorities with custom page size",
                    parameters={"start": 0, "limit": 10},
                    expected_behaviour="Returns up to 10 priorities from the beginning",
                ),
            ],
            related_tools=["issue_create", "issue_update", "issue_type_list"],
            notes=[
                "Priority IDs are used in issue_create and issue_update to set issue priority",
                "Default priorities are Highest, High, Medium, Low, and Lowest",
                "Custom priorities configured by Jira administrators will also appear",
                "Results are paginated; use start and limit to navigate larger sets",
            ],
        )
