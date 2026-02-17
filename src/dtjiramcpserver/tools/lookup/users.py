"""Lookup tools: user_search.

User search via the Jira Platform REST API v3.
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


class UserSearchTool(BaseTool):
    """Search for Jira users by name or email."""

    name = "user_search"
    category = "lookup"
    description = "Search for Jira users by name or email address"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (name or email address)",
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
        "required": ["query"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Search for users by name or email.

        GET /user/search returns a flat array of user objects up to maxResults.
        """
        validate_required(arguments, "query")
        query = validate_string(arguments["query"], "query", min_length=1)
        start, limit = validate_pagination(arguments, default_limit=50, max_limit=100)

        result = await self._platform_client.get(
            "/user/search",
            params={
                "query": query,
                "startAt": start,
                "maxResults": limit,
            },
        )

        # The API returns a flat array of user objects
        users = result if isinstance(result, list) else []

        pagination = {
            "start": start,
            "limit": limit,
            "total": start + len(users),
            "has_more": len(users) >= limit,
        }

        return ToolResult.ok(data=users, pagination=pagination)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Search for Jira users by display name or email address. Returns "
                "matching user accounts including their accountId, which is required "
                "by other tools such as issue_create and issue_update for setting "
                "assignees and reporters."
            ),
            parameters=[
                ParameterGuide(
                    name="query",
                    type="string",
                    required=True,
                    description="Search query matching user display name or email address",
                ),
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
                        "accountId": "5b10ac8d82e05b22cc7d4ef5",
                        "accountType": "atlassian",
                        "displayName": "Jane Smith",
                        "emailAddress": "jane.smith@example.com",
                        "active": True,
                        "avatarUrls": {},
                    },
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 1,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="Search by name",
                    parameters={"query": "Jane"},
                    expected_behaviour="Returns users whose display name contains 'Jane'",
                ),
                ToolExample(
                    description="Search by email",
                    parameters={"query": "jane.smith@example.com"},
                    expected_behaviour="Returns the user matching the email address",
                ),
                ToolExample(
                    description="Search with pagination",
                    parameters={"query": "smith", "start": 0, "limit": 10},
                    expected_behaviour="Returns up to 10 users matching 'smith'",
                ),
            ],
            related_tools=[
                "issue_create",
                "issue_update",
                "servicedesk_add_customers",
            ],
            notes=[
                "The accountId field is required when setting assignees or reporters on issues",
                "Searches match against both display name and email address",
                "Only active Atlassian accounts are returned by default",
                "The API does not provide a total count; has_more is estimated from result size",
                "Use the accountId (not email) when passing user references to other tools",
            ],
        )
