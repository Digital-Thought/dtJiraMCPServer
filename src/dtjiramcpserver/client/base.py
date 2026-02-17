"""Base HTTP client for Atlassian Cloud REST APIs.

Handles authentication, rate limiting, error classification,
and credential redaction from logs. All Jira and JSM API
communication flows through this class.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from dtjiramcpserver.client.errors import classify_http_error
from dtjiramcpserver.client.rate_limiter import RateLimiter
from dtjiramcpserver.exceptions import (
    AuthenticationError,
    NetworkError,
)

logger = logging.getLogger(__name__)


class AtlassianClient:
    """Base HTTP client for Atlassian Cloud REST APIs.

    Provides authenticated HTTP methods with automatic retry
    on rate limits and server errors, plus structured error
    classification.
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._api_token = api_token
        self._rate_limiter = rate_limiter or RateLimiter()
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        """Return the base URL for this client."""
        return self._base_url

    async def connect(self) -> None:
        """Create the httpx.AsyncClient with authentication headers."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            auth=httpx.BasicAuth(username=self._email, password=self._api_token),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0),
        )
        logger.info("HTTP client connected to %s", self._base_url)

    async def validate_credentials(self) -> dict[str, Any]:
        """Validate credentials by calling GET /rest/api/3/myself.

        Returns:
            User information from the Atlassian API.

        Raises:
            AuthenticationError: If credentials are invalid.
            NetworkError: If the connection fails.
        """
        try:
            # Use the instance URL (not the API base URL) for /myself
            instance_url = self._base_url
            # Strip the API path suffix to get the instance base
            for suffix in ("/rest/api/3", "/rest/servicedeskapi"):
                if instance_url.endswith(suffix):
                    instance_url = instance_url[: -len(suffix)]
                    break

            if self._client is None:
                raise NetworkError("Client not connected. Call connect() first.")

            response = await self._client.get(
                f"{instance_url}/rest/api/3/myself",
            )

            if response.status_code == 401:
                raise AuthenticationError()

            response.raise_for_status()
            return response.json()

        except httpx.ConnectError as exc:
            raise NetworkError(f"Failed to connect to {self._base_url}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise NetworkError(f"Connection timed out: {exc}") from exc

    async def disconnect(self) -> None:
        """Close the httpx client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client disconnected from %s", self._base_url)

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GET request with retry and error handling.

        Args:
            path: API endpoint path (relative to base URL).
            params: Optional query parameters.

        Returns:
            Parsed JSON response body.
        """
        return await self._execute("GET", path, params=params)

    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a POST request with retry and error handling.

        Args:
            path: API endpoint path (relative to base URL).
            json: Optional JSON request body.

        Returns:
            Parsed JSON response body.
        """
        return await self._execute("POST", path, json=json)

    async def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a PUT request with retry and error handling.

        Args:
            path: API endpoint path (relative to base URL).
            json: Optional JSON request body.

        Returns:
            Parsed JSON response body.
        """
        return await self._execute("PUT", path, json=json)

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a DELETE request with retry and error handling.

        Args:
            path: API endpoint path (relative to base URL).
            params: Optional query parameters.
            json: Optional JSON request body (used by some JSM endpoints).

        Returns:
            Parsed JSON response body, or None for 204 responses.
        """
        return await self._execute("DELETE", path, params=params, json=json, allow_empty=True)

    async def _execute(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        allow_empty: bool = False,
    ) -> Any:
        """Execute an HTTP request through the rate limiter with error classification.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API endpoint path.
            params: Optional query parameters.
            json: Optional JSON request body.
            allow_empty: If True, return None for 204 responses.

        Returns:
            Parsed JSON response body, or None if allow_empty and 204.

        Raises:
            AtlassianAPIError: For classified HTTP errors.
            NetworkError: For connection or timeout errors.
        """
        if self._client is None:
            raise NetworkError("Client not connected. Call connect() first.")

        logger.debug(
            "%s %s params=%s",
            method,
            path,
            params,
        )

        try:
            response = await self._rate_limiter.execute_with_retry(
                self._client.request,
                method,
                path,
                params=params,
                json=json,
            )
        except httpx.ConnectError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise NetworkError(f"Request timed out: {exc}") from exc

        # Handle successful responses
        if response.status_code < 400:
            if response.status_code == 204 and allow_empty:
                return None
            if not response.content:
                return {}
            return response.json()

        # Classify error response
        response_body: dict[str, Any] | None = None
        try:
            response_body = response.json()
        except Exception:
            pass

        retry_after: float | None = None
        retry_after_header = response.headers.get("Retry-After")
        if retry_after_header:
            try:
                retry_after = float(retry_after_header)
            except ValueError:
                pass

        raise classify_http_error(
            status_code=response.status_code,
            response_body=response_body,
            retry_after=retry_after,
        )
