"""Service desk tools: servicedesk_get_customers, _add_customers, _remove_customers.

Customer management for JSM service desks (FR-011).
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
    validate_string,
)


class ServiceDeskGetCustomersTool(BaseTool):
    """List customers for a service desk."""

    name = "servicedesk_get_customers"
    category = "servicedesk"
    description = "List customers for a service desk with optional search"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "query": {
                "type": "string",
                "description": "Optional search query to filter customers by name or email",
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
        """List customers for a service desk."""
        validate_required(arguments, "service_desk_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        start, limit = validate_pagination(arguments)

        extra_params: dict[str, Any] | None = None
        query = arguments.get("query")
        if query:
            extra_params = {"query": query}

        paginated = await self._jsm_client.list_paginated(
            f"/servicedesk/{desk_id}/customer",
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
                "List customers associated with a service desk. Optionally "
                "filter by name or email using the query parameter."
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
                    name="query",
                    type="string",
                    required=False,
                    description="Search query to filter customers by name or email",
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
                        "displayName": "Jane Smith",
                        "emailAddress": "jane@example.com",
                    }
                ],
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 25,
                    "has_more": False,
                },
            },
            examples=[
                ToolExample(
                    description="List all customers",
                    parameters={"service_desk_id": 1},
                    expected_behaviour="Returns all customers for the service desk",
                ),
                ToolExample(
                    description="Search for a customer",
                    parameters={"service_desk_id": 1, "query": "jane"},
                    expected_behaviour="Returns customers matching the search query",
                ),
            ],
            related_tools=[
                "servicedesk_add_customers",
                "servicedesk_remove_customers",
            ],
            notes=[
                "The query parameter searches across display name and email",
                "Requires Service Desk Agent permissions",
            ],
        )


class ServiceDeskAddCustomersTool(BaseTool):
    """Add customers to a service desk."""

    name = "servicedesk_add_customers"
    category = "servicedesk"
    description = "Add customers to a service desk by account IDs"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "account_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of Atlassian account IDs to add as customers",
            },
        },
        "required": ["service_desk_id", "account_ids"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Add customers to a service desk."""
        validate_required(arguments, "service_desk_id", "account_ids")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        account_ids = arguments["account_ids"]
        if not isinstance(account_ids, list) or not account_ids:
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message="Parameter 'account_ids' must be a non-empty list",
                field="account_ids",
                reason="invalid_type",
            )

        await self._jsm_client.post(
            f"/servicedesk/{desk_id}/customer",
            json={"accountIds": account_ids},
        )

        return ToolResult.ok(
            data={
                "service_desk_id": desk_id,
                "added_count": len(account_ids),
                "account_ids": account_ids,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Add one or more customers to a service desk by their "
                "Atlassian account IDs."
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
                    name="account_ids",
                    type="array[string]",
                    required=True,
                    description="Atlassian account IDs to add as customers",
                    constraints="Must be a non-empty list",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "service_desk_id": 1,
                    "added_count": 2,
                    "account_ids": ["id1", "id2"],
                },
            },
            examples=[
                ToolExample(
                    description="Add a customer to a service desk",
                    parameters={
                        "service_desk_id": 1,
                        "account_ids": ["5b10ac8d82e05b22cc7d4ef5"],
                    },
                    expected_behaviour="Adds the account as a customer of the service desk",
                ),
            ],
            related_tools=[
                "servicedesk_get_customers",
                "servicedesk_remove_customers",
            ],
            notes=[
                "Requires Service Desk Administrator permissions",
                "Silently succeeds if account is already a customer",
            ],
        )


class ServiceDeskRemoveCustomersTool(BaseTool):
    """Remove customers from a service desk."""

    name = "servicedesk_remove_customers"
    category = "servicedesk"
    description = "Remove customers from a service desk by account IDs"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "account_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of Atlassian account IDs to remove from customers",
            },
        },
        "required": ["service_desk_id", "account_ids"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Remove customers from a service desk."""
        validate_required(arguments, "service_desk_id", "account_ids")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        account_ids = arguments["account_ids"]
        if not isinstance(account_ids, list) or not account_ids:
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message="Parameter 'account_ids' must be a non-empty list",
                field="account_ids",
                reason="invalid_type",
            )

        await self._jsm_client.delete(
            f"/servicedesk/{desk_id}/customer",
            json={"accountIds": account_ids},
        )

        return ToolResult.ok(
            data={
                "service_desk_id": desk_id,
                "removed_count": len(account_ids),
                "account_ids": account_ids,
            }
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Remove one or more customers from a service desk by their "
                "Atlassian account IDs."
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
                    name="account_ids",
                    type="array[string]",
                    required=True,
                    description="Atlassian account IDs to remove from customers",
                    constraints="Must be a non-empty list",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "service_desk_id": 1,
                    "removed_count": 1,
                    "account_ids": ["5b10ac8d82e05b22cc7d4ef5"],
                },
            },
            examples=[
                ToolExample(
                    description="Remove a customer from a service desk",
                    parameters={
                        "service_desk_id": 1,
                        "account_ids": ["5b10ac8d82e05b22cc7d4ef5"],
                    },
                    expected_behaviour="Removes the account from the service desk's customers",
                ),
            ],
            related_tools=[
                "servicedesk_get_customers",
                "servicedesk_add_customers",
            ],
            notes=[
                "Requires Service Desk Administrator permissions",
                "Silently succeeds if account is not currently a customer",
                "Uses DELETE with a JSON body as required by the JSM API",
            ],
        )
