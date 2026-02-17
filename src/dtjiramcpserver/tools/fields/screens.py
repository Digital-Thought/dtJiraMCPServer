"""Field tools: screen_list, screen_get, screen_add_field.

Screen management via the Jira Platform REST API v3 (FR-017).
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
    validate_string,
)


class ScreenListTool(BaseTool):
    """List all screens."""

    name = "screen_list"
    category = "fields"
    description = "List all Jira screens with pagination"
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
        """List all screens."""
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/screens",
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
                "List all screens in the Jira instance. Screens define which "
                "fields are displayed when creating, editing, or viewing issues."
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
                    {"id": 1, "name": "Default Screen"},
                    {"id": 2, "name": "Bug Screen"},
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 10,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all screens",
                    parameters={},
                    expected_behaviour="Returns all screens with pagination",
                ),
            ],
            related_tools=["screen_get", "screen_add_field", "screen_scheme_list"],
            notes=[
                "Requires Jira Administrator permissions",
                "Use the screen ID with screen_get to see tabs and fields",
            ],
        )


class ScreenGetTool(BaseTool):
    """Get screen details including tabs and fields."""

    name = "screen_get"
    category = "fields"
    description = "Get a screen's tabs and fields"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "screen_id": {
                "type": "integer",
                "description": "Screen ID",
            },
        },
        "required": ["screen_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get screen tabs (which include fields)."""
        validate_required(arguments, "screen_id")
        screen_id = validate_integer(
            arguments["screen_id"], "screen_id", minimum=1
        )

        result = await self._platform_client.get(
            f"/screens/{screen_id}/tabs"
        )

        # The API returns an array of tabs
        tabs = result if isinstance(result, list) else []

        return ToolResult.ok(data=tabs)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve the tabs and their field layout for a specific screen. "
                "Each tab contains the fields displayed in that section of the screen."
            ),
            parameters=[
                ParameterGuide(
                    name="screen_id",
                    type="integer",
                    required=True,
                    description="Screen ID (from screen_list)",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": 10001,
                        "name": "Field Tab",
                        "fields": [
                            {"id": "summary", "name": "Summary"},
                            {"id": "description", "name": "Description"},
                        ],
                    }
                ],
            },
            examples=[
                ToolExample(
                    description="Get screen details",
                    parameters={"screen_id": 1},
                    expected_behaviour="Returns the screen's tabs and their fields",
                ),
            ],
            related_tools=["screen_list", "screen_add_field"],
            notes=[
                "Returns NOT_FOUND if the screen does not exist",
                "Each screen has at least one tab",
                "Use tab IDs with screen_add_field to add fields",
            ],
        )


class ScreenAddFieldTool(BaseTool):
    """Add a field to a screen tab."""

    name = "screen_add_field"
    category = "fields"
    description = "Add a field to a screen tab"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "screen_id": {
                "type": "integer",
                "description": "Screen ID",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID within the screen",
            },
            "field_id": {
                "type": "string",
                "description": "Field ID to add (e.g. 'customfield_10001')",
            },
        },
        "required": ["screen_id", "tab_id", "field_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Add a field to a screen tab."""
        validate_required(arguments, "screen_id", "tab_id", "field_id")
        screen_id = validate_integer(
            arguments["screen_id"], "screen_id", minimum=1
        )
        tab_id = validate_integer(
            arguments["tab_id"], "tab_id", minimum=1
        )
        field_id = validate_string(arguments["field_id"], "field_id", min_length=1)

        result = await self._platform_client.post(
            f"/screens/{screen_id}/tabs/{tab_id}/fields",
            json={"fieldId": field_id},
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Add a field to a specific tab on a screen. This makes the "
                "field visible on issues that use this screen."
            ),
            parameters=[
                ParameterGuide(
                    name="screen_id",
                    type="integer",
                    required=True,
                    description="Screen ID",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="tab_id",
                    type="integer",
                    required=True,
                    description="Tab ID within the screen (from screen_get)",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="field_id",
                    type="string",
                    required=True,
                    description="Field ID to add (e.g. 'customfield_10001' or 'summary')",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "customfield_10001",
                    "name": "Story Points",
                },
            },
            examples=[
                ToolExample(
                    description="Add a custom field to a screen",
                    parameters={
                        "screen_id": 1,
                        "tab_id": 10001,
                        "field_id": "customfield_10001",
                    },
                    expected_behaviour="Adds the field to the specified screen tab",
                ),
            ],
            related_tools=["screen_get", "screen_list", "field_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "Use screen_get to discover available tab IDs",
                "Returns CONFLICT if the field is already on the screen",
            ],
        )
