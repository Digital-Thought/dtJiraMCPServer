"""Service desk tools: servicedesk_get_queues, servicedesk_get_queue_issues.

Queue listing and issue retrieval for JSM service desks (FR-010).
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
from dtjiramcpserver.validation.validators import (
    validate_integer,
    validate_pagination,
    validate_required,
)


class ServiceDeskGetQueuesTool(BaseTool):
    """List queues for a service desk."""

    name = "servicedesk_get_queues"
    category = "servicedesk"
    description = "List queues for a service desk"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "include_count": {
                "type": "boolean",
                "description": "Whether to include issue counts for each queue (default: false)",
            },
            "start": {
                "type": "integer",
                "description": "Starting index for pagination (default: 0)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
        },
        "required": ["service_desk_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List queues for a service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] | None = None
        include_count = arguments.get("include_count", False)
        if include_count:
            extra_params = {"includeCount": "true"}

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/queue",
            start=start,
            limit=limit,
            extra_params=extra_params,
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
                "List all queues for a specific service desk. Optionally "
                "includes the issue count for each queue."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="include_count",
                    type="boolean",
                    required=False,
                    description="Whether to include issue counts per queue",
                    default=False,
                ),
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
                    {"id": "1", "name": "Open Requests", "issueCount": 12}
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
                    description="List queues for a service desk",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns all queues for the service desk",
                ),
                ToolExample(
                    description="List queues with issue counts",
                    parameters={"service_desk_id": 1, "include_count": True},
                    expected_behaviour="Returns queues with issue count per queue",
                ),
            ],
            related_tools=["servicedesk_get", "servicedesk_get_queue_issues"],
            notes=[
                "Returns NOT_FOUND if the service desk does not exist",
                "Issue counts are only included when include_count is true",
            ],
        )


class ServiceDeskGetQueueIssuesTool(BaseTool):
    """Get issues from a service desk queue."""

    name = "servicedesk_get_queue_issues"
    category = "servicedesk"
    description = "Get issues from a specific queue in a service desk"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "queue_id": {
                "type": "integer",
                "description": "Queue ID",
            },
            "start": {
                "type": "integer",
                "description": "Starting index for pagination (default: 0)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
        },
        "required": ["service_desk_id", "queue_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get issues from a queue."""
        validate_required(arguments, "service_desk_id", "queue_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        queue_id = validate_integer(
            arguments["queue_id"], "queue_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/queue/{queue_id}/issue",
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
                "Retrieve the issues in a specific queue within a service desk. "
                "Returns issues with only the fields configured for display in the queue."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="queue_id",
                    type="integer",
                    required=True,
                    description="Queue ID (from servicedesk_get_queues)",
                    constraints="Must be a positive integer",
                ),
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
                    {"key": "SD-1", "fields": {"summary": "Cannot log in"}}
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 12,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="Get issues from a queue",
                    parameters={"service_desk_id": 1, "queue_id": 5},
                    expected_behaviour="Returns issues in queue 5",
                ),
            ],
            related_tools=["servicedesk_get_queues", "issue_get"],
            notes=[
                "Use servicedesk_get_queues first to discover available queue IDs",
                "Returns only fields configured for queue display",
            ],
        )
