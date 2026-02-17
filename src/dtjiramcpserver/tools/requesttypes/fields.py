"""Request type tool: requesttype_get_fields.

Retrieves fields configured for a request type (FR-014).
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
)


class RequestTypeGetFieldsTool(BaseTool):
    """Get fields for a request type."""

    name = "requesttype_get_fields"
    category = "requesttypes"
    description = "Get the fields configured for a request type"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "service_desk_id": {
                "type": "integer",
                "description": "Service desk ID",
            },
            "request_type_id": {
                "type": "integer",
                "description": "Request type ID",
            },
        },
        "required": ["service_desk_id", "request_type_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Get fields for a request type."""
        validate_required(arguments, "service_desk_id", "request_type_id")
        desk_id = validate_integer(
            arguments["service_desk_id"], "service_desk_id", minimum=1
        )
        rt_id = validate_integer(
            arguments["request_type_id"], "request_type_id", minimum=1
        )

        result = await self._jsm_client.get(
            f"/servicedesk/{desk_id}/requesttype/{rt_id}/field"
        )

        # The API returns fields in a requestTypeFields array
        fields = result.get("requestTypeFields", result.get("values", []))
        if isinstance(result, dict) and "requestTypeFields" not in result and "values" not in result:
            # If the response is the fields array directly
            fields = result if isinstance(result, list) else [result]

        return ToolResult.ok(data=fields)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Retrieve the fields configured for a specific request type. "
                "This shows what fields are presented to customers when they "
                "raise a request of this type, including required/optional status."
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
                    name="request_type_id",
                    type="integer",
                    required=True,
                    description="Request type ID",
                    constraints="Must be a positive integer",
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "fieldId": "summary",
                        "name": "Summary",
                        "required": True,
                        "jiraSchema": {"type": "string"},
                    },
                    {
                        "fieldId": "description",
                        "name": "Description",
                        "required": False,
                        "jiraSchema": {"type": "string"},
                    },
                ],
            },
            examples=[
                ToolExample(
                    description="Get fields for a request type",
                    parameters={"service_desk_id": 1, "request_type_id": 5},
                    expected_behaviour="Returns all fields configured for the request type",
                ),
            ],
            related_tools=[
                "requesttype_get",
                "requesttype_list",
                "field_list",
            ],
            notes=[
                "Fields include both standard and custom fields",
                "The required flag indicates whether the customer must fill in the field",
                "Use this to understand what data is needed to create a request",
            ],
        )
