"""Service desk tools: servicedesk_get_organisations, _add, _remove.

Organisation management for JSM service desks (FR-012).

Note: Atlassian uses American English "organization" in API paths and parameters.
Tool names and documentation use Australian English "organisation".
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
    validate_pagination,
    validate_required,
)


class ServiceDeskGetOrganisationsTool(BaseTool):
    """List organisations for a service desk."""

    name = "servicedesk_get_organisations"
    category = "servicedesk"
    description = "List organisations associated with a service desk"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
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
        "required": ["service_desk_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List organisations for a service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/organization",
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
                "List all organisations associated with a service desk. "
                "Organisations group customers for easier management of "
                "service desk access."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID",
                    constraints="Must be a positive integer",
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
                    {"id": "1", "name": "ACME Corporation"}
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
                    description="List organisations for a service desk",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns all organisations linked to the service desk",
                ),
            ],
            related_tools=[
                "servicedesk_add_organisation",
                "servicedesk_remove_organisation",
            ],
            notes=[
                "Requires Service Desk Agent permissions",
                "Use the returned organisation ID in add/remove operations",
            ],
        )


class ServiceDeskAddOrganisationTool(BaseTool):
    """Add an organisation to a service desk."""

    name = "servicedesk_add_organisation"
    category = "servicedesk"
    description = "Add an organisation to a service desk"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "organisation_id": {
                "type": "integer",
                "description": "Organisation ID to add",
            },
        },
        "required": ["service_desk_id", "organisation_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Add an organisation to a service desk."""
        validate_required(arguments, "service_desk_id", "organisation_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        org_id = validate_integer(
            arguments["organisation_id"], "organisation_id", minimum=1
        )

        await self._jsm_client.post(
            f"/servicedesk/{desk_id}/organization",
            json={"organizationId": org_id},
        )

        return ToolResult.ok(
            data={
                "service_desk_id": desk_id,
                "organisation_id": org_id,
                "added": True,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Add an organisation to a service desk, granting all members "
                "of the organisation customer access to the service desk."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="organisation_id",
                    type="integer",
                    required=True,
                    description="Organisation ID to add",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "service_desk_id": 1,
                    "organisation_id": 5,
                    "added": True,
                },
            },
            examples=[
                ToolExample(
                    description="Add an organisation to a service desk",
                    parameters={"service_desk_id": 1, "organisation_id": 5},
                    expected_behaviour="Links the organisation to the service desk",
                ),
            ],
            related_tools=[
                "servicedesk_get_organisations",
                "servicedesk_remove_organisation",
            ],
            notes=[
                "Requires Service Desk Administrator permissions",
                "Silently succeeds if the organisation is already linked",
            ],
        )


class ServiceDeskRemoveOrganisationTool(BaseTool):
    """Remove an organisation from a service desk."""

    name = "servicedesk_remove_organisation"
    category = "servicedesk"
    description = "Remove an organisation from a service desk"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "organisation_id": {
                "type": "integer",
                "description": "Organisation ID to remove",
            },
        },
        "required": ["service_desk_id", "organisation_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Remove an organisation from a service desk."""
        validate_required(arguments, "service_desk_id", "organisation_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        org_id = validate_integer(
            arguments["organisation_id"], "organisation_id", minimum=1
        )

        await self._jsm_client.delete(
            f"/servicedesk/{desk_id}/organization",
            json={"organizationId": org_id},
        )

        return ToolResult.ok(
            data={
                "service_desk_id": desk_id,
                "organisation_id": org_id,
                "removed": True,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Remove an organisation from a service desk, revoking "
                "customer access for all members of the organisation."
            ),
            parameters=[
                ParameterGuide(
                    name="service_desk_id",
                    type="integer",
                    required=True,
                    description="Service desk ID",
                    constraints="Must be a positive integer",
                ),
                ParameterGuide(
                    name="organisation_id",
                    type="integer",
                    required=True,
                    description="Organisation ID to remove",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "service_desk_id": 1,
                    "organisation_id": 5,
                    "removed": True,
                },
            },
            examples=[
                ToolExample(
                    description="Remove an organisation from a service desk",
                    parameters={"service_desk_id": 1, "organisation_id": 5},
                    expected_behaviour="Unlinks the organisation from the service desk",
                ),
            ],
            related_tools=[
                "servicedesk_get_organisations",
                "servicedesk_add_organisation",
            ],
            notes=[
                "Requires Service Desk Administrator permissions",
                "Silently succeeds if the organisation is not currently linked",
                "Uses DELETE with a JSON body as required by the JSM API",
            ],
        )
