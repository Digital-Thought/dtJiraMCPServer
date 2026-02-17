"""Workflow tools: transition_list, transition_get.

Transition queries via the Jira Platform REST API v3 (FR-021).
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


class TransitionListTool(BaseTool):
    """List transitions for a workflow."""

    name = "transition_list"
    category = "workflows"
    description = "List all transitions for a workflow"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "workflow_name": {
                "type": "string",
                "description": "Workflow name to list transitions for",
            },
        },
        "required": ["workflow_name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List transitions for a workflow by fetching with expanded transitions."""
        validate_required(arguments, "workflow_name")
        workflow_name = validate_string(
            arguments["workflow_name"], "workflow_name", min_length=1
        )

        response = await self._platform_client.get(
            "/workflow/search",
            params={
                "workflowName": workflow_name,
                "expand": "transitions",
            },
        )

        values = response.get("values", [])
        if not values:
            from dtjiramcpserver.exceptions import NotFoundError

            raise NotFoundError(
                message=f"Workflow '{workflow_name}' not found",
            )

        workflow = values[0]
        transitions = workflow.get("transitions", [])

        return ToolResult.ok(data=transitions)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all transitions defined in a specific workflow. "
                "Returns the transition names, types, source and target "
                "statuses for each transition."
            ),
            parameters=[
                ParameterGuide(
                    name="workflow_name",
                    type="string",
                    required=True,
                    description="Workflow name (from workflow_list)",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "1",
                        "name": "Create",
                        "type": "initial",
                        "to": {"id": "1"},
                    },
                    {
                        "id": "2",
                        "name": "Start Progress",
                        "type": "directed",
                        "from": [{"id": "1"}],
                        "to": {"id": "3"},
                    },
                ],
            },
            examples=[
                ToolExample(
                    description="List transitions for a workflow",
                    parameters={"workflow_name": "jira"},
                    expected_behaviour="Returns all transitions in the workflow",
                ),
            ],
            related_tools=["transition_get", "workflow_get", "workflow_list"],
            notes=[
                "Transition types: initial (creates issue), directed (between specific statuses), global (from any status)",
                "Returns NOT_FOUND if the workflow does not exist",
            ],
        )


class TransitionGetTool(BaseTool):
    """Get details of a specific transition in a workflow."""

    name = "transition_get"
    category = "workflows"
    description = "Get detailed information about a specific workflow transition"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "workflow_name": {
                "type": "string",
                "description": "Workflow name containing the transition",
            },
            "transition_id": {
                "type": "string",
                "description": "Transition ID within the workflow",
            },
        },
        "required": ["workflow_name", "transition_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a specific transition from a workflow."""
        validate_required(arguments, "workflow_name", "transition_id")
        workflow_name = validate_string(
            arguments["workflow_name"], "workflow_name", min_length=1
        )
        transition_id = validate_string(
            arguments["transition_id"], "transition_id", min_length=1
        )

        response = await self._platform_client.get(
            "/workflow/search",
            params={
                "workflowName": workflow_name,
                "expand": "transitions,transitions.rules",
            },
        )

        values = response.get("values", [])
        if not values:
            from dtjiramcpserver.exceptions import NotFoundError

            raise NotFoundError(
                message=f"Workflow '{workflow_name}' not found",
            )

        workflow = values[0]
        transitions = workflow.get("transitions", [])

        for transition in transitions:
            if str(transition.get("id")) == str(transition_id):
                return ToolResult.ok(data=transition)

        from dtjiramcpserver.exceptions import NotFoundError

        raise NotFoundError(
            message=(
                f"Transition '{transition_id}' not found in "
                f"workflow '{workflow_name}'"
            ),
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve detailed information about a specific transition "
                "in a workflow, including its rules (conditions, validators, "
                "and post functions)."
            ),
            parameters=[
                ParameterGuide(
                    name="workflow_name",
                    type="string",
                    required=True,
                    description="Workflow name containing the transition",
                ),
                ParameterGuide(
                    name="transition_id",
                    type="string",
                    required=True,
                    description="Transition ID (from transition_list)",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "2",
                    "name": "Start Progress",
                    "type": "directed",
                    "from": [{"id": "1"}],
                    "to": {"id": "3"},
                    "rules": {
                        "conditions": [],
                        "validators": [],
                        "postFunctions": [],
                    },
                },
            },
            examples=[
                ToolExample(
                    description="Get a specific transition",
                    parameters={
                        "workflow_name": "jira",
                        "transition_id": "2",
                    },
                    expected_behaviour=(
                        "Returns the transition details including rules"
                    ),
                ),
            ],
            related_tools=["transition_list", "workflow_get"],
            notes=[
                "Returns NOT_FOUND if the workflow or transition does not exist",
                "Rules include conditions, validators, and post functions",
                "Use transition_list to discover available transition IDs",
            ],
        )
