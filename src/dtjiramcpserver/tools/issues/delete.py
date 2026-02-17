"""Issue tool: issue_delete.

Deletes an issue from Jira (FR-008).
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
    validate_issue_key,
    validate_required,
)


class IssueDeleteTool(BaseTool):
    """Delete a Jira issue."""

    name = "issue_delete"
    category = "issues"
    description = "Delete a Jira issue by its key"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123)",
            },
            "delete_subtasks": {
                "type": "boolean",
                "description": "Whether to also delete subtasks (default: false)",
            },
        },
        "required": ["issue_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Delete an issue."""
        validate_required(arguments, "issue_key")
        issue_key = validate_issue_key(arguments["issue_key"])

        params: dict[str, Any] | None = None
        delete_subtasks = arguments.get("delete_subtasks", False)
        if delete_subtasks:
            params = {"deleteSubtasks": "true"}

        await self._platform_client.delete(
            f"/issue/{issue_key}",
            params=params,
        )

        return ToolResult.ok(
            data={"issue_key": issue_key, "deleted": True}
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Permanently delete a Jira issue. This action cannot be undone. "
                "Optionally deletes subtasks as well."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key in PROJECT-NUMBER format (e.g. PROJ-123)",
                ),
                ParameterGuide(
                    name="delete_subtasks",
                    type="boolean",
                    required=False,
                    description="Whether to also delete subtasks",
                    default=False,
                ),
            ],
            response_format={
                "success": True,
                "data": {"issue_key": "PROJ-123", "deleted": True},
            },
            examples=[
                ToolExample(
                    description="Delete an issue",
                    parameters={"issue_key": "PROJ-123"},
                    expected_behaviour="Permanently deletes the issue",
                ),
                ToolExample(
                    description="Delete an issue and its subtasks",
                    parameters={"issue_key": "PROJ-123", "delete_subtasks": True},
                    expected_behaviour="Deletes the issue and all its subtasks",
                ),
            ],
            related_tools=["issue_get", "issue_create"],
            notes=[
                "This action is permanent and cannot be undone",
                "Returns NOT_FOUND if the issue does not exist",
                "Returns PERMISSION_ERROR if the user lacks delete permission",
                "If the issue has subtasks and delete_subtasks is false, the API may return an error",
            ],
        )
