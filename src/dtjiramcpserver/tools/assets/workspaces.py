"""Asset tools: assets_get_workspaces.

Asset workspace queries via the JSM REST API (FR-024).
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


class AssetsGetWorkspacesTool(BaseTool):
    """Get available asset workspaces."""

    name = "assets_get_workspaces"
    category = "assets"
    description = "List available Assets workspace IDs"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get asset workspaces."""
        result = await self._jsm_client.get("/assets/workspace")

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all accessible Assets workspace IDs. Workspaces are "
                "the top-level containers for asset data in Jira Service "
                "Management."
            ),
            parameters=[],
            response_format={
                "success": True,
                "data": {
                    "values": [
                        {
                            "workspaceId": "abc-123-def",
                            "name": "My Workspace",
                        }
                    ]
                },
            },
            examples=[
                ToolExample(
                    description="List asset workspaces",
                    parameters={},
                    expected_behaviour="Returns all accessible workspace IDs",
                ),
            ],
            related_tools=["servicedesk_list"],
            notes=[
                "Uses the non-deprecated /assets/workspace endpoint",
                "Workspace IDs are required for other asset operations",
                "Returns empty if Assets is not enabled for the instance",
            ],
        )
