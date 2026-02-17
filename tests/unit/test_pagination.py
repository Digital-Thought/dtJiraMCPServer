"""Tests for pagination handler."""

from __future__ import annotations

from dtjiramcpserver.client.pagination import PaginationHandler


class TestPlatformPagination:
    """Tests for Jira Platform API pagination parsing."""

    def test_standard_response(self) -> None:
        """Parse normal paginated response with issues."""
        response = {
            "startAt": 0,
            "maxResults": 50,
            "total": 100,
            "issues": [{"key": f"PROJ-{i}"} for i in range(50)],
        }
        result = PaginationHandler.parse_platform_response(response, 0, 50)

        assert result.start == 0
        assert result.limit == 50
        assert result.total == 100
        assert result.has_more is True
        assert len(result.results) == 50

    def test_last_page(self) -> None:
        """Last page has has_more=False."""
        response = {
            "startAt": 50,
            "maxResults": 50,
            "total": 75,
            "issues": [{"key": f"PROJ-{i}"} for i in range(25)],
        }
        result = PaginationHandler.parse_platform_response(response, 50, 50)

        assert result.has_more is False
        assert len(result.results) == 25

    def test_empty_results(self) -> None:
        """Empty result set returns zero results."""
        response = {"startAt": 0, "maxResults": 50, "total": 0, "issues": []}
        result = PaginationHandler.parse_platform_response(response, 0, 50)

        assert result.total == 0
        assert result.has_more is False
        assert len(result.results) == 0

    def test_values_key(self) -> None:
        """Parse response using 'values' key instead of 'issues'."""
        response = {
            "startAt": 0,
            "maxResults": 10,
            "total": 5,
            "values": [{"id": i} for i in range(5)],
        }
        result = PaginationHandler.parse_platform_response(response, 0, 10)

        assert len(result.results) == 5
        assert result.has_more is False


class TestJsmPagination:
    """Tests for JSM API pagination parsing."""

    def test_standard_response(self) -> None:
        """Parse normal JSM paginated response."""
        response = {
            "start": 0,
            "limit": 50,
            "size": 50,
            "isLastPage": False,
            "values": [{"id": i} for i in range(50)],
        }
        result = PaginationHandler.parse_jsm_response(response, 0, 50)

        assert result.start == 0
        assert result.limit == 50
        assert result.has_more is True
        assert len(result.results) == 50

    def test_last_page(self) -> None:
        """Last page identified by isLastPage flag."""
        response = {
            "start": 50,
            "limit": 50,
            "size": 10,
            "isLastPage": True,
            "values": [{"id": i} for i in range(10)],
        }
        result = PaginationHandler.parse_jsm_response(response, 50, 50)

        assert result.has_more is False
        assert result.total == 60  # start + size

    def test_total_provided(self) -> None:
        """Use explicit total when provided."""
        response = {
            "start": 0,
            "limit": 10,
            "size": 10,
            "total": 42,
            "isLastPage": False,
            "values": [{"id": i} for i in range(10)],
        }
        result = PaginationHandler.parse_jsm_response(response, 0, 10)

        assert result.total == 42

    def test_empty_results(self) -> None:
        """Empty JSM result set."""
        response = {
            "start": 0,
            "limit": 50,
            "size": 0,
            "isLastPage": True,
            "values": [],
        }
        result = PaginationHandler.parse_jsm_response(response, 0, 50)

        assert result.total == 0
        assert result.has_more is False
        assert len(result.results) == 0
