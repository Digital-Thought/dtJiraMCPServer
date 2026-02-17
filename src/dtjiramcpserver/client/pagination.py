"""Pagination handling for Atlassian API responses.

Normalises the two different pagination conventions used by the
Jira Platform API (startAt/maxResults/total) and the JSM API
(start/limit/size/isLastPage) into a consistent PaginatedResponse model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """Standardised pagination metadata returned by all list operations."""

    results: list[Any]
    start: int
    limit: int
    total: int
    has_more: bool


class PaginationHandler:
    """Handles the two different Atlassian API pagination styles."""

    @staticmethod
    def parse_platform_response(
        response: dict[str, Any],
        start: int,
        limit: int,
    ) -> PaginatedResponse:
        """Parse Jira Platform API pagination.

        Platform API responses use:
            startAt: starting index
            maxResults: page size
            total: total number of results
            issues/values: the result list
        """
        total = response.get("total", 0)
        actual_start = response.get("startAt", start)
        actual_limit = response.get("maxResults", limit)

        # Results can be in 'issues', 'values', or other keys
        results = (
            response.get("issues")
            or response.get("values")
            or response.get("results")
            or []
        )

        has_more = (actual_start + len(results)) < total

        return PaginatedResponse(
            results=results,
            start=actual_start,
            limit=actual_limit,
            total=total,
            has_more=has_more,
        )

    @staticmethod
    def parse_jsm_response(
        response: dict[str, Any],
        start: int,
        limit: int,
    ) -> PaginatedResponse:
        """Parse JSM REST API pagination.

        JSM API responses use:
            start: starting index
            limit: page size
            size: number of results in this page
            isLastPage: boolean indicating if this is the last page
            values: the result list
        """
        values = response.get("values", [])
        actual_start = response.get("start", start)
        actual_limit = response.get("limit", limit)
        size = response.get("size", len(values))
        is_last_page = response.get("isLastPage", True)

        # JSM does not always provide a total count; estimate if missing
        if "total" in response:
            total = response["total"]
        elif is_last_page:
            total = actual_start + size
        else:
            # Unknown total; indicate there are more results
            total = actual_start + size + 1

        has_more = not is_last_page

        return PaginatedResponse(
            results=values,
            start=actual_start,
            limit=actual_limit,
            total=total,
            has_more=has_more,
        )
