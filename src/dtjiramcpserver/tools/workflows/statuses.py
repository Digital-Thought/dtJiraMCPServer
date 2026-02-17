"""Workflow tools: status_list, status_get, status_create.

Status management via the Jira Platform REST API v3 (FR-020).
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
    validate_enum,
    validate_pagination,
    validate_required,
    validate_string,
)


class StatusListTool(BaseTool):
    """List all statuses."""

    name = "status_list"
    category = "workflows"
    description = "List all Jira statuses with optional category filtering"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "status_category": {
                "type": "string",
                "description": (
                    "Filter by category: 'TODO', 'IN_PROGRESS', or 'DONE'"
                ),
            },
            "search_string": {
                "type": "string",
                "description": "Search string to filter statuses by name",
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
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List all statuses with optional filtering."""
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] = {}

        status_category = arguments.get("status_category")
        if status_category:
            validate_enum(
                status_category,
                "status_category",
                ["TODO", "IN_PROGRESS", "DONE"],
            )
            extra_params["statusCategory"] = status_category

        search_string = arguments.get("search_string")
        if search_string:
            extra_params["searchString"] = search_string

        paginated = await self._platform_client.list_paginated(
            "/statuses/search",
            start=start,
            limit=limit,
            extra_params=extra_params if extra_params else None,
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
                "List all statuses in the Jira instance. Statuses represent "
                "the states that issues can be in (e.g. Open, In Progress, Done). "
                "Optionally filter by status category."
            ),
            parameters=[
                ParameterGuide(
                    name="status_category",
                    type="string",
                    required=False,
                    description="Filter by status category",
                    valid_values=["TODO", "IN_PROGRESS", "DONE"],
                ),
                ParameterGuide(
                    name="search_string",
                    type="string",
                    required=False,
                    description="Search string to filter statuses by name",
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
                    {
                        "id": "1",
                        "name": "Open",
                        "statusCategory": "TODO",
                    },
                    {
                        "id": "3",
                        "name": "In Progress",
                        "statusCategory": "IN_PROGRESS",
                    },
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
                    description="List all statuses",
                    parameters={},
                    expected_behaviour="Returns all statuses with pagination",
                ),
                ToolExample(
                    description="List in-progress statuses",
                    parameters={"status_category": "IN_PROGRESS"},
                    expected_behaviour="Returns only IN_PROGRESS category statuses",
                ),
            ],
            related_tools=["status_get", "status_create", "workflow_list"],
            notes=[
                "Status categories are: TODO, IN_PROGRESS, DONE",
                "Use status IDs with workflow_create to define workflow statuses",
            ],
        )


class StatusGetTool(BaseTool):
    """Get a status by ID or name."""

    name = "status_get"
    category = "workflows"
    description = "Get details of a status by its ID or name"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "status_id_or_name": {
                "type": "string",
                "description": "Status ID or name",
            },
        },
        "required": ["status_id_or_name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a status by ID or name."""
        validate_required(arguments, "status_id_or_name")
        status_id = validate_string(
            arguments["status_id_or_name"], "status_id_or_name", min_length=1
        )

        result = await self._platform_client.get(f"/status/{status_id}")

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve details of a specific status by its ID or name. "
                "Returns the status name, description, and category."
            ),
            parameters=[
                ParameterGuide(
                    name="status_id_or_name",
                    type="string",
                    required=True,
                    description="Status ID or name (from status_list)",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "1",
                    "name": "Open",
                    "description": "The issue is open.",
                    "statusCategory": {
                        "id": 2,
                        "key": "new",
                        "name": "To Do",
                    },
                },
            },
            examples=[
                ToolExample(
                    description="Get a status by ID",
                    parameters={"status_id_or_name": "1"},
                    expected_behaviour="Returns the status details",
                ),
                ToolExample(
                    description="Get a status by name",
                    parameters={"status_id_or_name": "Open"},
                    expected_behaviour="Returns the status details",
                ),
            ],
            related_tools=["status_list", "status_create"],
            notes=[
                "Returns NOT_FOUND if the status does not exist",
                "Accepts either numeric ID or status name",
            ],
        )


class StatusCreateTool(BaseTool):
    """Create new statuses."""

    name = "status_create"
    category = "workflows"
    description = "Create one or more new statuses"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the new status",
            },
            "status_category": {
                "type": "string",
                "description": "Status category: 'TODO', 'IN_PROGRESS', or 'DONE'",
            },
            "description": {
                "type": "string",
                "description": "Description of the status",
            },
            "scope_type": {
                "type": "string",
                "description": "Scope type: 'PROJECT' (default: 'PROJECT')",
            },
            "scope_project_id": {
                "type": "string",
                "description": "Project ID for the status scope",
            },
        },
        "required": ["name", "status_category"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a status."""
        validate_required(arguments, "name", "status_category")
        name = validate_string(
            arguments["name"], "name", min_length=1, max_length=255
        )
        status_category = validate_enum(
            arguments["status_category"],
            "status_category",
            ["TODO", "IN_PROGRESS", "DONE"],
        )

        status_entry: dict[str, Any] = {
            "name": name,
            "statusCategory": status_category,
        }

        description = arguments.get("description")
        if description:
            status_entry["description"] = description

        scope: dict[str, Any] = {
            "type": arguments.get("scope_type", "PROJECT"),
        }
        scope_project_id = arguments.get("scope_project_id")
        if scope_project_id:
            scope["project"] = {"id": scope_project_id}

        body: dict[str, Any] = {
            "scope": scope,
            "statuses": [status_entry],
        }

        result = await self._platform_client.post("/statuses", json=body)

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new status in Jira. Statuses must belong to one of "
                "three categories: TODO, IN_PROGRESS, or DONE. The status "
                "must be scoped to a project."
            ),
            parameters=[
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Name for the new status",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="status_category",
                    type="string",
                    required=True,
                    description="Status category",
                    valid_values=["TODO", "IN_PROGRESS", "DONE"],
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description of the status",
                ),
                ParameterGuide(
                    name="scope_type",
                    type="string",
                    required=False,
                    description="Scope type for the status",
                    default="PROJECT",
                ),
                ParameterGuide(
                    name="scope_project_id",
                    type="string",
                    required=False,
                    description="Project ID for the status scope",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "10100",
                        "name": "Awaiting Review",
                        "statusCategory": "IN_PROGRESS",
                    }
                ],
            },
            examples=[
                ToolExample(
                    description="Create a new status",
                    parameters={
                        "name": "Awaiting Review",
                        "status_category": "IN_PROGRESS",
                        "scope_project_id": "10001",
                    },
                    expected_behaviour="Creates a new IN_PROGRESS status",
                ),
            ],
            related_tools=["status_list", "workflow_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "Status categories: TODO (not started), IN_PROGRESS (in progress), DONE (completed)",
                "Created statuses can be used in workflow_create",
            ],
        )
