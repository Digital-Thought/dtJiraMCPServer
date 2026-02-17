"""Knowledge base tools: knowledgebase_search.

Knowledge base article search via the JSM REST API (FR-022).
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


class KnowledgeBaseSearchTool(BaseTool):
    """Search knowledge base articles."""

    name = "knowledgebase_search"
    category = "knowledgebase"
    description = "Search knowledge base articles across service desks"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query text",
            },
            "highlight": {
                "type": "boolean",
                "description": "Whether to highlight matching text (default: true)",
            },
            "service_desk_id": {
                "type": "integer",
                "description": "Optional service desk ID to scope the search",
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
        """Search knowledge base articles."""
        validate_required(arguments, "query")
        query = validate_string(arguments["query"], "query", min_length=1)
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] = {"query": query}

        highlight = arguments.get("highlight")
        if highlight is not None:
            extra_params["highlight"] = str(highlight).lower()

        service_desk_id = arguments.get("service_desk_id")
        if service_desk_id is not None:
            path = f"/servicedesk/{service_desk_id}/knowledgebase/article"
        else:
            path = "/knowledgebase/article"

        paginated = await self._jsm_client.list_paginated(
            path,
            start=start,
            limit=limit,
            extra_params=extra_params,
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
                "Search knowledge base articles across all service desks or "
                "within a specific service desk. Returns matching articles "
                "with titles, excerpts, and source information."
            ),
            parameters=[
                ParameterGuide(
                    name="query",
                    type="string",
                    required=True,
                    description="Search query text",
                ),
                ParameterGuide(
                    name="highlight",
                    type="boolean",
                    required=False,
                    description="Whether to highlight matching text in results",
                    default=True,
                ),
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=False,
                    description="Service desk ID to scope the search to",
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
                        "title": "How to reset your password",
                        "excerpt": "To reset your password, go to...",
                        "source": {
                            "type": "confluence",
                            "pageId": "12345",
                        },
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 3,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="Search all knowledge bases",
                    parameters={"query": "password reset"},
                    expected_behaviour="Returns articles matching 'password reset'",
                ),
                ToolExample(
                    description="Search within a service desk",
                    parameters={
                        "query": "VPN setup",
                        "service_desk_id": 1,
                    },
                    expected_behaviour=(
                        "Returns articles from service desk 1 matching 'VPN setup'"
                    ),
                ),
            ],
            related_tools=["servicedesk_list"],
            notes=[
                "Searches across Confluence spaces linked to service desks",
                "Highlighting wraps matches in @@@hl@@@ / @@@endhl@@@ markers",
                "Scope to a service desk for more relevant results",
            ],
        )
