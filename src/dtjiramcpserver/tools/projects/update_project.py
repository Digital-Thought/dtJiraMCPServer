"""Project tool: project_update.

Updates an existing Jira project via PUT /rest/api/3/project/{projectIdOrKey}.
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
    validate_required,
    validate_string,
)


class ProjectUpdateTool(BaseTool):
    """Update an existing Jira project."""

    name = "project_update"
    category = "projects"
    description = "Update fields on an existing Jira project"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_key": {
                "type": "string",
                "description": "Project key or numeric ID (e.g. PROJ or 10001)",
            },
            "name": {
                "type": "string",
                "description": "New display name for the project",
            },
            "description": {
                "type": "string",
                "description": "New project description",
            },
            "lead_account_id": {
                "type": "string",
                "description": "New project lead Atlassian account ID",
            },
            "assignee_type": {
                "type": "string",
                "description": "New default assignee type: 'PROJECT_LEAD' or 'UNASSIGNED'",
            },
            "url": {
                "type": "string",
                "description": "New project URL",
            },
        },
        "required": ["project_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Update an existing project."""
        validate_required(arguments, "project_key")
        project_key = validate_string(
            arguments["project_key"], "project_key", min_length=1
        )

        body: dict[str, Any] = {}

        if "name" in arguments and arguments["name"] is not None:
            body["name"] = validate_string(
                arguments["name"], "name", min_length=1, max_length=255
            )

        if "description" in arguments and arguments["description"] is not None:
            body["description"] = arguments["description"]

        if "lead_account_id" in arguments and arguments["lead_account_id"] is not None:
            body["leadAccountId"] = validate_string(
                arguments["lead_account_id"], "lead_account_id", min_length=1
            )

        if "assignee_type" in arguments and arguments["assignee_type"] is not None:
            assignee_type = validate_enum(
                arguments["assignee_type"],
                "assignee_type",
                ["PROJECT_LEAD", "UNASSIGNED"],
            )
            body["assigneeType"] = assignee_type

        if "url" in arguments and arguments["url"] is not None:
            body["url"] = arguments["url"]

        if not body:
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message=(
                    "At least one field to update must be provided "
                    "(name, description, lead_account_id, assignee_type, or url)"
                ),
                field="fields",
                reason="empty",
            )

        result = await self._platform_client.put(
            f"/project/{project_key}",
            json=body,
        )

        return ToolResult.ok(
            data={"project_key": project_key, "updated": True}
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Update fields on an existing Jira project. At least one field "
                "must be provided to update. Supports changing the project name, "
                "description, lead, assignee type, and URL."
            ),
            parameters=[
                ParameterGuide(
                    name="project_key",
                    type="string",
                    required=True,
                    description="Project key (e.g. PROJ) or numeric project ID (e.g. 10001)",
                ),
                ParameterGuide(
                    name="name",
                    type="string",
                    required=False,
                    description="New display name for the project",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="New project description",
                ),
                ParameterGuide(
                    name="lead_account_id",
                    type="string",
                    required=False,
                    description="New project lead Atlassian account ID",
                ),
                ParameterGuide(
                    name="assignee_type",
                    type="string",
                    required=False,
                    description="New default assignee type for new issues",
                    valid_values=["PROJECT_LEAD", "UNASSIGNED"],
                ),
                ParameterGuide(
                    name="url",
                    type="string",
                    required=False,
                    description="New project URL",
                ),
            ],
            response_format={
                "success": True,
                "data": {"project_key": "PROJ", "updated": True},
            },
            examples=[
                ToolExample(
                    description="Rename a project",
                    parameters={
                        "project_key": "PROJ",
                        "name": "My Renamed Project",
                    },
                    expected_behaviour="Updates the project's display name",
                ),
                ToolExample(
                    description="Change project lead and description",
                    parameters={
                        "project_key": "PROJ",
                        "lead_account_id": "5b10ac8d82e05b22cc7d4ef5",
                        "description": "Updated project description",
                    },
                    expected_behaviour="Updates the project lead and description",
                ),
                ToolExample(
                    description="Set default assignee to unassigned",
                    parameters={
                        "project_key": "PROJ",
                        "assignee_type": "UNASSIGNED",
                    },
                    expected_behaviour="Changes the default assignee type so new issues are unassigned",
                ),
            ],
            related_tools=["project_get", "project_list", "project_create", "project_delete"],
            notes=[
                "Requires Jira Administrator permissions or Project Administrator for the target project",
                "At least one field must be provided; an empty update is rejected",
                "Returns NOT_FOUND if the project does not exist",
                "The project key itself cannot be changed via this endpoint",
                "Use project_get to check current values before updating",
            ],
        )
