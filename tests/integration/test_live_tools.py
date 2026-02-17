"""Integration tests against a live Jira Cloud instance.

These tests perform read-only operations to verify API compatibility.
Skipped automatically when credentials are not set.

Run with:
    export JIRA_INSTANCE_URL=https://your-domain.atlassian.net
    export JIRA_USER_EMAIL=user@example.com
    export JIRA_API_TOKEN=your-api-token
    pytest tests/integration/ -v
"""

from __future__ import annotations

import os

import pytest

# Skip entire module if credentials not set
pytestmark = pytest.mark.skipif(
    not all(
        os.environ.get(k)
        for k in ("JIRA_INSTANCE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN")
    ),
    reason="Jira credentials not set in environment",
)


def _make_config():
    """Build JiraConfig from environment variables."""
    from dtjiramcpserver.config.models import JiraConfig

    return JiraConfig(
        instance_url=os.environ["JIRA_INSTANCE_URL"],
        user_email=os.environ["JIRA_USER_EMAIL"],
        api_token=os.environ["JIRA_API_TOKEN"],
    )


class TestPlatformAPIIntegration:
    """Read-only tests against Jira Platform REST API v3."""

    @pytest.mark.asyncio
    async def test_field_list(self) -> None:
        """field_list returns fields from the live API."""
        from dtjiramcpserver.client.platform import PlatformClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.fields.custom_fields import FieldListTool

        client = PlatformClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = FieldListTool(platform_client=client)
            result = await tool.safe_execute({})

            assert result.success is True
            assert len(result.data) > 0
            field_ids = {f["id"] for f in result.data}
            assert "summary" in field_ids
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_workflow_list(self) -> None:
        """workflow_list returns workflows from the live API."""
        from dtjiramcpserver.client.platform import PlatformClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.workflows.workflows import WorkflowListTool

        client = PlatformClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = WorkflowListTool(platform_client=client)
            result = await tool.safe_execute({"limit": 5})

            assert result.success is True
            assert result.pagination["total"] > 0
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_status_list(self) -> None:
        """status_list returns statuses from the live API."""
        from dtjiramcpserver.client.platform import PlatformClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.workflows.statuses import StatusListTool

        client = PlatformClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = StatusListTool(platform_client=client)
            result = await tool.safe_execute({"limit": 5})

            assert result.success is True
            assert result.pagination["total"] > 0
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_screen_list(self) -> None:
        """screen_list returns screens from the live API."""
        from dtjiramcpserver.client.platform import PlatformClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.fields.screens import ScreenListTool

        client = PlatformClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = ScreenListTool(platform_client=client)
            result = await tool.safe_execute({"limit": 5})

            assert result.success is True
            assert result.pagination["total"] > 0
        finally:
            await client.disconnect()


class TestJSMAPIIntegration:
    """Read-only tests against JSM REST API."""

    @pytest.mark.asyncio
    async def test_servicedesk_list(self) -> None:
        """servicedesk_list returns desks from the live API."""
        from dtjiramcpserver.client.jsm import JsmClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.servicedesk.desks import ServiceDeskListTool

        client = JsmClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = ServiceDeskListTool(jsm_client=client)
            result = await tool.safe_execute({"limit": 5})

            assert result.success is True
            assert result.pagination["total"] > 0
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_assets_get_workspaces(self) -> None:
        """assets_get_workspaces returns data from the live API."""
        from dtjiramcpserver.client.jsm import JsmClient
        from dtjiramcpserver.client.rate_limiter import RateLimiter
        from dtjiramcpserver.tools.assets.workspaces import AssetsGetWorkspacesTool

        client = JsmClient(config=_make_config(), rate_limiter=RateLimiter())
        await client.connect()
        try:
            tool = AssetsGetWorkspacesTool(jsm_client=client)
            result = await tool.safe_execute({})

            assert result.success is True
        finally:
            await client.disconnect()
