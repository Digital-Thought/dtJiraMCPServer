"""Tests for AtlassianClient, PlatformClient, and JsmClient."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from dtjiramcpserver.client.base import AtlassianClient
from dtjiramcpserver.client.jsm import JsmClient
from dtjiramcpserver.client.platform import PlatformClient
from dtjiramcpserver.config.models import JiraConfig
from dtjiramcpserver.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    ServerError,
)


# ---------------------------------------------------------------------------
# AtlassianClient
# ---------------------------------------------------------------------------


class TestAtlassianClientLifecycle:
    """Tests for connect / disconnect lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self) -> None:
        """connect() creates an httpx.AsyncClient."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        await client.connect()
        assert client._client is not None
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_clears_client(self) -> None:
        """disconnect() sets _client to None."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        await client.connect()
        await client.disconnect()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_disconnect_noop_when_not_connected(self) -> None:
        """disconnect() is safe to call when not connected."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        await client.disconnect()  # Should not raise

    def test_base_url_property(self) -> None:
        """base_url property returns the normalised URL."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3/",
            email="user@example.com",
            api_token="tok",
        )
        assert client.base_url == "https://test.atlassian.net/rest/api/3"


class TestAtlassianClientExecute:
    """Tests for HTTP method routing through _execute."""

    @pytest.fixture
    def mock_response(self) -> MagicMock:
        """Create a mock httpx.Response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"ok": true}'
        response.json.return_value = {"ok": True}
        response.headers = {}
        return response

    @pytest.fixture
    def connected_client(self, mock_response: MagicMock) -> AtlassianClient:
        """Create an AtlassianClient with a mocked httpx client."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)
        client._client = mock_httpx
        # Bypass rate limiter - execute directly
        client._rate_limiter.execute_with_retry = AsyncMock(return_value=mock_response)
        return client

    @pytest.mark.asyncio
    async def test_get_returns_json(self, connected_client: AtlassianClient) -> None:
        """GET request returns parsed JSON."""
        result = await connected_client.get("/search")
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_post_returns_json(self, connected_client: AtlassianClient) -> None:
        """POST request returns parsed JSON."""
        result = await connected_client.post("/issues", json={"summary": "test"})
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_put_returns_json(self, connected_client: AtlassianClient) -> None:
        """PUT request returns parsed JSON."""
        result = await connected_client.put("/issues/PROJ-1", json={"summary": "updated"})
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_delete_returns_none_for_204(self, connected_client: AtlassianClient) -> None:
        """DELETE returns None for 204 No Content."""
        connected_client._rate_limiter.execute_with_retry.return_value.status_code = 204
        result = await connected_client.delete("/issues/PROJ-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_not_connected_raises(self) -> None:
        """Calling HTTP methods without connect() raises NetworkError."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        with pytest.raises(NetworkError, match="not connected"):
            await client.get("/test")

    @pytest.mark.asyncio
    async def test_empty_response_returns_empty_dict(
        self, connected_client: AtlassianClient
    ) -> None:
        """Empty response body returns empty dict."""
        connected_client._rate_limiter.execute_with_retry.return_value.content = b""
        result = await connected_client.get("/empty")
        assert result == {}


class TestAtlassianClientErrorHandling:
    """Tests for HTTP error classification in _execute."""

    @pytest.fixture
    def error_client(self) -> AtlassianClient:
        """Create an AtlassianClient with a mocked rate limiter."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_404_raises_not_found(self, error_client: AtlassianClient) -> None:
        """HTTP 404 raises NotFoundError."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        response.json.return_value = {"errorMessages": ["Issue not found"]}
        response.headers = {}
        error_client._rate_limiter.execute_with_retry = AsyncMock(return_value=response)

        with pytest.raises(NotFoundError, match="Issue not found"):
            await error_client.get("/issues/NOPE-1")

    @pytest.mark.asyncio
    async def test_500_raises_server_error(self, error_client: AtlassianClient) -> None:
        """HTTP 500 raises ServerError."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 500
        response.json.return_value = {"message": "Internal error"}
        response.headers = {}
        error_client._rate_limiter.execute_with_retry = AsyncMock(return_value=response)

        with pytest.raises(ServerError):
            await error_client.get("/broken")

    @pytest.mark.asyncio
    async def test_connect_error_raises_network_error(
        self, error_client: AtlassianClient
    ) -> None:
        """httpx.ConnectError is wrapped in NetworkError."""
        error_client._rate_limiter.execute_with_retry = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(NetworkError, match="Connection failed"):
            await error_client.get("/test")

    @pytest.mark.asyncio
    async def test_timeout_raises_network_error(
        self, error_client: AtlassianClient
    ) -> None:
        """httpx.TimeoutException is wrapped in NetworkError."""
        error_client._rate_limiter.execute_with_retry = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with pytest.raises(NetworkError, match="timed out"):
            await error_client.get("/slow")


class TestValidateCredentials:
    """Tests for credential validation."""

    @pytest.mark.asyncio
    async def test_valid_credentials(self) -> None:
        """Successful /myself call returns user info."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {
            "displayName": "Test User",
            "emailAddress": "user@example.com",
        }
        mock_httpx.get = AsyncMock(return_value=response)
        client._client = mock_httpx

        result = await client.validate_credentials()
        assert result["displayName"] == "Test User"

    @pytest.mark.asyncio
    async def test_invalid_credentials_raises(self) -> None:
        """HTTP 401 from /myself raises AuthenticationError."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="bad-token",
        )
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_httpx.get = AsyncMock(return_value=response)
        client._client = mock_httpx

        with pytest.raises(AuthenticationError):
            await client.validate_credentials()

    @pytest.mark.asyncio
    async def test_not_connected_raises(self) -> None:
        """validate_credentials without connect() raises NetworkError."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        with pytest.raises(NetworkError, match="not connected"):
            await client.validate_credentials()

    @pytest.mark.asyncio
    async def test_strips_api_path_for_myself_call(self) -> None:
        """validate_credentials calls /rest/api/3/myself relative to instance URL."""
        client = AtlassianClient(
            base_url="https://test.atlassian.net/rest/api/3",
            email="user@example.com",
            api_token="tok",
        )
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"displayName": "User"}
        mock_httpx.get = AsyncMock(return_value=response)
        client._client = mock_httpx

        await client.validate_credentials()

        # Verify the URL used for the /myself call
        call_args = mock_httpx.get.call_args
        url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert url == "https://test.atlassian.net/rest/api/3/myself"


# ---------------------------------------------------------------------------
# PlatformClient
# ---------------------------------------------------------------------------


class TestPlatformClient:
    """Tests for PlatformClient."""

    def test_base_url_constructed(self, sample_jira_config: JiraConfig) -> None:
        """PlatformClient constructs the correct base URL."""
        client = PlatformClient(sample_jira_config)
        assert client.base_url == "https://test.atlassian.net/rest/api/3"

    @pytest.mark.asyncio
    async def test_list_paginated(self, sample_jira_config: JiraConfig) -> None:
        """list_paginated sends correct params and parses response."""
        client = PlatformClient(sample_jira_config)
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.content = b"data"
        response.json.return_value = {
            "startAt": 0,
            "maxResults": 10,
            "total": 2,
            "issues": [{"key": "PROJ-1"}, {"key": "PROJ-2"}],
        }
        response.headers = {}
        client._client = mock_httpx
        client._rate_limiter.execute_with_retry = AsyncMock(return_value=response)

        result = await client.list_paginated("/search", start=0, limit=10)

        assert len(result.results) == 2
        assert result.total == 2
        assert result.has_more is False


# ---------------------------------------------------------------------------
# JsmClient
# ---------------------------------------------------------------------------


class TestJsmClient:
    """Tests for JsmClient."""

    def test_base_url_constructed(self, sample_jira_config: JiraConfig) -> None:
        """JsmClient constructs the correct base URL."""
        client = JsmClient(sample_jira_config)
        assert client.base_url == "https://test.atlassian.net/rest/servicedeskapi"

    @pytest.mark.asyncio
    async def test_connect_adds_experimental_header(
        self, sample_jira_config: JiraConfig
    ) -> None:
        """connect() adds the X-ExperimentalApi header."""
        client = JsmClient(sample_jira_config)
        await client.connect()
        assert client._client is not None
        assert client._client.headers.get("X-ExperimentalApi") == "opt-in"
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_list_paginated(self, sample_jira_config: JiraConfig) -> None:
        """list_paginated sends correct JSM-style params and parses response."""
        client = JsmClient(sample_jira_config)
        mock_httpx = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.content = b"data"
        response.json.return_value = {
            "start": 0,
            "limit": 10,
            "size": 3,
            "isLastPage": True,
            "values": [{"id": 1}, {"id": 2}, {"id": 3}],
        }
        response.headers = {}
        client._client = mock_httpx
        client._rate_limiter.execute_with_retry = AsyncMock(return_value=response)

        result = await client.list_paginated("/servicedesk", start=0, limit=10)

        assert len(result.results) == 3
        assert result.has_more is False
