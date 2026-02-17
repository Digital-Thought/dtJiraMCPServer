"""Field tools: screen_scheme_list, screen_scheme_get.

Screen scheme management via the Jira Platform REST API v3 (FR-018).
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


class ScreenSchemeListTool(BaseTool):
    """List all screen schemes."""

    name = "screen_scheme_list"
    category = "fields"
    description = "List all screen schemes with pagination"
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
        """List all screen schemes."""
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/screenscheme",
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
                "List all screen schemes in the Jira instance. Screen schemes "
                "map operations (create, edit, view) to specific screens."
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
                        "id": 1,
                        "name": "Default Screen Scheme",
                        "screens": {
                            "default": {"id": 1, "name": "Default Screen"},
                        },
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
                    description="List all screen schemes",
                    parameters={},
                    expected_behaviour="Returns all screen schemes with pagination",
                ),
            ],
            related_tools=["screen_scheme_get", "screen_list"],
            notes=[
                "Requires Jira Administrator permissions",
                "Screen schemes are assigned to issue type screen schemes",
            ],
        )


class ScreenSchemeGetTool(BaseTool):
    """Get details of a screen scheme."""

    name = "screen_scheme_get"
    category = "fields"
    description = "Get details of a screen scheme by its ID"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "screen_scheme_id": {
                "type": "integer",
                "description": "Screen scheme ID",
            },
        },
        "required": ["screen_scheme_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a screen scheme by filtering the list endpoint by ID."""
        validate_required(arguments, "screen_scheme_id")
        scheme_id = validate_integer(
            arguments["screen_scheme_id"], "screen_scheme_id", minimum=1
        )

        # The API supports filtering by ID via query parameter
        response = await self._platform_client.get(
            "/screenscheme",
            params={"id": scheme_id},
        )

        values = response.get("values", [])
        if not values:
            from dtjiramcpserver.exceptions import NotFoundError

            raise NotFoundError(
                message=f"Screen scheme {scheme_id} not found",
            )

        return ToolResult.ok(data=values[0])

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a specific screen scheme, including "
                "the screens mapped to each operation (create, edit, view, default)."
            ),
            parameters=[
                ParameterGuide(
                    name="screen_scheme_id",
                    type="integer",
                    required=True,
                    description="Screen scheme ID (from screen_scheme_list)",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": 1,
                    "name": "Default Screen Scheme",
                    "screens": {
                        "default": {"id": 1, "name": "Default Screen"},
                        "create": {"id": 2, "name": "Create Screen"},
                    },
                },
            },
            examples=[
                ToolExample(
                    description="Get a screen scheme",
                    parameters={"screen_scheme_id": 1},
                    expected_behaviour="Returns the screen scheme with mapped screens",
                ),
            ],
            related_tools=["screen_scheme_list", "screen_get"],
            notes=[
                "Returns NOT_FOUND if the screen scheme does not exist",
                "The 'default' screen is used for any operation without a specific mapping",
            ],
        )
