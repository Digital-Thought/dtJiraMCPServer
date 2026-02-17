"""Request type tool: requesttype_get_groups.

Retrieves request type groups for a service desk (FR-014).
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


class RequestTypeGetGroupsTool(BaseTool):
    """Get request type groups for a service desk."""

    name = "requesttype_get_groups"
    category = "requesttypes"
    description = "Get request type groups for a service desk"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
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
        """Get request type groups for a service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/requesttypegroup",
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
                "List the request type groups configured for a service desk. "
                "Groups organise request types into categories on the customer "
                "portal (e.g. 'IT Help', 'Access Requests')."
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
                    {"id": "1", "name": "General"},
                    {"id": "2", "name": "Access & Permissions"},
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 2,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List request type groups",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns all request type groups for the service desk",
                ),
            ],
            related_tools=[
                "requesttype_list",
            ],
            notes=[
                "Use group IDs with requesttype_list to filter by group",
                "Groups define the categories shown on the customer portal",
            ],
        )
