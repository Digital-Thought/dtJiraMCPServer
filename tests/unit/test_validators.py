"""Tests for input validation functions."""

from __future__ import annotations

import pytest

from dtjiramcpserver.exceptions import InputValidationError
from dtjiramcpserver.validation.validators import (
    validate_enum,
    validate_integer,
    validate_issue_key,
    validate_pagination,
    validate_required,
    validate_string,
)


class TestValidateRequired:
    """Tests for validate_required."""

    def test_present_values_pass(self) -> None:
        """Non-empty values pass validation."""
        validate_required({"name": "test", "value": "data"}, "name", "value")

    def test_missing_field_raises(self) -> None:
        """Missing field raises InputValidationError."""
        with pytest.raises(InputValidationError, match="Missing required parameter: name"):
            validate_required({}, "name")

    def test_none_value_raises(self) -> None:
        """None value raises InputValidationError."""
        with pytest.raises(InputValidationError):
            validate_required({"name": None}, "name")

    def test_empty_string_raises(self) -> None:
        """Empty string raises InputValidationError."""
        with pytest.raises(InputValidationError, match="must not be empty"):
            validate_required({"name": ""}, "name")

    def test_whitespace_only_raises(self) -> None:
        """Whitespace-only string raises InputValidationError."""
        with pytest.raises(InputValidationError, match="must not be empty"):
            validate_required({"name": "   "}, "name")

    def test_non_string_values_pass(self) -> None:
        """Non-string values (int, list) pass presence check."""
        validate_required({"count": 0, "items": []}, "count", "items")


class TestValidateString:
    """Tests for validate_string."""

    def test_valid_string(self) -> None:
        """Valid string returns stripped value."""
        result = validate_string("  hello  ", "field")
        assert result == "hello"

    def test_non_string_raises(self) -> None:
        """Non-string value raises error."""
        with pytest.raises(InputValidationError, match="must be a string"):
            validate_string(123, "field")

    def test_too_short_raises(self) -> None:
        """String shorter than minimum raises error."""
        with pytest.raises(InputValidationError, match="at least"):
            validate_string("", "field", min_length=1)

    def test_too_long_raises(self) -> None:
        """String longer than maximum raises error."""
        with pytest.raises(InputValidationError, match="at most"):
            validate_string("abcdef", "field", max_length=3)

    def test_exact_length_passes(self) -> None:
        """String at exact min/max boundary passes."""
        result = validate_string("abc", "field", min_length=3, max_length=3)
        assert result == "abc"


class TestValidateInteger:
    """Tests for validate_integer."""

    def test_valid_integer(self) -> None:
        """Valid integer returns the value."""
        assert validate_integer(42, "count") == 42

    def test_string_number_coerced(self) -> None:
        """Numeric string is coerced to integer."""
        assert validate_integer("42", "count") == 42

    def test_non_numeric_raises(self) -> None:
        """Non-numeric value raises error."""
        with pytest.raises(InputValidationError, match="must be an integer"):
            validate_integer("abc", "count")

    def test_none_raises(self) -> None:
        """None value raises error."""
        with pytest.raises(InputValidationError, match="must be an integer"):
            validate_integer(None, "count")

    def test_below_minimum_raises(self) -> None:
        """Value below minimum raises error."""
        with pytest.raises(InputValidationError, match="at least"):
            validate_integer(-1, "count", minimum=0)

    def test_above_maximum_raises(self) -> None:
        """Value above maximum raises error."""
        with pytest.raises(InputValidationError, match="at most"):
            validate_integer(200, "count", maximum=100)

    def test_boundary_values_pass(self) -> None:
        """Values at exact boundaries pass."""
        assert validate_integer(0, "count", minimum=0) == 0
        assert validate_integer(100, "count", maximum=100) == 100


class TestValidateIssueKey:
    """Tests for validate_issue_key."""

    def test_valid_keys(self) -> None:
        """Valid issue key formats pass."""
        assert validate_issue_key("PROJ-1") == "PROJ-1"
        assert validate_issue_key("ABC-12345") == "ABC-12345"
        assert validate_issue_key("MY_PROJECT-42") == "MY_PROJECT-42"

    def test_lowercase_uppercased(self) -> None:
        """Lowercase keys are normalised to uppercase."""
        assert validate_issue_key("proj-123") == "PROJ-123"

    def test_invalid_formats(self) -> None:
        """Invalid formats raise error."""
        invalid_keys = ["123-ABC", "PROJ", "PROJ-", "-123", "P-", ""]
        for key in invalid_keys:
            with pytest.raises(InputValidationError):
                validate_issue_key(key)

    def test_non_string_raises(self) -> None:
        """Non-string value raises error."""
        with pytest.raises(InputValidationError):
            validate_issue_key(123)

    def test_whitespace_stripped(self) -> None:
        """Whitespace is stripped before validation."""
        assert validate_issue_key("  PROJ-123  ") == "PROJ-123"


class TestValidateEnum:
    """Tests for validate_enum."""

    def test_valid_value(self) -> None:
        """Valid enum value returns matched value."""
        result = validate_enum("TODO", "status", ["TODO", "IN_PROGRESS", "DONE"])
        assert result == "TODO"

    def test_case_insensitive_match(self) -> None:
        """Case-insensitive matching returns the canonical value."""
        result = validate_enum("todo", "status", ["TODO", "IN_PROGRESS", "DONE"])
        assert result == "TODO"

    def test_case_sensitive_match(self) -> None:
        """Case-sensitive matching rejects wrong case."""
        with pytest.raises(InputValidationError):
            validate_enum("todo", "status", ["TODO"], case_sensitive=True)

    def test_invalid_value_raises(self) -> None:
        """Invalid value raises error with valid options."""
        with pytest.raises(InputValidationError, match="must be one of"):
            validate_enum("INVALID", "status", ["TODO", "DONE"])

    def test_non_string_raises(self) -> None:
        """Non-string value raises error."""
        with pytest.raises(InputValidationError, match="must be a string"):
            validate_enum(123, "status", ["TODO"])


class TestValidatePagination:
    """Tests for validate_pagination."""

    def test_defaults(self) -> None:
        """Default values applied when not specified."""
        start, limit = validate_pagination({})
        assert start == 0
        assert limit == 50

    def test_custom_values(self) -> None:
        """Custom start and limit values used."""
        start, limit = validate_pagination({"start": 10, "limit": 25})
        assert start == 10
        assert limit == 25

    def test_custom_defaults(self) -> None:
        """Custom default_limit applied."""
        start, limit = validate_pagination({}, default_limit=20)
        assert limit == 20

    def test_exceeds_max_raises(self) -> None:
        """Limit exceeding maximum raises error."""
        with pytest.raises(InputValidationError, match="at most"):
            validate_pagination({"limit": 200}, max_limit=100)

    def test_negative_start_raises(self) -> None:
        """Negative start raises error."""
        with pytest.raises(InputValidationError, match="at least"):
            validate_pagination({"start": -1})

    def test_zero_limit_raises(self) -> None:
        """Zero limit raises error."""
        with pytest.raises(InputValidationError, match="at least"):
            validate_pagination({"limit": 0})

    def test_none_values_use_defaults(self) -> None:
        """Explicitly None values fall back to defaults."""
        start, limit = validate_pagination({"start": None, "limit": None})
        assert start == 0
        assert limit == 50
