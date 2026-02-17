"""Group tools: group_list, group_create, group_delete.

Group CRUD operations against the Jira Platform REST API v3.
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


class GroupListTool(BaseTool):
    """List groups in the Jira instance."""

    name = "group_list"
    category = "groups"
    description = "List groups in the Jira instance with pagination"
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
        """List all groups."""
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/group/bulk",
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
                "List all groups in the Jira instance using the bulk groups "
                "endpoint. Returns group names and IDs with pagination metadata."
            ),
            parameters=[
                ParameterGuide(
                    name="start",
                    type="integer",
                    required=False,
                    description="Starting index for pagination",
                    default=0,
                    constraints="Must be >= 0",
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
                        "name": "jira-administrators",
                        "groupId": "abc123",
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 12,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all groups",
                    parameters={},
                    expected_behaviour="Returns all groups with pagination metadata",
                ),
                ToolExample(
                    description="List groups with pagination",
                    parameters={"start": 0, "limit": 10},
                    expected_behaviour="Returns up to 10 groups starting from index 0",
                ),
            ],
            related_tools=[
                "group_create",
                "group_delete",
                "group_get_members",
            ],
            notes=[
                "Returns only groups visible to the authenticated user",
                "Use the returned group name in other group_* tools",
                "Uses the /rest/api/3/group/bulk endpoint",
            ],
        )


class GroupCreateTool(BaseTool):
    """Create a new group in Jira."""

    name = "group_create"
    category = "groups"
    description = "Create a new group in the Jira instance"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the group to create",
            },
        },
        "required": ["name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a new group."""
        validate_required(arguments, "name")
        name = validate_string(arguments["name"], "name")

        result = await self._platform_client.post(
            "/group",
            json={"name": name},
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new group in the Jira instance. The group name must "
                "be unique across the instance."
            ),
            parameters=[
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Name for the new group",
                    constraints="Must be a non-empty, unique group name",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "name": "new-group",
                    "groupId": "abc123",
                    "self": "https://instance.atlassian.net/rest/api/3/group?groupname=new-group",
                },
            },
            examples=[
                ToolExample(
                    description="Create a new group",
                    parameters={"name": "project-reviewers"},
                    expected_behaviour="Creates the group and returns its details including group ID",
                ),
            ],
            related_tools=[
                "group_list",
                "group_delete",
                "group_add_user",
            ],
            notes=[
                "Requires Jira Administrator permissions",
                "Returns CONFLICT if a group with the same name already exists",
                "Group names are case-insensitive in Jira Cloud",
            ],
        )


class GroupDeleteTool(BaseTool):
    """Delete a group from Jira."""

    name = "group_delete"
    category = "groups"
    description = "Delete a group from the Jira instance"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "Name of the group to delete",
            },
        },
        "required": ["group_name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Delete a group."""
        validate_required(arguments, "group_name")
        group_name = validate_string(arguments["group_name"], "group_name")

        await self._platform_client.delete(
            "/group",
            params={"groupname": group_name},
        )

        return ToolResult.ok(
            data={"group_name": group_name, "deleted": True}
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Permanently delete a group from the Jira instance. This action "
                "cannot be undone. Members will lose any permissions granted via "
                "this group."
            ),
            parameters=[
                ParameterGuide(
                    name="group_name",
                    type="string",
                    required=True,
                    description="Name of the group to delete",
                ),
            ],
            response_format={
                "success": True,
                "data": {"group_name": "old-group", "deleted": True},
            },
            examples=[
                ToolExample(
                    description="Delete a group",
                    parameters={"group_name": "obsolete-team"},
                    expected_behaviour="Permanently deletes the group",
                ),
            ],
            related_tools=[
                "group_list",
                "group_create",
                "group_remove_user",
            ],
            notes=[
                "This action is permanent and cannot be undone",
                "Requires Jira Administrator permissions",
                "Returns NOT_FOUND if the group does not exist",
                "Members are not deleted; they simply lose permissions granted through this group",
            ],
        )
