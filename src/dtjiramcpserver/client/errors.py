"""Error classification for Atlassian API responses.

Maps HTTP status codes to structured exception types defined in
the exceptions module (AD-003).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from dtjiramcpserver.exceptions import (
    AtlassianAPIError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ServerError,
)


class ErrorCategory(str, Enum):
    """Error categories matching architecture specification AD-003."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"


def _extract_error_message(response_body: dict[str, Any] | None) -> str | None:
    """Extract the human-readable error message from an Atlassian API response.

    Atlassian APIs return error messages in various formats:
        {"errorMessages": ["message"]}
        {"message": "message"}
        {"errors": {"field": "message"}}
    """
    if not response_body:
        return None

    # Standard errorMessages array
    error_messages = response_body.get("errorMessages")
    if error_messages and isinstance(error_messages, list):
        return "; ".join(str(m) for m in error_messages if m)

    # Simple message field
    message = response_body.get("message")
    if message:
        return str(message)

    # Field-level errors
    errors = response_body.get("errors")
    if errors and isinstance(errors, dict):
        return "; ".join(f"{k}: {v}" for k, v in errors.items())

    return None


def classify_http_error(
    status_code: int,
    response_body: dict[str, Any] | None = None,
    retry_after: float | None = None,
) -> AtlassianAPIError:
    """Map an HTTP status code to the appropriate exception class.

    Args:
        status_code: HTTP response status code.
        response_body: Parsed JSON response body, if available.
        retry_after: Retry-After header value in seconds, for 429 responses.

    Returns:
        An appropriate AtlassianAPIError subclass instance.
    """
    detail_msg = _extract_error_message(response_body)
    details = response_body if response_body else None

    if status_code == 400:
        return AtlassianAPIError(
            category=ErrorCategory.VALIDATION_ERROR.value,
            message=detail_msg or "Bad request - invalid parameters.",
            details=details,
            status_code=400,
        )

    if status_code == 401:
        return AuthenticationError(
            message=detail_msg or "Authentication failed. Check JIRA_USER_EMAIL and JIRA_API_TOKEN.",
            details=details,
        )

    if status_code == 403:
        return PermissionError(
            message=detail_msg or "Insufficient permissions for this operation.",
            details=details,
        )

    if status_code == 404:
        return NotFoundError(
            message=detail_msg or "The requested resource was not found.",
            details=details,
        )

    if status_code == 409:
        return ConflictError(
            message=detail_msg or "Resource conflict.",
            details=details,
        )

    if status_code == 429:
        return RateLimitError(
            message=detail_msg or "Rate limited by Atlassian API.",
            details=details,
            retry_after=retry_after,
        )

    if 500 <= status_code < 600:
        return ServerError(
            message=detail_msg or f"Atlassian server error (HTTP {status_code}).",
            details=details,
            status_code=status_code,
        )

    # Unrecognised status code
    return AtlassianAPIError(
        category="UNKNOWN_ERROR",
        message=detail_msg or f"Unexpected HTTP {status_code} response.",
        details=details,
        status_code=status_code,
    )
