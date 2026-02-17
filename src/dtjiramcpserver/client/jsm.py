"""Jira Service Management REST API client.

Base URL: {instance}/rest/servicedeskapi/
Pagination: start/limit/size/isLastPage
Headers: X-ExperimentalApi: opt-in (for experimental endpoints)
"""

from __future__ import annotations

from typing import Any

from dtjiramcpserver.client.base import AtlassianClient
from dtjiramcpserver.client.pagination import PaginatedResponse, PaginationHandler
from dtjiramcpserver.client.rate_limiter import RateLimiter
from dtjiramcpserver.config.models import JiraConfig


class JsmClient(AtlassianClient):
    """Client for Jira Service Management REST API.

    Extends the base AtlassianClient with JSM-specific pagination
    and the X-ExperimentalApi header required for some endpoints.
    """

    def __init__(
        self,
        config: JiraConfig,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(
            base_url=f"{config.instance_url}/rest/servicedeskapi",
            email=config.user_email,
            api_token=config.api_token,
            rate_limiter=rate_limiter,
        )

    async def connect(self) -> None:
        """Create the httpx client with the X-ExperimentalApi header."""
        await super().connect()
        if self._client:
            self._client.headers["X-ExperimentalApi"] = "opt-in"

    async def list_paginated(
        self,
        path: str,
        start: int = 0,
        limit: int = 50,
        extra_params: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """Execute a paginated GET using JSM API conventions.

        JSM API uses start/limit parameters.

        Args:
            path: API endpoint path.
            start: Starting index for pagination.
            limit: Maximum number of results per page.
            extra_params: Additional query parameters.

        Returns:
            PaginatedResponse with normalised pagination metadata.
        """
        params: dict[str, Any] = {"start": start, "limit": limit}
        if extra_params:
            params.update(extra_params)

        response = await self.get(path, params=params)
        return PaginationHandler.parse_jsm_response(response, start, limit)
