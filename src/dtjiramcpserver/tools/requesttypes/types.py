"""Request type tools: requesttype_list, _get, _create, _delete.

CRUD operations for JSM request types (FR-013).
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


class RequestTypeListTool(BaseTool):
    """List request types for a service desk."""

    name = "requesttype_list"
    category = "requesttypes"
    description = "List request types for a service desk"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "search_query": {
                "type": "string",
                "description": "Optional text to filter request types by name",
            },
            "group_id": {
                "type": "integer",
                "description": "Optional request type group ID to filter by",
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
        """List request types for a service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] = {}
        search_query = arguments.get("search_query")
        if search_query:
            extra_params["searchQuery"] = search_query

        group_id = arguments.get("group_id")
        if group_id is not None:
            extra_params["groupId"] = validate_integer(
                group_id, "group_id", minimum=1
            )

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/requesttype",
            start=start,
            limit=limit,
            extra_params=extra_params or None,
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
                "List request types available in a service desk. Optionally "
                "filter by name or group. Request types define the forms "
                "customers use to raise requests."
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
                    name="search_query",
                    type="string",
                    required=False,
                    description="Filter request types by name",
                ),
                ParameterGuide(
                    name="group_id",
                    type="integer",
                    required=False,
                    description="Filter by request type group ID",
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
                        "name": "Get IT Help",
                        "description": "Request IT assistance",
                        "issueTypeId": "10001",
                    }
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
                    description="List all request types",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns all request types for the service desk",
                ),
                ToolExample(
                    description="Search for request types",
                    parameters={"service_desk_id": 1, "search_query": "IT"},
                    expected_behaviour="Returns request types matching 'IT'",
                ),
            ],
            related_tools=[
                "requesttype_get",
                "requesttype_create",
                "requesttype_get_groups",
            ],
            notes=[
                "Use requesttype_get_groups to discover available group IDs",
                "Request types are tied to issue types in the underlying project",
            ],
        )


class RequestTypeGetTool(BaseTool):
    """Get details of a request type."""

    name = "requesttype_get"
    category = "requesttypes"
    description = "Get details of a request type by its ID"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "request_type_id": {
                "type": "integer",
                "description": "Request type ID",
            },
        },
        "required": ["service_desk_id", "request_type_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a single request type."""
        validate_required(arguments, "service_desk_id", "request_type_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        rt_id = validate_integer(
            arguments["request_type_id"], "request_type_id", minimum=1
        )

        result = await self._jsm_client.get(
            f"/servicedesk/{desk_id}/requesttype/{rt_id}"
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a specific request type including "
                "its name, description, help text, and linked issue type."
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
                    name="request_type_id",
                    type="integer",
                    required=True,
                    description="Request type ID",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "1",
                    "name": "Get IT Help",
                    "description": "Request IT assistance",
                    "helpText": "Use this for general IT queries",
                    "issueTypeId": "10001",
                },
            },
            examples=[
                ToolExample(
                    description="Get a request type",
                    parameters={"service_desk_id": 1, "request_type_id": 5},
                    expected_behaviour="Returns full details of the request type",
                ),
            ],
            related_tools=[
                "requesttype_list",
                "requesttype_get_fields",
            ],
            notes=[
                "Returns NOT_FOUND if the request type does not exist",
            ],
        )


class RequestTypeCreateTool(BaseTool):
    """Create a new request type."""

    name = "requesttype_create"
    category = "requesttypes"
    description = "Create a new request type in a service desk"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "name": {
                "type": "string",
                "description": "Name of the request type",
            },
            "description": {
                "type": "string",
                "description": "Description shown to customers",
            },
            "help_text": {
                "type": "string",
                "description": "Help text displayed on the request form",
            },
            "issue_type_id": {
                "type": "string",
                "description": "Issue type ID to link this request type to",
            },
        },
        "required": ["service_desk_id", "name", "issue_type_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a new request type."""
        validate_required(arguments, "service_desk_id", "name", "issue_type_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        name = validate_string(arguments["name"], "name", min_length=1, max_length=255)
        issue_type_id = validate_string(
            arguments["issue_type_id"], "issue_type_id", min_length=1
        )

        body: dict[str, Any] = {
            "name": name,
            "issueTypeId": issue_type_id,
        }

        description = arguments.get("description")
        if description:
            body["description"] = description

        help_text = arguments.get("help_text")
        if help_text:
            body["helpText"] = help_text

        result = await self._jsm_client.post(
            f"/servicedesk/{desk_id}/requesttype",
            json=body,
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new request type in a service desk. A request type "
                "defines the form customers use to raise a specific kind of "
                "request. It must be linked to an issue type."
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
                    name="name",
                    type="string",
                    required=True,
                    description="Display name for the request type",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="issue_type_id",
                    type="string",
                    required=True,
                    description="Issue type ID to link to (e.g. '10001')",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description shown to customers on the portal",
                ),
                ParameterGuide(
                    name="help_text",
                    type="string",
                    required=False,
                    description="Help text displayed on the request form",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "10",
                    "name": "New Hardware Request",
                    "issueTypeId": "10001",
                },
            },
            examples=[
                ToolExample(
                    description="Create a simple request type",
                    parameters={
                        "service_desk_id": 1,
                        "name": "New Hardware Request",
                        "issue_type_id": "10001",
                    },
                    expected_behaviour="Creates a new request type linked to the issue type",
                ),
                ToolExample(
                    description="Create with full details",
                    parameters={
                        "service_desk_id": 1,
                        "name": "VPN Access",
                        "issue_type_id": "10001",
                        "description": "Request VPN access for remote working",
                        "help_text": "Provide your employee ID and reason for access",
                    },
                    expected_behaviour="Creates a request type with description and help text",
                ),
            ],
            related_tools=[
                "requesttype_list",
                "requesttype_get_fields",
                "requesttype_delete",
            ],
            notes=[
                "Requires Service Desk Administrator permissions",
                "The issue_type_id must reference a valid issue type in the project",
                "Use field_list to discover available issue type IDs",
            ],
        )


class RequestTypeDeleteTool(BaseTool):
    """Delete a request type."""

    name = "requesttype_delete"
    category = "requesttypes"
    description = "Delete a request type from a service desk"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "request_type_id": {
                "type": "integer",
                "description": "Request type ID to delete",
            },
        },
        "required": ["service_desk_id", "request_type_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Delete a request type."""
        validate_required(arguments, "service_desk_id", "request_type_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        rt_id = validate_integer(
            arguments["request_type_id"], "request_type_id", minimum=1
        )

        await self._jsm_client.delete(
            f"/servicedesk/{desk_id}/requesttype/{rt_id}"
        )

        return ToolResult.ok(
            data={
                "service_desk_id": desk_id,
                "request_type_id": rt_id,
                "deleted": True,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Delete a request type from a service desk. This removes the "
                "request type from the customer portal. Existing issues created "
                "via this request type are not affected."
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
                    name="request_type_id",
                    type="integer",
                    required=True,
                    description="Request type ID to delete",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "service_desk_id": 1,
                    "request_type_id": 5,
                    "deleted": True,
                },
            },
            examples=[
                ToolExample(
                    description="Delete a request type",
                    parameters={"service_desk_id": 1, "request_type_id": 5},
                    expected_behaviour="Permanently removes the request type",
                ),
            ],
            related_tools=[
                "requesttype_list",
                "requesttype_create",
            ],
            notes=[
                "This action cannot be undone",
                "Requires Service Desk Administrator permissions",
                "Returns NOT_FOUND if the request type does not exist",
            ],
        )
