"""Service desk tools: servicedesk_list, servicedesk_get.

List and retrieve service desks from JSM (FR-009).
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


class ServiceDeskListTool(BaseTool):
    """List all accessible service desks."""

    name = "servicedesk_list"
    category = "servicedesk"
    description = "List all accessible service desks with pagination"
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
        """List all service desks."""
        start, limit = validate_pagination(arguments)

        paginated = await self._jsm_client.list_paginated(
            "/servicedesk",
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
                "List all service desks accessible to the authenticated user. "
                "Returns basic details including ID, project key, and name."
            ),
            parameters=[
                ParameterGuide(
                    name="start",
                    type="integer",
                    required=False,
                    description="Starting index for pagination",
                    default=0,
                    constraints="Must be >= 0",
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
                        "projectId": "10001",
                        "projectKey": "SD",
                        "projectName": "Service Desk",
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 3,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all service desks",
                    parameters={},
                    expected_behaviour="Returns all accessible service desks with pagination",
                ),
                ToolExample(
                    description="List with pagination",
                    parameters={"start": 0, "limit": 10},
                    expected_behaviour="Returns up to 10 service desks",
                ),
            ],
            related_tools=["servicedesk_get", "servicedesk_get_queues"],
            notes=[
                "Returns only service desks the authenticated user has access to",
                "Use the returned ID in other servicedesk_* tools",
            ],
        )


class ServiceDeskGetTool(BaseTool):
    """Get details of a single service desk."""

    name = "servicedesk_get"
    category = "servicedesk"
    description = "Get details of a service desk by its ID"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
        },
        "required": ["service_desk_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a single service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )

        result = await self._jsm_client.get(f"/servicedesk/{desk_id}")

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a specific service desk by its ID, "
                "including project information and links."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID (numeric)",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "1",
                    "projectId": "10001",
                    "projectKey": "SD",
                    "projectName": "Service Desk",
                },
            },
            examples=[
                ToolExample(
                    description="Get a service desk by ID",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns full details of the service desk",
                ),
            ],
            related_tools=["servicedesk_list", "servicedesk_get_queues"],
            notes=[
                "Returns NOT_FOUND if the service desk does not exist",
                "Returns PERMISSION_ERROR if the user lacks access",
            ],
        )
