"""Group membership tools: group_get_members, group_add_user, group_remove_user.

Manage group membership against the Jira Platform REST API v3.
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


class GroupGetMembersTool(BaseTool):
    """List members of a group."""

    name = "group_get_members"
    category = "groups"
    description = "List members of a group with pagination"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "Name of the group",
            },
            "start": {
                "type": "integer",
                "description": "Starting index for pagination (default: 0)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
        },
        "required": ["group_name"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List members of a group."""
        validate_required(arguments, "group_name")
        group_name = validate_string(arguments["group_name"], "group_name")
        start, limit = validate_pagination(arguments)

        paginated = await self._platform_client.list_paginated(
            "/group/member",
            start=start,
            limit=limit,
            extra_params={"groupname": group_name},
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
                "List all members of a specified group. Returns user account "
                "details including account IDs and display names with pagination."
            ),
            parameters=[
                ParameterGuide(
                    name="group_name",
                    type="string",
                    required=True,
                    description="Name of the group to list members for",
                ),
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
                        "accountId": "5b10ac8d82e05b22cc7d4ef5",
                        "displayName": "Jane Smith",
                        "emailAddress": "jane@example.com",
                        "active": True,
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
                    description="List all members of a group",
                    parameters={"group_name": "jira-administrators"},
                    expected_behaviour="Returns all members of the group with pagination",
                ),
                ToolExample(
                    description="List members with pagination",
                    parameters={"group_name": "developers", "start": 0, "limit": 10},
                    expected_behaviour="Returns up to 10 members starting from index 0",
                ),
            ],
            related_tools=[
                "group_list",
                "group_add_user",
                "group_remove_user",
            ],
            notes=[
                "Returns NOT_FOUND if the group does not exist",
                "The returned account IDs can be used with group_add_user and group_remove_user",
                "Inactive users may still appear in the member list",
            ],
        )


class GroupAddUserTool(BaseTool):
    """Add a user to a group."""

    name = "group_add_user"
    category = "groups"
    description = "Add a user to a group by account ID"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "Name of the group",
            },
            "account_id": {
                "type": "string",
                "description": "Atlassian account ID of the user to add",
            },
        },
        "required": ["group_name", "account_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Add a user to a group."""
        validate_required(arguments, "group_name", "account_id")
        group_name = validate_string(arguments["group_name"], "group_name")
        account_id = validate_string(arguments["account_id"], "account_id")

        # The Jira API requires groupname as a query parameter on POST.
        # The base post() method does not accept params, so we encode
        # the query parameter directly in the path.
        from urllib.parse import quote

        encoded_name = quote(group_name, safe="")
        result = await self._platform_client.post(
            f"/group/user?groupname={encoded_name}",
            json={"accountId": account_id},
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Add a user to a group by their Atlassian account ID. "
                "The user will inherit all permissions granted to the group."
            ),
            parameters=[
                ParameterGuide(
                    name="group_name",
                    type="string",
                    required=True,
                    description="Name of the group to add the user to",
                ),
                ParameterGuide(
                    name="account_id",
                    type="string",
                    required=True,
                    description="Atlassian account ID of the user to add",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "accountId": "5b10ac8d82e05b22cc7d4ef5",
                    "displayName": "Jane Smith",
                    "emailAddress": "jane@example.com",
                    "active": True,
                },
            },
            examples=[
                ToolExample(
                    description="Add a user to a group",
                    parameters={
                        "group_name": "developers",
                        "account_id": "5b10ac8d82e05b22cc7d4ef5",
                    },
                    expected_behaviour="Adds the user to the group and returns their details",
                ),
            ],
            related_tools=[
                "group_get_members",
                "group_remove_user",
                "group_list",
            ],
            notes=[
                "Requires Jira Administrator permissions",
                "Returns NOT_FOUND if the group or user does not exist",
                "Silently succeeds if the user is already a member of the group",
                "Use group_get_members to find existing account IDs",
            ],
        )


class GroupRemoveUserTool(BaseTool):
    """Remove a user from a group."""

    name = "group_remove_user"
    category = "groups"
    description = "Remove a user from a group by account ID"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "Name of the group",
            },
            "account_id": {
                "type": "string",
                "description": "Atlassian account ID of the user to remove",
            },
        },
        "required": ["group_name", "account_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Remove a user from a group."""
        validate_required(arguments, "group_name", "account_id")
        group_name = validate_string(arguments["group_name"], "group_name")
        account_id = validate_string(arguments["account_id"], "account_id")

        await self._platform_client.delete(
            "/group/user",
            params={"groupname": group_name, "accountId": account_id},
        )

        return ToolResult.ok(
            data={
                "group_name": group_name,
                "account_id": account_id,
                "removed": True,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Remove a user from a group by their Atlassian account ID. "
                "The user will lose all permissions granted via this group."
            ),
            parameters=[
                ParameterGuide(
                    name="group_name",
                    type="string",
                    required=True,
                    description="Name of the group to remove the user from",
                ),
                ParameterGuide(
                    name="account_id",
                    type="string",
                    required=True,
                    description="Atlassian account ID of the user to remove",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "group_name": "developers",
                    "account_id": "5b10ac8d82e05b22cc7d4ef5",
                    "removed": True,
                },
            },
            examples=[
                ToolExample(
                    description="Remove a user from a group",
                    parameters={
                        "group_name": "developers",
                        "account_id": "5b10ac8d82e05b22cc7d4ef5",
                    },
                    expected_behaviour="Removes the user from the group",
                ),
            ],
            related_tools=[
                "group_get_members",
                "group_add_user",
                "group_list",
            ],
            notes=[
                "Requires Jira Administrator permissions",
                "Returns NOT_FOUND if the group does not exist",
                "Silently succeeds if the user is not currently a member",
                "The user account itself is not deleted, only the group membership",
            ],
        )
