"""Project tool: project_list.

Lists Jira projects with optional filtering via the Jira Platform
REST API v3 endpoint GET /rest/api/3/project/search.
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
    validate_string,
)


class ProjectListTool(BaseTool):
    """List Jira projects with optional filtering."""

    name = "project_list"
    category = "projects"
    description = "List Jira projects with optional filtering and pagination"
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
            "query": {
                "type": "string",
                "description": "Filter projects by name or key (partial match)",
            },
            "type_key": {
                "type": "string",
                "description": "Filter by project type: 'software', 'service_desk', or 'business'",
            },
            "expand": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of expansions to include (e.g. description, lead, url)",
            },
        },
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List projects with optional filters."""
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] = {}

        query = arguments.get("query")
        if query:
            extra_params["query"] = validate_string(query, "query", min_length=1)

        type_key = arguments.get("type_key")
        if type_key:
            type_key = validate_enum(
                type_key,
                "type_key",
                ["software", "service_desk", "business"],
            )
            extra_params["typeKey"] = type_key

        expand = arguments.get("expand")
        if expand:
            extra_params["expand"] = ",".join(expand)

        paginated = await self._platform_client.list_paginated(
            "/project/search",
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
                "List all Jira projects accessible to the authenticated user. "
                "Supports filtering by name or key, project type, and optional "
                "field expansions. Results are paginated."
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
                ParameterGuide(
                    name="query",
                    type="string",
                    required=False,
                    description="Filter projects by name or key (partial match)",
                ),
                ParameterGuide(
                    name="type_key",
                    type="string",
                    required=False,
                    description="Filter by project type",
                    valid_values=["software", "service_desk", "business"],
                ),
                ParameterGuide(
                    name="expand",
                    type="array[string]",
                    required=False,
                    description="Expansions to include in the response",
                    valid_values=["description", "lead", "url", "projectKeys", "issueTypes"],
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "10001",
                        "key": "PROJ",
                        "name": "My Project",
                        "projectTypeKey": "software",
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
                    description="List all projects",
                    parameters={},
                    expected_behaviour="Returns all accessible projects with pagination",
                ),
                ToolExample(
                    description="Search projects by name",
                    parameters={"query": "support"},
                    expected_behaviour="Returns projects matching 'support' in name or key",
                ),
                ToolExample(
                    description="List only software projects",
                    parameters={"type_key": "software"},
                    expected_behaviour="Returns only projects with type 'software'",
                ),
                ToolExample(
                    description="List projects with expanded details",
                    parameters={"expand": ["description", "lead"]},
                    expected_behaviour="Returns projects with description and lead information",
                ),
            ],
            related_tools=["project_get", "project_create"],
            notes=[
                "Only returns projects the authenticated user has permission to view",
                "The query parameter performs a partial match on project name and key",
                "Use expand to include additional fields in the response",
            ],
        )
