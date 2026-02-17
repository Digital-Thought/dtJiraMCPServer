"""Project tool: project_create.

Creates a new Jira project via POST /rest/api/3/project.
"""

from __future__ import annotations

import re
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

# Project key pattern: 2-10 uppercase ASCII letters, optionally followed by digits
_PROJECT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")


class ProjectCreateTool(BaseTool):
    """Create a new Jira project."""

    name = "project_create"
    category = "projects"
    description = "Create a new Jira project"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Project key (2-10 uppercase characters, e.g. PROJ)",
            },
            "name": {
                "type": "string",
                "description": "Display name for the project",
            },
            "project_type_key": {
                "type": "string",
                "description": "Project type: 'software', 'service_desk', or 'business'",
            },
            "lead_account_id": {
                "type": "string",
                "description": "Atlassian account ID of the project lead",
            },
            "description": {
                "type": "string",
                "description": "Project description",
            },
            "assignee_type": {
                "type": "string",
                "description": "Default assignee type: 'PROJECT_LEAD' or 'UNASSIGNED'",
            },
            "project_template_key": {
                "type": "string",
                "description": "Project template key (e.g. 'com.pyxis.greenhopper.jira:gh-simplified-scrum-classic')",
            },
        },
        "required": ["key", "name", "project_type_key", "lead_account_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a new project."""
        validate_required(
            arguments, "key", "name", "project_type_key", "lead_account_id"
        )

        key = validate_string(arguments["key"], "key", min_length=2, max_length=10)
        key = key.upper()

        if not _PROJECT_KEY_PATTERN.match(key):
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message=(
                    f"Parameter 'key' must be 2-10 uppercase alphanumeric characters "
                    f"starting with a letter (got '{key}')"
                ),
                field="key",
                reason="invalid_format",
            )

        name = validate_string(arguments["name"], "name", min_length=1, max_length=255)
        project_type_key = validate_enum(
            arguments["project_type_key"],
            "project_type_key",
            ["software", "service_desk", "business"],
        )
        lead_account_id = validate_string(
            arguments["lead_account_id"], "lead_account_id", min_length=1
        )

        body: dict[str, Any] = {
            "key": key,
            "name": name,
            "projectTypeKey": project_type_key,
            "leadAccountId": lead_account_id,
        }

        # Optional fields
        description = arguments.get("description")
        if description:
            body["description"] = description

        assignee_type = arguments.get("assignee_type")
        if assignee_type:
            assignee_type = validate_enum(
                assignee_type,
                "assignee_type",
                ["PROJECT_LEAD", "UNASSIGNED"],
            )
            body["assigneeType"] = assignee_type

        project_template_key = arguments.get("project_template_key")
        if project_template_key:
            body["projectTemplateKey"] = project_template_key

        result = await self._platform_client.post("/project", json=body)

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new Jira project. Requires a unique project key, display "
                "name, project type, and a lead account ID. Optionally specify a "
                "description, assignee type, and project template."
            ),
            parameters=[
                ParameterGuide(
                    name="key",
                    type="string",
                    required=True,
                    description="Unique project key (uppercase alphanumeric)",
                    constraints="2-10 uppercase characters starting with a letter",
                ),
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Display name for the project",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="project_type_key",
                    type="string",
                    required=True,
                    description="Type of project to create",
                    valid_values=["software", "service_desk", "business"],
                ),
                ParameterGuide(
                    name="lead_account_id",
                    type="string",
                    required=True,
                    description="Atlassian account ID of the project lead",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description of the project",
                ),
                ParameterGuide(
                    name="assignee_type",
                    type="string",
                    required=False,
                    description="Default assignee type for new issues",
                    valid_values=["PROJECT_LEAD", "UNASSIGNED"],
                ),
                ParameterGuide(
                    name="project_template_key",
                    type="string",
                    required=False,
                    description=(
                        "Template key to initialise the project with a predefined "
                        "configuration (e.g. Scrum, Kanban)"
                    ),
                    valid_values=[
                        "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
                        "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic",
                        "com.pyxis.greenhopper.jira:gh-simplified-basic",
                        "com.atlassian.servicedesk:simplified-it-service-management",
                    ],
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": 10001,
                    "key": "PROJ",
                    "self": "https://your-domain.atlassian.net/rest/api/3/project/10001",
                },
            },
            examples=[
                ToolExample(
                    description="Create a software project",
                    parameters={
                        "key": "MYPROJ",
                        "name": "My Software Project",
                        "project_type_key": "software",
                        "lead_account_id": "5b10ac8d82e05b22cc7d4ef5",
                    },
                    expected_behaviour="Creates a new software project and returns its ID and key",
                ),
                ToolExample(
                    description="Create a service desk project with template",
                    parameters={
                        "key": "SUPPORT",
                        "name": "Customer Support",
                        "project_type_key": "service_desk",
                        "lead_account_id": "5b10ac8d82e05b22cc7d4ef5",
                        "description": "Customer support service desk",
                        "project_template_key": "com.atlassian.servicedesk:simplified-it-service-management",
                    },
                    expected_behaviour="Creates a service desk project with the ITSM template",
                ),
            ],
            related_tools=["project_list", "project_get", "project_update", "project_delete"],
            notes=[
                "Requires Jira Administrator permissions",
                "Project keys must be unique across the Jira instance",
                "Returns CONFLICT if a project with the same key already exists",
                "The lead_account_id can be obtained from Jira user search or the myself endpoint",
                "Project templates define the initial workflow, screens, and issue types",
            ],
        )
