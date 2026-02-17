"""Tests for service desk management tools (Phase 4)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from dtjiramcpserver.client.pagination import PaginatedResponse
from dtjiramcpserver.exceptions import InputValidationError
from dtjiramcpserver.tools.servicedesk.customers import (
    ServiceDeskAddCustomersTool,
    ServiceDeskGetCustomersTool,
    ServiceDeskRemoveCustomersTool,
)
from dtjiramcpserver.tools.servicedesk.desks import (
    ServiceDeskGetTool,
    ServiceDeskListTool,
)
from dtjiramcpserver.tools.servicedesk.organisations import (
    ServiceDeskAddOrganisationTool,
    ServiceDeskGetOrganisationsTool,
    ServiceDeskRemoveOrganisationTool,
)
from dtjiramcpserver.tools.servicedesk.queues import (
    ServiceDeskGetQueueIssuesTool,
    ServiceDeskGetQueuesTool,
)


@pytest.fixture
def jsm_client() -> AsyncMock:
    """Mocked JsmClient for service desk tools."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/servicedeskapi"
    return client


def _make_tool(tool_cls: type, client: AsyncMock) -> Any:
    """Instantiate a tool with a mocked JSM client."""
    return tool_cls(jsm_client=client)


def _paginated_response(
    results: list[Any],
    start: int = 0,
    limit: int = 50,
    total: int | None = None,
    has_more: bool = False,
) -> PaginatedResponse:
    """Create a PaginatedResponse for mocking list_paginated."""
    return PaginatedResponse(
        results=results,
        start=start,
        limit=limit,
        total=total if total is not None else len(results),
        has_more=has_more,
    )


# --------------------------------------------------------------------------- #
# ServiceDeskListTool
# --------------------------------------------------------------------------- #


class TestServiceDeskListTool:
    """Tests for servicedesk_list tool."""

    class TestExecution:
        """Successful execution tests."""

        @pytest.mark.asyncio
        async def test_list_desks(self, jsm_client: AsyncMock) -> None:
            """Lists service desks with pagination."""
            desks = [
                {"id": "1", "projectKey": "SD", "projectName": "Service Desk"},
                {"id": "2", "projectKey": "IT", "projectName": "IT Help Desk"},
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                desks, total=2
            )
            tool = _make_tool(ServiceDeskListTool, jsm_client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) == 2
            assert result.pagination["total"] == 2
            assert result.pagination["has_more"] is False

        @pytest.mark.asyncio
        async def test_list_with_pagination_params(self, jsm_client: AsyncMock) -> None:
            """Pagination parameters are passed through."""
            jsm_client.list_paginated.return_value = _paginated_response(
                [], start=10, limit=5, total=15, has_more=True
            )
            tool = _make_tool(ServiceDeskListTool, jsm_client)
            result = await tool.safe_execute({"start": 10, "limit": 5})

            assert result.success is True
            jsm_client.list_paginated.assert_called_once_with(
                "/servicedesk", start=10, limit=5
            )

    class TestGuide:
        """Guide metadata tests."""

        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskListTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_list"
            assert guide.category == "servicedesk"
            assert len(guide.examples) >= 1


# --------------------------------------------------------------------------- #
# ServiceDeskGetTool
# --------------------------------------------------------------------------- #


class TestServiceDeskGetTool:
    """Tests for servicedesk_get tool."""

    class TestValidation:
        """Input validation tests."""

        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            """Missing service_desk_id returns VALIDATION_ERROR."""
            tool = _make_tool(ServiceDeskGetTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_invalid_service_desk_id(self, jsm_client: AsyncMock) -> None:
            """Non-integer service_desk_id returns VALIDATION_ERROR."""
            tool = _make_tool(ServiceDeskGetTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": "abc"})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        """Successful execution tests."""

        @pytest.mark.asyncio
        async def test_get_desk(self, jsm_client: AsyncMock) -> None:
            """Gets a service desk by ID."""
            desk = {"id": "1", "projectKey": "SD", "projectName": "Service Desk"}
            jsm_client.get.return_value = desk
            tool = _make_tool(ServiceDeskGetTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert result.data["projectKey"] == "SD"
            jsm_client.get.assert_called_once_with("/servicedesk/1")

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_get"
            assert guide.category == "servicedesk"


# --------------------------------------------------------------------------- #
# ServiceDeskGetQueuesTool
# --------------------------------------------------------------------------- #


class TestServiceDeskGetQueuesTool:
    """Tests for servicedesk_get_queues tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetQueuesTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_queues(self, jsm_client: AsyncMock) -> None:
            """Lists queues for a service desk."""
            queues = [
                {"id": "1", "name": "Open Requests"},
                {"id": "2", "name": "All Unresolved"},
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                queues, total=2
            )
            tool = _make_tool(ServiceDeskGetQueuesTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert len(result.data) == 2
            jsm_client.list_paginated.assert_called_once()

        @pytest.mark.asyncio
        async def test_include_count(self, jsm_client: AsyncMock) -> None:
            """include_count passes includeCount query parameter."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(ServiceDeskGetQueuesTool, jsm_client)
            await tool.safe_execute({"service_desk_id": 1, "include_count": True})

            call_kwargs = jsm_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {"includeCount": "true"}

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetQueuesTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_get_queues"


# --------------------------------------------------------------------------- #
# ServiceDeskGetQueueIssuesTool
# --------------------------------------------------------------------------- #


class TestServiceDeskGetQueueIssuesTool:
    """Tests for servicedesk_get_queue_issues tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_queue_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetQueueIssuesTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetQueueIssuesTool, jsm_client)
            result = await tool.safe_execute({"queue_id": 5})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_get_queue_issues(self, jsm_client: AsyncMock) -> None:
            """Gets issues from a queue."""
            issues = [{"key": "SD-1", "fields": {"summary": "Cannot log in"}}]
            jsm_client.list_paginated.return_value = _paginated_response(
                issues, total=1
            )
            tool = _make_tool(ServiceDeskGetQueueIssuesTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "queue_id": 5}
            )

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["key"] == "SD-1"
            jsm_client.list_paginated.assert_called_once_with(
                "/servicedesk/1/queue/5/issue", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetQueueIssuesTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_get_queue_issues"


# --------------------------------------------------------------------------- #
# ServiceDeskGetCustomersTool
# --------------------------------------------------------------------------- #


class TestServiceDeskGetCustomersTool:
    """Tests for servicedesk_get_customers tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetCustomersTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_customers(self, jsm_client: AsyncMock) -> None:
            """Lists customers for a service desk."""
            customers = [
                {"accountId": "abc123", "displayName": "Jane Smith"}
            ]
            jsm_client.list_paginated.return_value = _paginated_response(
                customers, total=1
            )
            tool = _make_tool(ServiceDeskGetCustomersTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["displayName"] == "Jane Smith"

        @pytest.mark.asyncio
        async def test_search_query(self, jsm_client: AsyncMock) -> None:
            """Query parameter is passed as extra_params."""
            jsm_client.list_paginated.return_value = _paginated_response([])
            tool = _make_tool(ServiceDeskGetCustomersTool, jsm_client)
            await tool.safe_execute({"service_desk_id": 1, "query": "jane"})

            call_kwargs = jsm_client.list_paginated.call_args
            assert call_kwargs.kwargs.get("extra_params") == {"query": "jane"}

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetCustomersTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_get_customers"


# --------------------------------------------------------------------------- #
# ServiceDeskAddCustomersTool
# --------------------------------------------------------------------------- #


class TestServiceDeskAddCustomersTool:
    """Tests for servicedesk_add_customers tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_account_ids(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskAddCustomersTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False

        @pytest.mark.asyncio
        async def test_empty_account_ids(self, jsm_client: AsyncMock) -> None:
            """Empty account_ids list returns VALIDATION_ERROR."""
            tool = _make_tool(ServiceDeskAddCustomersTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "account_ids": []}
            )
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_add_customers(self, jsm_client: AsyncMock) -> None:
            """Adds customers to a service desk."""
            jsm_client.post.return_value = {}
            tool = _make_tool(ServiceDeskAddCustomersTool, jsm_client)
            result = await tool.safe_execute(
                {
                    "service_desk_id": 1,
                    "account_ids": ["id1", "id2"],
                }
            )

            assert result.success is True
            assert result.data["added_count"] == 2
            jsm_client.post.assert_called_once_with(
                "/servicedesk/1/customer",
                json={"accountIds": ["id1", "id2"]},
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskAddCustomersTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_add_customers"


# --------------------------------------------------------------------------- #
# ServiceDeskRemoveCustomersTool
# --------------------------------------------------------------------------- #


class TestServiceDeskRemoveCustomersTool:
    """Tests for servicedesk_remove_customers tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_empty_account_ids(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskRemoveCustomersTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "account_ids": []}
            )
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_remove_customers(self, jsm_client: AsyncMock) -> None:
            """Removes customers from a service desk."""
            jsm_client.delete.return_value = None
            tool = _make_tool(ServiceDeskRemoveCustomersTool, jsm_client)
            result = await tool.safe_execute(
                {
                    "service_desk_id": 1,
                    "account_ids": ["id1"],
                }
            )

            assert result.success is True
            assert result.data["removed_count"] == 1
            jsm_client.delete.assert_called_once_with(
                "/servicedesk/1/customer",
                json={"accountIds": ["id1"]},
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskRemoveCustomersTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_remove_customers"


# --------------------------------------------------------------------------- #
# ServiceDeskGetOrganisationsTool
# --------------------------------------------------------------------------- #


class TestServiceDeskGetOrganisationsTool:
    """Tests for servicedesk_get_organisations tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_service_desk_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetOrganisationsTool, jsm_client)
            result = await tool.safe_execute({})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_list_organisations(self, jsm_client: AsyncMock) -> None:
            """Lists organisations for a service desk."""
            orgs = [{"id": "1", "name": "ACME Corporation"}]
            jsm_client.list_paginated.return_value = _paginated_response(
                orgs, total=1
            )
            tool = _make_tool(ServiceDeskGetOrganisationsTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})

            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["name"] == "ACME Corporation"
            jsm_client.list_paginated.assert_called_once_with(
                "/servicedesk/1/organization", start=0, limit=50
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskGetOrganisationsTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_get_organisations"


# --------------------------------------------------------------------------- #
# ServiceDeskAddOrganisationTool
# --------------------------------------------------------------------------- #


class TestServiceDeskAddOrganisationTool:
    """Tests for servicedesk_add_organisation tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_organisation_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskAddOrganisationTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False

        @pytest.mark.asyncio
        async def test_invalid_organisation_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskAddOrganisationTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "organisation_id": -1}
            )
            assert result.success is False
            assert result.error["type"] == "VALIDATION_ERROR"

    class TestExecution:
        @pytest.mark.asyncio
        async def test_add_organisation(self, jsm_client: AsyncMock) -> None:
            """Adds an organisation to a service desk."""
            jsm_client.post.return_value = {}
            tool = _make_tool(ServiceDeskAddOrganisationTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "organisation_id": 5}
            )

            assert result.success is True
            assert result.data["added"] is True
            assert result.data["organisation_id"] == 5
            jsm_client.post.assert_called_once_with(
                "/servicedesk/1/organization",
                json={"organizationId": 5},
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskAddOrganisationTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_add_organisation"


# --------------------------------------------------------------------------- #
# ServiceDeskRemoveOrganisationTool
# --------------------------------------------------------------------------- #


class TestServiceDeskRemoveOrganisationTool:
    """Tests for servicedesk_remove_organisation tool."""

    class TestValidation:
        @pytest.mark.asyncio
        async def test_missing_organisation_id(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskRemoveOrganisationTool, jsm_client)
            result = await tool.safe_execute({"service_desk_id": 1})
            assert result.success is False

    class TestExecution:
        @pytest.mark.asyncio
        async def test_remove_organisation(self, jsm_client: AsyncMock) -> None:
            """Removes an organisation from a service desk."""
            jsm_client.delete.return_value = None
            tool = _make_tool(ServiceDeskRemoveOrganisationTool, jsm_client)
            result = await tool.safe_execute(
                {"service_desk_id": 1, "organisation_id": 5}
            )

            assert result.success is True
            assert result.data["removed"] is True
            jsm_client.delete.assert_called_once_with(
                "/servicedesk/1/organization",
                json={"organizationId": 5},
            )

    class TestGuide:
        def test_guide_metadata(self, jsm_client: AsyncMock) -> None:
            tool = _make_tool(ServiceDeskRemoveOrganisationTool, jsm_client)
            guide = tool.get_guide()
            assert guide.name == "servicedesk_remove_organisation"


# --------------------------------------------------------------------------- #
# Registry Integration
# --------------------------------------------------------------------------- #


class TestServiceDeskToolRegistration:
    """Tests for service desk tool auto-discovery."""

    def test_all_servicedesk_tools_discovered(
        self, tool_registry: Any
    ) -> None:
        """All 10 service desk tools are discovered by the registry."""
        expected = {
            "servicedesk_list",
            "servicedesk_get",
            "servicedesk_get_queues",
            "servicedesk_get_queue_issues",
            "servicedesk_get_customers",
            "servicedesk_add_customers",
            "servicedesk_remove_customers",
            "servicedesk_get_organisations",
            "servicedesk_add_organisation",
            "servicedesk_remove_organisation",
        }
        for name in expected:
            assert tool_registry.get_tool(name) is not None, f"Tool {name} not found"

    def test_tool_count_includes_servicedesk(
        self, tool_registry: Any
    ) -> None:
        """Total tool count includes service desk tools."""
        # meta (2) + issues (7) + servicedesk (10) = 19
        assert tool_registry.tool_count == 47
