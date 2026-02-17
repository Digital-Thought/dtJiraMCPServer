"""SLA tools: sla_get_metrics, sla_get_detail.

SLA management via the JSM REST API (FR-023).
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
    validate_issue_key,
    validate_pagination,
    validate_required,
)


class SlaGetMetricsTool(BaseTool):
    """Get SLA metrics for a customer request."""

    name = "sla_get_metrics"
    category = "sla"
    description = "Get all SLA metrics for a customer request"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. 'HELP-123')",
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
        "required": ["issue_key"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get SLA metrics for a request."""
        validate_required(arguments, "issue_key")
        issue_key = validate_issue_key(arguments["issue_key"], "issue_key")
        start, limit = validate_pagination(arguments)

        paginated = await self._jsm_client.list_paginated(
            f"/request/{issue_key}/sla",
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
                "Retrieve all SLA metrics for a customer request. Returns "
                "each SLA metric with its current status, remaining time, "
                "and breach information."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key (e.g. 'HELP-123')",
                    constraints="Must be a valid Jira issue key (PROJECT-NUMBER)",
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
                        "id": "10001",
                        "name": "Time to first response",
                        "ongoingCycle": {
                            "breached": False,
                            "remainingTime": {"millis": 3600000, "friendly": "1h"},
                            "goalDuration": {"millis": 14400000, "friendly": "4h"},
                        },
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 2,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="Get SLA metrics for a request",
                    parameters={"issue_key": "HELP-123"},
                    expected_behaviour="Returns all SLA metrics for the request",
                ),
            ],
            related_tools=["sla_get_detail", "issue_get"],
            notes=[
                "Only works with issues raised as customer requests in a service desk",
                "Returns empty results for issues without SLA metrics",
                "Use sla_get_detail for detailed cycle information",
            ],
        )


class SlaGetDetailTool(BaseTool):
    """Get detailed SLA information for a specific metric."""

    name = "sla_get_detail"
    category = "sla"
    description = "Get detailed SLA information for a specific metric on a request"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. 'HELP-123')",
            },
            "metric_id": {
                "type": "integer",
                "description": "SLA metric ID (from sla_get_metrics)",
            },
        },
        "required": ["issue_key", "metric_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get detailed SLA information for a specific metric."""
        validate_required(arguments, "issue_key", "metric_id")
        issue_key = validate_issue_key(arguments["issue_key"], "issue_key")
        metric_id = validate_integer(
            arguments["metric_id"], "metric_id", minimum=1
        )

        result = await self._jsm_client.get(
            f"/request/{issue_key}/sla/{metric_id}"
        )

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve detailed SLA information for a specific metric on "
                "a customer request, including cycle history, breach status, "
                "and goal details."
            ),
            parameters=[
                ParameterGuide(
                    name="issue_key",
                    type="string",
                    required=True,
                    description="Issue key (e.g. 'HELP-123')",
                    constraints="Must be a valid Jira issue key (PROJECT-NUMBER)",
                ),
                ParameterGuide(
                    name="metric_id",
                    type="integer",
                    required=True,
                    description="SLA metric ID (from sla_get_metrics)",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "10001",
                    "name": "Time to first response",
                    "ongoingCycle": {
                        "breached": False,
                        "remainingTime": {"millis": 3600000, "friendly": "1h"},
                        "goalDuration": {"millis": 14400000, "friendly": "4h"},
                        "elapsedTime": {"millis": 10800000, "friendly": "3h"},
                        "paused": False,
                    },
                    "completedCycles": [],
                },
            },
            examples=[
                ToolExample(
                    description="Get SLA detail for a metric",
                    parameters={"issue_key": "HELP-123", "metric_id": 10001},
                    expected_behaviour="Returns detailed SLA cycle information",
                ),
            ],
            related_tools=["sla_get_metrics", "issue_get"],
            notes=[
                "Returns NOT_FOUND if the issue or metric does not exist",
                "The ongoingCycle shows the current SLA status",
                "completedCycles shows historical SLA cycle data",
            ],
        )
