"""Issue tool: issue_create.

Creates a new issue in Jira (FR-005).
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


class IssueCreateTool(BaseTool):
    """Create a new Jira issue."""

    name = "issue_create"
    category = "issues"
    description = "Create a new issue in a Jira project"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_key": {
                "type": "string",
                "description": "Project key (e.g. PROJ)",
            },
            "issue_type": {
                "type": "string",
                "description": "Issue type name (e.g. Task, Bug, Story)",
            },
            "summary": {
                "type": "string",
                "description": "Issue summary/title",
            },
            "description": {
                "type": "string",
                "description": "Issue description (plain text or ADF JSON)",
            },
            "priority": {
                "type": "string",
                "description": "Priority name (e.g. High, Medium, Low)",
            },
            "assignee": {
                "type": "string",
                "description": "Assignee account ID",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of labels to apply",
            },
            "custom_fields": {
                "type": "object",
                "description": "Custom field values as {field_id: value} pairs",
            },
        },
        "required": ["project_key", "issue_type", "summary"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a new issue."""
        validate_required(arguments, "project_key", "issue_type", "summary")
        project_key = validate_string(arguments["project_key"], "project_key")
        issue_type = validate_string(arguments["issue_type"], "issue_type")
        summary = validate_string(arguments["summary"], "summary", min_length=1, max_length=255)

        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
        }

        # Optional standard fields
        description = arguments.get("description")
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }

        priority = arguments.get("priority")
        if priority:
            fields["priority"] = {"name": priority}

        assignee = arguments.get("assignee")
        if assignee:
            fields["assignee"] = {"accountId": assignee}

        labels = arguments.get("labels")
        if labels:
            fields["labels"] = labels

        # Custom fields
        custom_fields = arguments.get("custom_fields")
        if custom_fields and isinstance(custom_fields, dict):
            fields.update(custom_fields)

        result = await self._platform_client.post(
            "/issue",
            json={"fields": fields},
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new issue in a Jira project. Requires at minimum "
                "a project key, issue type, and summary. Additional fields "
                "like description, priority, assignee, and labels are optional."
            ),
            parameters=[
                ParameterGuide(
                    name="project_key",
                    type="string",
                    required=True,
                    description="Project key (e.g. PROJ)",
                ),
                ParameterGuide(
                    name="issue_type",
                    type="string",
                    required=True,
                    description="Issue type name",
                    valid_values=["Task", "Bug", "Story", "Epic", "Sub-task"],
                ),
                ParameterGuide(
                    name="summary",
                    type="string",
                    required=True,
                    description="Issue summary/title",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Issue description (will be converted to Atlassian Document Format)",
                ),
                ParameterGuide(
                    name="priority",
                    type="string",
                    required=False,
                    description="Priority name",
                    valid_values=["Highest", "High", "Medium", "Low", "Lowest"],
                ),
                ParameterGuide(
                    name="assignee",
                    type="string",
                    required=False,
                    description="Assignee Atlassian account ID",
                ),
                ParameterGuide(
                    name="labels",
                    type="array[string]",
                    required=False,
                    description="Labels to apply to the issue",
                ),
                ParameterGuide(
                    name="custom_fields",
                    type="object",
                    required=False,
                    description="Custom field values as {field_id: value} pairs (e.g. {'customfield_10001': 'value'})",
                ),
            ],
            response_format={
                "success": True,
                "data": {"id": "10001", "key": "PROJ-123", "self": "https://..."},
            },
            examples=[
                ToolExample(
                    description="Create a simple task",
                    parameters={
                        "project_key": "PROJ",
                        "issue_type": "Task",
                        "summary": "Implement login page",
                    },
                    expected_behaviour="Creates a new Task in PROJ and returns its key",
                ),
                ToolExample(
                    description="Create a bug with full details",
                    parameters={
                        "project_key": "PROJ",
                        "issue_type": "Bug",
                        "summary": "Login button unresponsive",
                        "description": "The login button does not respond to clicks on mobile devices",
                        "priority": "High",
                        "labels": ["mobile", "ui"],
                    },
                    expected_behaviour="Creates a high-priority Bug with description and labels",
                ),
            ],
            related_tools=["issue_get", "issue_update", "jql_search"],
            notes=[
                "Issue type names vary by project; use field_list to discover available types",
                "Description is automatically converted to Atlassian Document Format",
                "Custom fields use field IDs like 'customfield_10001'",
            ],
        )
