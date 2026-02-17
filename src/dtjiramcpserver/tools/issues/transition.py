"""Issue tools: issue_get_transitions and issue_transition.

Retrieves available transitions and moves issues through
workflow states (FR-007).
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
    validate_string,
)


class IssueGetTransitionsTool(BaseTool):
    """Get available transitions for a Jira issue."""

    name = "issue_get_transitions"
    category = "issues"
    description = "Get available workflow transitions for an issue"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123)",
            },
        },
        "required": ["issue_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Retrieve available transitions for an issue."""
        validate_required(arguments, "issue_key")
        issue_key = validate_issue_key(arguments["issue_key"])

        result = await self._platform_client.get(
            f"/issue/{issue_key}/transitions",
        )

        transitions = result.get("transitions", [])
        return ToolResult.ok(data=transitions)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Get the available workflow transitions for an issue based on "
                "its current status. Use the returned transition IDs with "
                "issue_transition to move the issue to a new state."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key in PROJECT-NUMBER format (e.g. PROJ-123)",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "21",
                        "name": "In Progress",
                        "to": {"name": "In Progress", "id": "3"},
                    }
                ],
            },
            examples=[
                ToolExample(
                    description="Get transitions for an issue",
                    parameters={"issue_key": "PROJ-123"},
                    expected_behaviour="Returns list of available transitions with IDs and target statuses",
                ),
            ],
            related_tools=["issue_transition", "issue_get"],
            notes=[
                "Available transitions depend on the issue's current workflow state",
                "Use the 'id' field from the result with issue_transition",
            ],
        )


class IssueTransitionTool(BaseTool):
    """Transition a Jira issue to a new workflow state."""

    name = "issue_transition"
    category = "issues"
    description = "Move an issue to a new workflow state via transition"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123)",
            },
            "transition_id": {
                "type": "string",
                "description": "Transition ID (from issue_get_transitions)",
            },
            "comment": {
                "type": "string",
                "description": "Optional comment to add during transition",
            },
            "fields": {
                "type": "object",
                "description": "Optional fields required by the transition",
            },
        },
        "required": ["issue_key", "transition_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Transition an issue to a new workflow state."""
        validate_required(arguments, "issue_key", "transition_id")
        issue_key = validate_issue_key(arguments["issue_key"])
        transition_id = validate_string(arguments["transition_id"], "transition_id")

        body: dict[str, Any] = {
            "transition": {"id": transition_id},
        }

        # Optional comment via the update block
        comment = arguments.get("comment")
        if comment:
            body["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": comment}],
                                    }
                                ],
                            }
                        }
                    }
                ]
            }

        # Optional fields required by the transition
        fields = arguments.get("fields")
        if fields and isinstance(fields, dict):
            body["fields"] = fields

        await self._platform_client.post(
            f"/issue/{issue_key}/transitions",
            json=body,
        )

        return ToolResult.ok(
            data={
                "issue_key": issue_key,
                "transition_id": transition_id,
                "transitioned": True,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Move a Jira issue to a new workflow state by executing a "
                "transition. Use issue_get_transitions first to discover "
                "available transitions and their IDs."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key in PROJECT-NUMBER format (e.g. PROJ-123)",
                ),
                ParameterGuide(
                    name="transition_id",
                    type="string",
                    required=True,
                    description="Transition ID obtained from issue_get_transitions",
                ),
                ParameterGuide(
                    name="comment",
                    type="string",
                    required=False,
                    description="Comment to add during the transition",
                ),
                ParameterGuide(
                    name="fields",
                    type="object",
                    required=False,
                    description="Fields required by the transition (e.g. resolution)",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "issue_key": "PROJ-123",
                    "transition_id": "21",
                    "transitioned": True,
                },
            },
            examples=[
                ToolExample(
                    description="Move an issue to In Progress",
                    parameters={"issue_key": "PROJ-123", "transition_id": "21"},
                    expected_behaviour="Transitions the issue to the In Progress state",
                ),
                ToolExample(
                    description="Close an issue with a comment",
                    parameters={
                        "issue_key": "PROJ-123",
                        "transition_id": "31",
                        "comment": "Closing as completed",
                        "fields": {"resolution": {"name": "Done"}},
                    },
                    expected_behaviour="Transitions the issue to Done with a comment and resolution",
                ),
            ],
            prerequisites=["Use issue_get_transitions to get available transition IDs"],
            related_tools=["issue_get_transitions", "issue_get", "issue_update"],
            notes=[
                "Transition IDs are NOT the same as status IDs",
                "Some transitions require fields (e.g. resolution); these will return a VALIDATION_ERROR if missing",
            ],
        )
