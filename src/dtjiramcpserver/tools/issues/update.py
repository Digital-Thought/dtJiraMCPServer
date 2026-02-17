"""Issue tool: issue_update.

Modifies fields on an existing Jira issue (FR-006).
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


class IssueUpdateTool(BaseTool):
    """Update fields on an existing Jira issue."""

    name = "issue_update"
    category = "issues"
    description = "Update fields on an existing Jira issue"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123)",
            },
            "fields": {
                "type": "object",
                "description": "Fields to update as {field_name: value} pairs",
            },
        },
        "required": ["issue_key", "fields"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Update fields on an existing issue."""
        validate_required(arguments, "issue_key", "fields")
        issue_key = validate_issue_key(arguments["issue_key"])

        fields = arguments["fields"]
        if not isinstance(fields, dict) or not fields:
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message="Parameter 'fields' must be a non-empty object",
                field="fields",
                reason="invalid_type",
            )

        await self._platform_client.put(
            f"/issue/{issue_key}",
            json={"fields": fields},
        )

        return ToolResult.ok(data={"issue_key": issue_key, "updated": True})

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Update fields on an existing Jira issue. Accepts the issue key "
                "and a dictionary of field values to set. Both standard and custom "
                "fields are supported."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key in PROJECT-NUMBER format (e.g. PROJ-123)",
                ),
                ParameterGuide(
                    name="fields",
                    type="object",
                    required=True,
                    description="Fields to update as {field_name: value} pairs",
                ),
            ],
            response_format={
                "success": True,
                "data": {"issue_key": "PROJ-123", "updated": True},
            },
            examples=[
                ToolExample(
                    description="Update summary and priority",
                    parameters={
                        "issue_key": "PROJ-123",
                        "fields": {
                            "summary": "Updated summary",
                            "priority": {"name": "High"},
                        },
                    },
                    expected_behaviour="Updates the summary and priority fields",
                ),
                ToolExample(
                    description="Add labels to an issue",
                    parameters={
                        "issue_key": "PROJ-123",
                        "fields": {"labels": ["urgent", "frontend"]},
                    },
                    expected_behaviour="Replaces the issue's labels with the specified values",
                ),
            ],
            related_tools=["issue_get", "issue_create", "issue_transition"],
            notes=[
                "The PUT replaces field values; to append, read first then include all values",
                "Use issue_get to check current field values before updating",
                "Custom fields use IDs like 'customfield_10001'",
                "Returns NOT_FOUND if the issue does not exist",
            ],
        )
