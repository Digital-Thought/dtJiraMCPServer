"""Issue tool: issue_get.

Retrieves full details of a single issue by key or ID (FR-004).
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


class IssueGetTool(BaseTool):
    """Retrieve full details of a single Jira issue."""

    name = "issue_get"
    category = "issues"
    description = "Get full details of a Jira issue by its key"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123)",
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of field keys to include in the response",
            },
            "expand": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of expansions to include",
            },
        },
        "required": ["issue_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Retrieve a single issue by key."""
        validate_required(arguments, "issue_key")
        issue_key = validate_issue_key(arguments["issue_key"])

        params: dict[str, Any] = {}

        fields = arguments.get("fields")
        if fields:
            params["fields"] = ",".join(fields)

        expand = arguments.get("expand")
        if expand:
            params["expand"] = ",".join(expand)

        result = await self._platform_client.get(
            f"/issue/{issue_key}",
            params=params or None,
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a single Jira issue by its key. "
                "Returns all fields by default, or a subset if the fields "
                "parameter is specified."
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
                    type="array[string]",
                    required=False,
                    description="Field keys to include (e.g. ['summary', 'status', 'assignee'])",
                ),
                ParameterGuide(
                    name="expand",
                    type="array[string]",
                    required=False,
                    description="Expansions to include",
                    valid_values=["changelog", "renderedFields", "names", "schema", "transitions", "operations", "editmeta"],
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "key": "PROJ-123",
                    "id": "10001",
                    "fields": {"summary": "...", "status": {"name": "Open"}},
                },
            },
            examples=[
                ToolExample(
                    description="Get full issue details",
                    parameters={"issue_key": "PROJ-123"},
                    expected_behaviour="Returns all fields for the issue",
                ),
                ToolExample(
                    description="Get specific fields only",
                    parameters={"issue_key": "PROJ-123", "fields": ["summary", "status", "assignee"]},
                    expected_behaviour="Returns only the specified fields for the issue",
                ),
            ],
            related_tools=["jql_search", "issue_update", "issue_transition"],
            notes=[
                "Issue keys are case-insensitive (proj-123 is normalised to PROJ-123)",
                "Returns NOT_FOUND if the issue does not exist",
            ],
        )
