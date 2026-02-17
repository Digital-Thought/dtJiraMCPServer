"""Project tool: project_get.

Retrieves full details of a single Jira project by key or ID
via GET /rest/api/3/project/{projectIdOrKey}.
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
    validate_required,
    validate_string,
)


class ProjectGetTool(BaseTool):
    """Retrieve full details of a single Jira project."""

    name = "project_get"
    category = "projects"
    description = "Get full details of a Jira project by its key or ID"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_key": {
                "type": "string",
                "description": "Project key or numeric ID (e.g. PROJ or 10001)",
            },
            "expand": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of expansions to include (e.g. description, lead, issueTypes)",
            },
        },
        "required": ["project_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Retrieve a single project by key or ID."""
        validate_required(arguments, "project_key")
        project_key = validate_string(
            arguments["project_key"], "project_key", min_length=1
        )

        params: dict[str, Any] = {}

        expand = arguments.get("expand")
        if expand:
            params["expand"] = ",".join(expand)

        result = await self._platform_client.get(
            f"/project/{project_key}",
            params=params or None,
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a single Jira project by its key or "
                "numeric ID. Returns project metadata including name, type, lead, "
                "and other configured properties."
            ),
            parameters=[
                ParameterGuide(
                    name="project_key",
                    type="string",
                    required=True,
                    description="Project key (e.g. PROJ) or numeric project ID (e.g. 10001)",
                ),
                ParameterGuide(
                    name="expand",
                    type="array[string]",
                    required=False,
                    description="Expansions to include in the response",
                    valid_values=[
                        "description",
                        "lead",
                        "url",
                        "projectKeys",
                        "issueTypes",
                        "issueTypeHierarchy",
                    ],
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "10001",
                    "key": "PROJ",
                    "name": "My Project",
                    "projectTypeKey": "software",
                    "lead": {"accountId": "...", "displayName": "..."},
                },
            },
            examples=[
                ToolExample(
                    description="Get project by key",
                    parameters={"project_key": "PROJ"},
                    expected_behaviour="Returns full details for the PROJ project",
                ),
                ToolExample(
                    description="Get project with expanded issue types",
                    parameters={
                        "project_key": "PROJ",
                        "expand": ["issueTypes", "lead"],
                    },
                    expected_behaviour="Returns project details including issue types and lead information",
                ),
            ],
            related_tools=["project_list", "project_update", "project_delete"],
            notes=[
                "Accepts either the project key (e.g. PROJ) or numeric ID (e.g. 10001)",
                "Returns NOT_FOUND if the project does not exist or is not accessible",
                "Use expand to include additional fields in the response",
            ],
        )
