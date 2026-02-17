"""Issue tool: jql_search.

Executes JQL queries against the Jira Platform API and returns
paginated results (FR-003).

Uses POST /rest/api/3/search/jql which returns cursor-based
pagination (nextPageToken / isLast) instead of the deprecated
GET /rest/api/3/search offset-based approach.
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
    validate_integer,
    validate_required,
    validate_string,
)


class JqlSearchTool(BaseTool):
    """Search for Jira issues using JQL queries."""

    name = "jql_search"
    category = "issues"
    description = "Search for issues using a JQL query with paginated results"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "jql": {
                "type": "string",
                "description": "JQL query string",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 50, max: 100)",
            },
            "next_page_token": {
                "type": "string",
                "description": "Cursor token for fetching the next page of results",
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of field keys to include in results",
            },
            "expand": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of expansions to include (e.g. changelog, renderedFields)",
            },
        },
        "required": ["jql"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Execute a JQL search and return cursor-paginated results.

        Uses the POST /search/jql endpoint (Atlassian migrated from
        GET /search, which was removed in 2025).
        """
        validate_required(arguments, "jql")
        jql = validate_string(arguments["jql"], "jql", min_length=1)

        limit = 50
        if "limit" in arguments and arguments["limit"] is not None:
            limit = validate_integer(arguments["limit"], "limit", minimum=1, maximum=100)

        body: dict[str, Any] = {
            "jql": jql,
            "maxResults": limit,
        }

        next_page_token = arguments.get("next_page_token")
        if next_page_token:
            body["nextPageToken"] = next_page_token

        fields = arguments.get("fields")
        if fields:
            body["fields"] = fields

        expand = arguments.get("expand")
        if expand:
            body["expand"] = expand

        response = await self._platform_client.post("/search/jql", json=body)

        issues = response.get("issues", [])
        is_last = response.get("isLast", True)
        returned_token = response.get("nextPageToken")

        pagination: dict[str, Any] = {
            "limit": limit,
            "returned": len(issues),
            "has_more": not is_last,
        }
        if returned_token and not is_last:
            pagination["next_page_token"] = returned_token

        return ToolResult.ok(data=issues, pagination=pagination)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Search for Jira issues using JQL (Jira Query Language). "
                "Returns paginated results with issue data. Use the fields "
                "parameter to limit the response size for large result sets. "
                "Results use cursor-based pagination; pass the returned "
                "next_page_token to fetch subsequent pages."
            ),
            parameters=[
                ParameterGuide(
                    name="jql",
                    type="string",
                    required=True,
                    description="JQL query string (e.g. 'project = PROJ AND status = Open')",
                ),
                ParameterGuide(
                    name="limit",
                    type="integer",
                    required=False,
                    description="Maximum number of results to return",
                    default=50,
                    constraints="Must be between 1 and 100",
                ),
                ParameterGuide(
                    name="next_page_token",
                    type="string",
                    required=False,
                    description="Cursor token from a previous search to fetch the next page",
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
                "data": [{"key": "PROJ-123", "fields": {"summary": "..."}}],
                "pagination": {
                    "limit": 50,
                    "returned": 50,
                    "has_more": True,
                    "next_page_token": "eyJ...",
                },
            },
            examples=[
                ToolExample(
                    description="Search for open issues in a project",
                    parameters={"jql": "project = PROJ AND status = Open"},
                    expected_behaviour="Returns open issues in PROJ with pagination metadata",
                ),
                ToolExample(
                    description="Search with specific fields",
                    parameters={
                        "jql": "assignee = currentUser() ORDER BY updated DESC",
                        "fields": ["summary", "status", "priority"],
                        "limit": 10,
                    },
                    expected_behaviour="Returns up to 10 issues with only the specified fields",
                ),
                ToolExample(
                    description="Fetch the next page of results",
                    parameters={
                        "jql": "project = PROJ",
                        "next_page_token": "eyJ...",
                    },
                    expected_behaviour="Returns the next page of results using the cursor token",
                ),
            ],
            related_tools=["issue_get", "issue_create"],
            notes=[
                "JQL syntax: https://support.atlassian.com/jira-service-management-cloud/docs/jql-fields/",
                "Use 'fields' to limit response size for better performance",
                "Maximum limit is 100 results per request",
                "Pass next_page_token from the pagination response to fetch subsequent pages",
            ],
        )
