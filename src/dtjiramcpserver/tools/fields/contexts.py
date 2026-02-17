"""Field tools: field_get_contexts, field_add_context.

Field context management via the Jira Platform REST API v3 (FR-016).
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
    validate_pagination,
    validate_required,
    validate_string,
)


class FieldGetContextsTool(BaseTool):
    """Get contexts for a custom field."""

    name = "field_get_contexts"
    category = "fields"
    description = "Get the contexts for a custom field"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "field_id": {
                "type": "string",
                "description": "Custom field ID (e.g. 'customfield_10001')",
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
        "required": ["field_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get contexts for a custom field."""
        validate_required(arguments, "field_id")
        field_id = validate_string(arguments["field_id"], "field_id", min_length=1)
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            f"/field/{field_id}/context",
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
                "Retrieve the contexts configured for a custom field. Contexts "
                "control which projects and issue types the field applies to."
            ),
            parameters=[
                ParameterGuide(
                    name="field_id",
                    type="string",
                    required=True,
                    description="Custom field ID (e.g. 'customfield_10001')",
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
                        "id": "10100",
                        "name": "Default Context",
                        "isGlobalContext": True,
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 1,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="Get contexts for a custom field",
                    parameters={"field_id": "customfield_10001"},
                    expected_behaviour="Returns all contexts for the field",
                ),
            ],
            related_tools=["field_add_context", "field_list"],
            notes=[
                "A global context applies the field to all projects",
                "Project-scoped contexts limit the field to specific projects",
            ],
        )


class FieldAddContextTool(BaseTool):
    """Add a context to a custom field."""

    name = "field_add_context"
    category = "fields"
    description = "Add a context to a custom field"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "field_id": {
                "type": "string",
                "description": "Custom field ID (e.g. 'customfield_10001')",
            },
            "name": {
                "type": "string",
                "description": "Name for the context",
            },
            "description": {
                "type": "string",
                "description": "Description of the context",
            },
            "project_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Project IDs to scope this context to (omit for global)",
            },
            "issue_type_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Issue type IDs to scope this context to (omit for all types)",
            },
        },
        "required": ["field_id", "name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Add a context to a custom field."""
        validate_required(arguments, "field_id", "name")
        field_id = validate_string(arguments["field_id"], "field_id", min_length=1)
        name = validate_string(arguments["name"], "name", min_length=1, max_length=255)

        body: dict[str, Any] = {"name": name}

        description = arguments.get("description")
        if description:
            body["description"] = description

        project_ids = arguments.get("project_ids")
        if project_ids:
            body["projectIds"] = project_ids

        issue_type_ids = arguments.get("issue_type_ids")
        if issue_type_ids:
            body["issueTypeIds"] = issue_type_ids

        result = await self._platform_client.post(
            f"/field/{field_id}/context",
            json=body,
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Add a context to a custom field. Contexts control which "
                "projects and issue types the field applies to. Omit "
                "project_ids and issue_type_ids for a global context."
            ),
            parameters=[
                ParameterGuide(
                    name="field_id",
                    type="string",
                    required=True,
                    description="Custom field ID (e.g. 'customfield_10001')",
                ),
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Name for the context",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description of the context",
                ),
                ParameterGuide(
                    name="project_ids",
                    type="array[string]",
                    required=False,
                    description="Project IDs to scope to (omit for global)",
                ),
                ParameterGuide(
                    name="issue_type_ids",
                    type="array[string]",
                    required=False,
                    description="Issue type IDs to scope to (omit for all types)",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "10200",
                    "name": "Project ABC Context",
                },
            },
            examples=[
                ToolExample(
                    description="Add a project-scoped context",
                    parameters={
                        "field_id": "customfield_10001",
                        "name": "Project ABC Context",
                        "project_ids": ["10001"],
                    },
                    expected_behaviour="Creates a context scoped to project 10001",
                ),
                ToolExample(
                    description="Add a global context",
                    parameters={
                        "field_id": "customfield_10001",
                        "name": "Global Context",
                    },
                    expected_behaviour="Creates a global context for the field",
                ),
            ],
            related_tools=["field_get_contexts", "field_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "A field can have multiple contexts with different scopes",
                "Omitting project_ids creates a global context",
            ],
        )
