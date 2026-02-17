"""Tests for error classification and mapping."""

from __future__ import annotations

from dtjiramcpserver.client.errors import ErrorCategory, classify_http_error
from dtjiramcpserver.exceptions import (
    AtlassianAPIError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ServerError,
)


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_defined(self) -> None:
        """All expected error categories are defined."""
        expected = {
            "VALIDATION_ERROR",
            "AUTHENTICATION_ERROR",
            "PERMISSION_ERROR",
            "NOT_FOUND",
            "CONFLICT",
            "RATE_LIMITED",
            "SERVER_ERROR",
            "NETWORK_ERROR",
        }
        actual = {e.value for e in ErrorCategory}
        assert actual == expected


class TestClassifyHttpError:
    """Tests for classify_http_error function."""

    def test_400_returns_validation_error(self) -> None:
        """HTTP 400 maps to VALIDATION_ERROR."""
        err = classify_http_error(400, {"errorMessages": ["Invalid field"]})
        assert isinstance(err, AtlassianAPIError)
        assert err.category == "VALIDATION_ERROR"
        assert "Invalid field" in err.message

    def test_401_returns_authentication_error(self) -> None:
        """HTTP 401 maps to AuthenticationError."""
        err = classify_http_error(401)
        assert isinstance(err, AuthenticationError)
        assert err.category == "AUTHENTICATION_ERROR"
        assert err.status_code == 401

    def test_403_returns_permission_error(self) -> None:
        """HTTP 403 maps to PermissionError."""
        err = classify_http_error(403)
        assert isinstance(err, PermissionError)
        assert err.category == "PERMISSION_ERROR"
        assert err.status_code == 403

    def test_404_returns_not_found(self) -> None:
        """HTTP 404 maps to NotFoundError."""
        err = classify_http_error(404)
        assert isinstance(err, NotFoundError)
        assert err.category == "NOT_FOUND"
        assert err.status_code == 404

    def test_409_returns_conflict(self) -> None:
        """HTTP 409 maps to ConflictError."""
        err = classify_http_error(409)
        assert isinstance(err, ConflictError)
        assert err.category == "CONFLICT"
        assert err.status_code == 409

    def test_429_returns_rate_limit(self) -> None:
        """HTTP 429 maps to RateLimitError."""
        err = classify_http_error(429, retry_after=10.0)
        assert isinstance(err, RateLimitError)
        assert err.category == "RATE_LIMITED"
        assert err.retry_after == 10.0

    def test_500_returns_server_error(self) -> None:
        """HTTP 500 maps to ServerError."""
        err = classify_http_error(500)
        assert isinstance(err, ServerError)
        assert err.category == "SERVER_ERROR"
        assert err.status_code == 500

    def test_502_returns_server_error(self) -> None:
        """HTTP 502 maps to ServerError."""
        err = classify_http_error(502)
        assert isinstance(err, ServerError)
        assert err.status_code == 502

    def test_503_returns_server_error(self) -> None:
        """HTTP 503 maps to ServerError."""
        err = classify_http_error(503)
        assert isinstance(err, ServerError)
        assert err.status_code == 503

    def test_extracts_error_messages_array(self) -> None:
        """Error message extracted from errorMessages array."""
        err = classify_http_error(400, {"errorMessages": ["Error 1", "Error 2"]})
        assert "Error 1" in err.message
        assert "Error 2" in err.message

    def test_extracts_message_field(self) -> None:
        """Error message extracted from message field."""
        err = classify_http_error(400, {"message": "Something went wrong"})
        assert err.message == "Something went wrong"

    def test_extracts_field_errors(self) -> None:
        """Error message extracted from errors dict."""
        err = classify_http_error(400, {"errors": {"summary": "Required field"}})
        assert "summary" in err.message
        assert "Required field" in err.message

    def test_no_response_body_uses_default(self) -> None:
        """Default message used when no response body available."""
        err = classify_http_error(404)
        assert "not found" in err.message.lower()

    def test_unknown_status_code(self) -> None:
        """Unknown status code creates generic error."""
        err = classify_http_error(418)
        assert isinstance(err, AtlassianAPIError)
        assert err.category == "UNKNOWN_ERROR"
        assert "418" in err.message

    def test_details_preserved(self) -> None:
        """Response body is preserved as error details."""
        body = {"errorMessages": ["Test"], "extra": "data"}
        err = classify_http_error(400, body)
        assert err.details == body
