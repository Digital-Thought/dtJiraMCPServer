"""Workflow tools: workflow_list, workflow_get, workflow_create.

Workflow management via the Jira Platform REST API v3 (FR-019).
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
    validate_pagination,
    validate_required,
    validate_string,
)


class WorkflowListTool(BaseTool):
    """List all workflows."""

    name = "workflow_list"
    category = "workflows"
    description = "List all Jira workflows with pagination"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "start": {
                "type": "integer",
                "description": "Starting index for pagination (default: 0)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
        },
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List all workflows."""
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/workflow/search",
            start=start,
            limit=limit,
        )

        pagination = {
            "start": paginated.start,
            "limit": paginated.limit,
            "total": paginated.total,
            "has_more": paginated.has_more,
        }

        return ToolResult.ok(data=paginated.results, pagination=pagination)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all workflows in the Jira instance. Workflows define "
                "the states and transitions that issues move through."
            ),
            parameters=[
                ParameterGuide(
                    name="start",
                    type="integer",
                    required=False,
                    description="Starting index for pagination",
                    default=0,
                ),
                ParameterGuide(
                    name="limit",
                    type="integer",
                    required=False,
                    description="Maximum number of results to return",
                    default=50,
                    constraints="Must be between 1 and 100",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": {"name": "jira"},
                        "description": "The default Jira workflow",
                        "isDefault": True,
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 5,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all workflows",
                    parameters={},
                    expected_behaviour="Returns all workflows with pagination",
                ),
            ],
            related_tools=["workflow_get", "workflow_create", "status_list"],
            notes=[
                "Requires Jira Administrator permissions",
                "Use workflow_get to see statuses and transitions for a workflow",
            ],
        )


class WorkflowGetTool(BaseTool):
    """Get details of a workflow by name."""

    name = "workflow_get"
    category = "workflows"
    description = "Get a workflow's details including statuses and transitions"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "workflow_name": {
                "type": "string",
                "description": "Workflow name (e.g. 'jira' for the default workflow)",
            },
        },
        "required": ["workflow_name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get a workflow by name with expanded statuses and transitions."""
        validate_required(arguments, "workflow_name")
        workflow_name = validate_string(
            arguments["workflow_name"], "workflow_name", min_length=1
        )

        response = await self._platform_client.get(
            "/workflow/search",
            params={
                "workflowName": workflow_name,
                "expand": "transitions,statuses",
            },
        )

        values = response.get("values", [])
        if not values:
            from dtjiramcpserver.exceptions import NotFoundError

            raise NotFoundError(
                message=f"Workflow '{workflow_name}' not found",
            )

        return ToolResult.ok(data=values[0])

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve full details of a specific workflow by name, "
                "including its statuses and transitions. Workflows are "
                "identified by name, not by numeric ID."
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
                "data": {
                    "id": {"name": "jira"},
                    "description": "The default Jira workflow",
                    "transitions": [
                        {
                            "id": "1",
                            "name": "Create",
                            "type": "initial",
                            "to": {"id": "1"},
                        }
                    ],
                    "statuses": [
                        {"id": "1", "name": "Open"},
                        {"id": "3", "name": "In Progress"},
                    ],
                },
            },
            examples=[
                ToolExample(
                    description="Get the default workflow",
                    parameters={"workflow_name": "jira"},
                    expected_behaviour=(
                        "Returns the workflow with statuses and transitions"
                    ),
                ),
            ],
            related_tools=["workflow_list", "transition_list", "status_list"],
            notes=[
                "Workflows are identified by name, not numeric ID",
                "Returns NOT_FOUND if the workflow does not exist",
                "Response includes expanded statuses and transitions",
            ],
        )


class WorkflowCreateTool(BaseTool):
    """Create a new workflow."""

    name = "workflow_create"
    category = "workflows"
    description = "Create a new Jira workflow"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the new workflow",
            },
            "description": {
                "type": "string",
                "description": "Description of the workflow",
            },
            "statuses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "properties": {"type": "object"},
                    },
                },
                "description": "Status references for the workflow",
            },
            "transitions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "to": {"type": "string"},
                        "from": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "description": "Transition definitions for the workflow",
            },
            "scope_type": {
                "type": "string",
                "description": "Scope type: 'PROJECT' (default: 'PROJECT')",
            },
            "scope_project_id": {
                "type": "string",
                "description": "Project ID for the workflow scope",
            },
        },
        "required": ["name", "statuses", "transitions"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a workflow."""
        validate_required(arguments, "name", "statuses", "transitions")
        name = validate_string(
            arguments["name"], "name", min_length=1, max_length=255
        )

        statuses = arguments["statuses"]
        transitions = arguments["transitions"]

        workflow: dict[str, Any] = {
            "name": name,
            "statuses": [
                {
                    "statusReference": s.get("id", s) if isinstance(s, dict) else s,
                    **({"properties": s["properties"]} if isinstance(s, dict) and "properties" in s else {}),
                }
                for s in statuses
            ],
            "transitions": transitions,
        }

        description = arguments.get("description")
        if description:
            workflow["description"] = description

        # Build scope
        scope: dict[str, Any] = {
            "type": arguments.get("scope_type", "PROJECT"),
        }
        scope_project_id = arguments.get("scope_project_id")
        if scope_project_id:
            scope["project"] = {"id": scope_project_id}

        body: dict[str, Any] = {
            "scope": scope,
            "workflows": [workflow],
            "statuses": [
                {"id": s.get("id", s) if isinstance(s, dict) else s}
                for s in statuses
            ],
        }

        result = await self._platform_client.post(
            "/workflows/create",
            json=body,
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new workflow in Jira. Requires defining the "
                "statuses the workflow uses and the transitions between them. "
                "The workflow must be scoped to a project."
            ),
            parameters=[
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Name for the new workflow",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description of the workflow",
                ),
                ParameterGuide(
                    name="statuses",
                    type="array[object]",
                    required=True,
                    description=(
                        "Status references: each has 'id' (status ID) and "
                        "optional 'properties'"
                    ),
                ),
                ParameterGuide(
                    name="transitions",
                    type="array[object]",
                    required=True,
                    description=(
                        "Transitions: each has 'name', 'type' (initial/directed/global), "
                        "'to' (target status reference), and optional 'from' (source status references)"
                    ),
                ),
                ParameterGuide(
                    name="scope_type",
                    type="string",
                    required=False,
                    description="Scope type for the workflow",
                    default="PROJECT",
                ),
                ParameterGuide(
                    name="scope_project_id",
                    type="string",
                    required=False,
                    description="Project ID for the workflow scope",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "workflows": [
                        {"id": "workflow-uuid", "name": "My Workflow"}
                    ],
                },
            },
            examples=[
                ToolExample(
                    description="Create a simple workflow",
                    parameters={
                        "name": "Simple Bug Workflow",
                        "statuses": [
                            {"id": "1"},
                            {"id": "3"},
                            {"id": "10001"},
                        ],
                        "transitions": [
                            {
                                "name": "Create",
                                "type": "initial",
                                "to": "1",
                            },
                            {
                                "name": "Start Progress",
                                "type": "directed",
                                "from": ["1"],
                                "to": "3",
                            },
                        ],
                        "scope_project_id": "10001",
                    },
                    expected_behaviour="Creates a new workflow with the defined statuses and transitions",
                ),
            ],
            related_tools=["workflow_list", "status_list", "status_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "Referenced statuses must already exist",
                "Workflow must have at least one initial transition",
                "Use status_list to discover available status IDs",
            ],
        )
