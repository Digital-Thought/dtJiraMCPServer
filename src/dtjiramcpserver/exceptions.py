"""Custom exception hierarchy for dtJiraMCPServer.

Each exception maps to an error category defined in the architecture
specification (AD-003). The hierarchy enables structured, LLM-friendly
error responses throughout the tool framework.
"""

from __future__ import annotations

from typing import Any


class JiraMCPError(Exception):
    """Base exception for all dtJiraMCPServer errors."""


class ConfigurationError(JiraMCPError):
    """Raised when application configuration is invalid or missing."""


class InputValidationError(JiraMCPError):
    """Raised when tool input parameters fail local validation.

    Carries the field name and reason to enable structured error responses.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.reason = reason


class ToolNotFoundError(JiraMCPError):
    """Raised when a requested tool does not exist in the registry."""


class NetworkError(JiraMCPError):
    """Raised on connection or timeout errors communicating with Atlassian."""


class AtlassianAPIError(JiraMCPError):
    """Base exception for all Atlassian REST API errors.

    Carries structured information for LLM-friendly error responses.

    Attributes:
        category: Error category string (e.g. AUTHENTICATION_ERROR).
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
        status_code: HTTP status code from the Atlassian response.
    """

    def __init__(
        self,
        category: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.details = details
        self.status_code = status_code


class AuthenticationError(AtlassianAPIError):
    """HTTP 401 - Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed. Check JIRA_USER_EMAIL and JIRA_API_TOKEN.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            category="AUTHENTICATION_ERROR",
            message=message,
            details=details,
            status_code=401,
        )


class PermissionError(AtlassianAPIError):
    """HTTP 403 - Insufficient permissions for the requested operation."""

    def __init__(
        self,
        message: str = "Insufficient permissions for this operation.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            category="PERMISSION_ERROR",
            message=message,
            details=details,
            status_code=403,
        )


class NotFoundError(AtlassianAPIError):
    """HTTP 404 - Requested resource was not found."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            category="NOT_FOUND",
            message=message,
            details=details,
            status_code=404,
        )


class ConflictError(AtlassianAPIError):
    """HTTP 409 - Resource conflict (e.g. duplicate name)."""

    def __init__(
        self,
        message: str = "Resource conflict.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            category="CONFLICT",
            message=message,
            details=details,
            status_code=409,
        )


class RateLimitError(AtlassianAPIError):
    """HTTP 429 - Rate limited by Atlassian. Handled internally with retry."""

    def __init__(
        self,
        message: str = "Rate limited by Atlassian API.",
        details: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            category="RATE_LIMITED",
            message=message,
            details=details,
            status_code=429,
        )
        self.retry_after = retry_after


class ServerError(AtlassianAPIError):
    """HTTP 5xx - Atlassian server error."""

    def __init__(
        self,
        message: str = "Atlassian server error.",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(
            category="SERVER_ERROR",
            message=message,
            details=details,
            status_code=status_code,
        )
