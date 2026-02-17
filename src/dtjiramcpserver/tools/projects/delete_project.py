"""Project tool: project_delete.

Deletes a Jira project via DELETE /rest/api/3/project/{projectIdOrKey}.
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


class ProjectDeleteTool(BaseTool):
    """Delete a Jira project."""

    name = "project_delete"
    category = "projects"
    description = "Delete a Jira project by its key or ID"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_key": {
                "type": "string",
                "description": "Project key or numeric ID (e.g. PROJ or 10001)",
            },
            "enable_undo": {
                "type": "boolean",
                "description": "Whether to move the project to the recycle bin (default: true)",
            },
        },
        "required": ["project_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Delete a project."""
        validate_required(arguments, "project_key")
        project_key = validate_string(
            arguments["project_key"], "project_key", min_length=1
        )

        enable_undo = arguments.get("enable_undo", True)

        params: dict[str, Any] = {
            "enableUndo": "true" if enable_undo else "false",
        }

        await self._platform_client.delete(
            f"/project/{project_key}",
            params=params,
        )

        return ToolResult.ok(
            data={"project_key": project_key, "deleted": True}
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Delete a Jira project. By default, the project is moved to "
                "the recycle bin and can be restored within a limited time. "
                "Set enable_undo to false to permanently delete the project."
            ),
            parameters=[
                ParameterGuide(
                    name="project_key",
                    type="string",
                    required=True,
                    description="Project key (e.g. PROJ) or numeric project ID (e.g. 10001)",
                ),
                ParameterGuide(
                    name="enable_undo",
                    type="boolean",
                    required=False,
                    description=(
                        "Whether to move the project to the recycle bin "
                        "(true) or permanently delete it (false)"
                    ),
                    default=True,
                ),
            ],
            response_format={
                "success": True,
                "data": {"project_key": "PROJ", "deleted": True},
            },
            examples=[
                ToolExample(
                    description="Delete a project (recoverable)",
                    parameters={"project_key": "PROJ"},
                    expected_behaviour="Moves the project to the recycle bin",
                ),
                ToolExample(
                    description="Permanently delete a project",
                    parameters={"project_key": "PROJ", "enable_undo": False},
                    expected_behaviour="Permanently deletes the project with no recovery option",
                ),
            ],
            related_tools=["project_get", "project_list", "project_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "With enable_undo=true (default), the project can be restored from the recycle bin",
                "With enable_undo=false, the deletion is permanent and cannot be undone",
                "All issues, versions, and components within the project are also deleted",
                "Returns NOT_FOUND if the project does not exist",
                "Returns PERMISSION_ERROR if the user lacks administrator permissions",
            ],
        )
