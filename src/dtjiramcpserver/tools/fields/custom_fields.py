"""Field tools: field_list, field_create, field_update.

Custom field management via the Jira Platform REST API v3 (FR-015).
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
    validate_enum,
    validate_required,
    validate_string,
)


class FieldListTool(BaseTool):
    """List all fields (system and custom)."""

    name = "field_list"
    category = "fields"
    description = "List all Jira fields (system and custom)"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "type_filter": {
                "type": "string",
                "description": "Filter by field type: 'system', 'custom', or 'all' (default: 'all')",
            },
        },
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """List all fields.

        GET /field returns all fields as a flat array (no pagination).
        """
        type_filter = "all"
        if "type_filter" in arguments and arguments["type_filter"] is not None:
            type_filter = validate_enum(
                arguments["type_filter"],
                "type_filter",
                ["system", "custom", "all"],
            )

        response = await self._platform_client.get("/field")

        # The API returns a flat array
        fields = response if isinstance(response, list) else []

        if type_filter == "custom":
            fields = [f for f in fields if f.get("custom", False)]
        elif type_filter == "system":
            fields = [f for f in fields if not f.get("custom", False)]

        return ToolResult.ok(
            data=fields,
            pagination={
                "start": 0,
                "limit": len(fields),
                "total": len(fields),
                "has_more": False,
            },
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "List all fields in the Jira instance, including both system "
                "and custom fields. Optionally filter by type. Note that this "
                "endpoint returns all fields at once (no pagination)."
            ),
            parameters=[
                ParameterGuide(
                    name="type_filter",
                    type="string",
                    required=False,
                    description="Filter by field type",
                    default="all",
                    valid_values=["system", "custom", "all"],
                ),
            ],
            response_format={
                "success": True,
                "data": [
                    {
                        "id": "summary",
                        "name": "Summary",
                        "custom": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "id": "customfield_10001",
                        "name": "Story Points",
                        "custom": True,
                        "schema": {"type": "number"},
                    },
                ],
            },
            examples=[
                ToolExample(
                    description="List all fields",
                    parameters={},
                    expected_behaviour="Returns all system and custom fields",
                ),
                ToolExample(
                    description="List only custom fields",
                    parameters={"type_filter": "custom"},
                    expected_behaviour="Returns only custom fields",
                ),
            ],
            related_tools=["field_create", "field_update", "field_get_contexts"],
            notes=[
                "Returns all fields in a single response (no pagination)",
                "Custom field IDs use the format 'customfield_NNNNN'",
                "Use type_filter to reduce the response size",
            ],
        )


class FieldCreateTool(BaseTool):
    """Create a new custom field."""

    name = "field_create"
    category = "fields"
    description = "Create a new custom field in Jira"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Display name for the custom field",
            },
            "field_type": {
                "type": "string",
                "description": "Field type identifier (e.g. 'com.atlassian.jira.plugin.system.customfieldtypes:textfield')",
            },
            "description": {
                "type": "string",
                "description": "Description of the field's purpose",
            },
            "searcher_key": {
                "type": "string",
                "description": "Searcher key for JQL support (e.g. 'com.atlassian.jira.plugin.system.customfieldtypes:textsearcher')",
            },
        },
        "required": ["name", "field_type"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Create a custom field."""
        validate_required(arguments, "name", "field_type")
        name = validate_string(arguments["name"], "name", min_length=1, max_length=255)
        field_type = validate_string(arguments["field_type"], "field_type", min_length=1)

        body: dict[str, Any] = {
            "name": name,
            "type": field_type,
        }

        description = arguments.get("description")
        if description:
            body["description"] = description

        searcher_key = arguments.get("searcher_key")
        if searcher_key:
            body["searcherKey"] = searcher_key

        result = await self._platform_client.post("/field", json=body)

        return ToolResult.ok(data=result)

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Create a new custom field in Jira. The field must be added "
                "to a screen before it will be visible on issues. A searcher "
                "key should be specified to enable JQL searching."
            ),
            parameters=[
                ParameterGuide(
                    name="name",
                    type="string",
                    required=True,
                    description="Display name for the custom field",
                    constraints="1-255 characters",
                ),
                ParameterGuide(
                    name="field_type",
                    type="string",
                    required=True,
                    description="Full field type identifier",
                    valid_values=[
                        "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
                        "com.atlassian.jira.plugin.system.customfieldtypes:textarea",
                        "com.atlassian.jira.plugin.system.customfieldtypes:float",
                        "com.atlassian.jira.plugin.system.customfieldtypes:select",
                        "com.atlassian.jira.plugin.system.customfieldtypes:multiselect",
                        "com.atlassian.jira.plugin.system.customfieldtypes:datepicker",
                    ],
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="Description of the field's purpose",
                ),
                ParameterGuide(
                    name="searcher_key",
                    type="string",
                    required=False,
                    description="Searcher key to enable JQL searching on this field",
                ),
            ],
            response_format={
                "success": True,
                "data": {
                    "id": "customfield_10100",
                    "name": "Release Notes",
                    "schema": {"type": "string", "custom": "..."},
                },
            },
            examples=[
                ToolExample(
                    description="Create a text field",
                    parameters={
                        "name": "Release Notes",
                        "field_type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
                    },
                    expected_behaviour="Creates a new single-line text custom field",
                ),
            ],
            related_tools=["field_list", "field_get_contexts", "screen_add_field"],
            notes=[
                "Requires Jira Administrator permissions",
                "The field must be added to a screen to be visible",
                "Use field_add_context to control which projects the field applies to",
            ],
        )


class FieldUpdateTool(BaseTool):
    """Update an existing custom field."""

    name = "field_update"
    category = "fields"
    description = "Update an existing custom field"
    mutates = True
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "field_id": {
                "type": "string",
                "description": "Custom field ID (e.g. 'customfield_10001')",
            },
            "name": {
                "type": "string",
                "description": "New display name",
            },
            "description": {
                "type": "string",
                "description": "New description",
            },
            "searcher_key": {
                "type": "string",
                "description": "New searcher key",
            },
        },
        "required": ["field_id"],
    }

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Update a custom field."""
        validate_required(arguments, "field_id")
        field_id = validate_string(arguments["field_id"], "field_id", min_length=1)

        body: dict[str, Any] = {}
        if "name" in arguments and arguments["name"] is not None:
            body["name"] = validate_string(arguments["name"], "name", min_length=1)
        if "description" in arguments and arguments["description"] is not None:
            body["description"] = arguments["description"]
        if "searcher_key" in arguments and arguments["searcher_key"] is not None:
            body["searcherKey"] = arguments["searcher_key"]

        if not body:
            from dtjiramcpserver.exceptions import InputValidationError

            raise InputValidationError(
                message="At least one field to update must be provided (name, description, or searcher_key)",
                field="fields",
                reason="empty",
            )

        await self._platform_client.put(f"/field/{field_id}", json=body)

        return ToolResult.ok(
            data={"field_id": field_id, "updated": True}
        )

    def get_guide(self) -> ToolGuide:
        """Return self-documentation guide."""
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=(
                "Update the name, description, or searcher key of an existing "
                "custom field. At least one field must be provided to update."
            ),
            parameters=[
                ParameterGuide(
                    name="field_id",
                    type="string",
                    required=True,
                    description="Custom field ID (e.g. 'customfield_10001')",
                ),
                ParameterGuide(
                    name="name",
                    type="string",
                    required=False,
                    description="New display name for the field",
                ),
                ParameterGuide(
                    name="description",
                    type="string",
                    required=False,
                    description="New description for the field",
                ),
                ParameterGuide(
                    name="searcher_key",
                    type="string",
                    required=False,
                    description="New searcher key for JQL support",
                ),
            ],
            response_format={
                "success": True,
                "data": {"field_id": "customfield_10001", "updated": True},
            },
            examples=[
                ToolExample(
                    description="Rename a custom field",
                    parameters={
                        "field_id": "customfield_10001",
                        "name": "Story Points (v2)",
                    },
                    expected_behaviour="Updates the field's display name",
                ),
            ],
            related_tools=["field_list", "field_create"],
            notes=[
                "Requires Jira Administrator permissions",
                "Only custom fields can be updated; system fields cannot be modified",
                "Returns NOT_FOUND if the field does not exist",
            ],
        )
