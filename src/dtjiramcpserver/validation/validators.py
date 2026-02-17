"""Stateless input validation functions for MCP tool parameters.

All validators raise InputValidationError with field name and reason
populated, enabling structured LLM-friendly error responses.
"""

from __future__ import annotations

import re
from typing import Any

from dtjiramcpserver.exceptions import InputValidationError

# Jira issue key pattern: PROJECT-123
_ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")

# Jira project key pattern: 2-10 uppercase alphanumeric, starting with a letter
_PROJECT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")


def validate_required(params: dict[str, Any], *field_names: str) -> None:
    """Validate that all specified fields are present and non-empty.

    Args:
        params: Dictionary of tool parameters.
        *field_names: Names of required fields.

    Raises:
        InputValidationError: If any required field is missing or empty.
    """
    for name in field_names:
        value = params.get(name)
        if value is None:
            raise InputValidationError(
                message=f"Missing required parameter: {name}",
                field=name,
                reason="required",
            )
        if isinstance(value, str) and not value.strip():
            raise InputValidationError(
                message=f"Parameter '{name}' must not be empty",
                field=name,
                reason="empty",
            )


def validate_string(
    value: Any,
    field_name: str,
    min_length: int = 1,
    max_length: int | None = None,
) -> str:
    """Validate and return a string parameter.

    Args:
        value: The value to validate.
        field_name: Name of the parameter (for error messages).
        min_length: Minimum string length (default 1, non-empty).
        max_length: Optional maximum string length.

    Returns:
        The validated, stripped string value.

    Raises:
        InputValidationError: If validation fails.
    """
    if not isinstance(value, str):
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be a string",
            field=field_name,
            reason="invalid_type",
        )

    value = value.strip()

    if len(value) < min_length:
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be at least {min_length} characters",
            field=field_name,
            reason="too_short",
        )

    if max_length is not None and len(value) > max_length:
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be at most {max_length} characters",
            field=field_name,
            reason="too_long",
        )

    return value


def validate_integer(
    value: Any,
    field_name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Validate and return an integer parameter.

    Args:
        value: The value to validate (int or numeric string).
        field_name: Name of the parameter (for error messages).
        minimum: Optional minimum value (inclusive).
        maximum: Optional maximum value (inclusive).

    Returns:
        The validated integer value.

    Raises:
        InputValidationError: If validation fails.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be an integer",
            field=field_name,
            reason="invalid_type",
        )

    if minimum is not None and int_value < minimum:
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be at least {minimum}",
            field=field_name,
            reason="below_minimum",
        )

    if maximum is not None and int_value > maximum:
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be at most {maximum}",
            field=field_name,
            reason="above_maximum",
        )

    return int_value


def validate_issue_key(value: Any, field_name: str = "issue_key") -> str:
    """Validate a Jira issue key format (e.g. PROJ-123).

    Args:
        value: The value to validate.
        field_name: Name of the parameter (for error messages).

    Returns:
        The validated, uppercase issue key.

    Raises:
        InputValidationError: If the format is invalid.
    """
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be a non-empty string",
            field=field_name,
            reason="invalid_type",
        )

    key = value.strip().upper()

    if not _ISSUE_KEY_PATTERN.match(key):
        raise InputValidationError(
            message=f"Parameter '{field_name}' must match format PROJECT-123 (got '{value}')",
            field=field_name,
            reason="invalid_format",
        )

    return key


def validate_project_key(value: Any, field_name: str = "key") -> str:
    """Validate a Jira project key format (2-10 uppercase alphanumeric, starting with letter).

    Args:
        value: The value to validate.
        field_name: Name of the parameter (for error messages).

    Returns:
        The validated, uppercase project key.

    Raises:
        InputValidationError: If the format is invalid.
    """
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be a non-empty string",
            field=field_name,
            reason="invalid_type",
        )

    key = value.strip().upper()

    if not _PROJECT_KEY_PATTERN.match(key):
        raise InputValidationError(
            message=(
                f"Parameter '{field_name}' must be 2-10 uppercase alphanumeric "
                f"characters starting with a letter (got '{value}')"
            ),
            field=field_name,
            reason="invalid_format",
        )

    return key


def validate_enum(
    value: Any,
    field_name: str,
    valid_values: list[str],
    case_sensitive: bool = False,
) -> str:
    """Validate a value against a known set of options.

    Args:
        value: The value to validate.
        field_name: Name of the parameter (for error messages).
        valid_values: List of acceptable values.
        case_sensitive: Whether comparison is case-sensitive.

    Returns:
        The matched value (preserving case of valid_values if case-insensitive).

    Raises:
        InputValidationError: If value is not in valid_values.
    """
    if not isinstance(value, str):
        raise InputValidationError(
            message=f"Parameter '{field_name}' must be a string",
            field=field_name,
            reason="invalid_type",
        )

    value = value.strip()

    if case_sensitive:
        if value in valid_values:
            return value
    else:
        value_lower = value.lower()
        for valid in valid_values:
            if valid.lower() == value_lower:
                return valid

    raise InputValidationError(
        message=f"Parameter '{field_name}' must be one of {valid_values} (got '{value}')",
        field=field_name,
        reason="invalid_value",
    )


def validate_pagination(
    params: dict[str, Any],
    default_limit: int = 50,
    max_limit: int = 100,
) -> tuple[int, int]:
    """Extract and validate start/limit pagination parameters.

    Args:
        params: Dictionary of tool parameters.
        default_limit: Default page size if not specified.
        max_limit: Maximum allowed page size.

    Returns:
        Tuple of (start, limit) as validated integers.

    Raises:
        InputValidationError: If values are invalid.
    """
    start = 0
    limit = default_limit

    if "start" in params and params["start"] is not None:
        start = validate_integer(params["start"], "start", minimum=0)

    if "limit" in params and params["limit"] is not None:
        limit = validate_integer(params["limit"], "limit", minimum=1, maximum=max_limit)

    return start, limit
