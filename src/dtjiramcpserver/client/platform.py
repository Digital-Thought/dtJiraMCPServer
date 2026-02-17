"""Jira Cloud Platform REST API v3 client.

Base URL: {instance}/rest/api/3/
Pagination: startAt/maxResults/total
"""

from __future__ import annotations

from typing import Any

from dtjiramcpserver.client.base import AtlassianClient
from dtjiramcpserver.client.pagination import PaginatedResponse, PaginationHandler
from dtjiramcpserver.client.rate_limiter import RateLimiter
from dtjiramcpserver.config.models import JiraConfig


class PlatformClient(AtlassianClient):
    """Client for Jira Cloud Platform REST API v3.

    Extends the base AtlassianClient with convenience methods
    for paginated list operations using Platform API conventions.
    """

    def __init__(
        self,
        config: JiraConfig,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(
            base_url=f"{config.instance_url}/rest/api/3",
            email=config.user_email,
            api_token=config.api_token,
            rate_limiter=rate_limiter,
        )

    async def list_paginated(
        self,
        path: str,
        start: int = 0,
        limit: int = 50,
        extra_params: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """Execute a paginated GET using Jira Platform API conventions.

        Platform API uses startAt/maxResults parameters.

        Args:
            path: API endpoint path.
            start: Starting index for pagination.
            limit: Maximum number of results per page.
            extra_params: Additional query parameters.

        Returns:
            PaginatedResponse with normalised pagination metadata.
        """
        params: dict[str, Any] = {"startAt": start, "maxResults": limit}
        if extra_params:
            params.update(extra_params)

        response = await self.get(path, params=params)
        return PaginationHandler.parse_platform_response(response, start, limit)
