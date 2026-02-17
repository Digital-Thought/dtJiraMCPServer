"""Tests for BaseTool and ToolResult models."""

from __future__ import annotations

from typing import Any

import pytest

from dtjiramcpserver.exceptions import AtlassianAPIError, InputValidationError
from dtjiramcpserver.tools.base import BaseTool, ToolGuide, ToolResult


class DummyTool(BaseTool):
    """Concrete tool for testing BaseTool behaviour."""

    name = "dummy_tool"
    category = "test"
    description = "A dummy tool for testing"
    input_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    def __init__(self, execute_result: Any = None, execute_error: Exception | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._execute_result = execute_result
        self._execute_error = execute_error

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        if self._execute_error:
            raise self._execute_error
        return self._execute_result or ToolResult.ok(data={"test": True})

    def get_guide(self) -> ToolGuide:
        return ToolGuide(
            name=self.name,
            category=self.category,
            description=self.description,
            parameters=[],
        )


class TestToolResult:
    """Tests for ToolResult model."""

    def test_ok_factory(self) -> None:
        """ToolResult.ok() creates successful response."""
        result = ToolResult.ok(data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_ok_with_pagination(self) -> None:
        """ToolResult.ok() includes pagination metadata."""
        pagination = {"start": 0, "limit": 50, "total": 100, "has_more": True}
        result = ToolResult.ok(data=[], pagination=pagination)
        assert result.pagination == pagination

    def test_fail_factory(self) -> None:
        """ToolResult.fail() creates error response."""
        result = ToolResult.fail(
            error_type="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "name"},
        )
        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert result.error["type"] == "VALIDATION_ERROR"
        assert result.error["message"] == "Invalid input"
        assert result.error["details"] == {"field": "name"}

    def test_fail_without_details(self) -> None:
        """ToolResult.fail() works without details."""
        result = ToolResult.fail(error_type="SERVER_ERROR", message="Oops")
        assert result.error is not None
        assert "details" not in result.error

    def test_serialisation_round_trip(self) -> None:
        """ToolResult serialises to and from dict."""
        result = ToolResult.ok(data={"items": [1, 2, 3]})
        dumped = result.model_dump()
        assert dumped["success"] is True
        assert dumped["data"] == {"items": [1, 2, 3]}


class TestBaseTool:
    """Tests for BaseTool safe_execute behaviour."""

    @pytest.mark.asyncio
    async def test_safe_execute_success(self) -> None:
        """Successful execution passes through."""
        tool = DummyTool()
        result = await tool.safe_execute({})
        assert result.success is True
        assert result.data == {"test": True}

    @pytest.mark.asyncio
    async def test_safe_execute_catches_validation_error(self) -> None:
        """InputValidationError mapped to VALIDATION_ERROR."""
        tool = DummyTool(
            execute_error=InputValidationError("Bad input", field="name", reason="required")
        )
        result = await tool.safe_execute({})
        assert result.success is False
        assert result.error is not None
        assert result.error["type"] == "VALIDATION_ERROR"
        assert result.error["details"]["field"] == "name"
        assert result.error["details"]["reason"] == "required"

    @pytest.mark.asyncio
    async def test_safe_execute_catches_atlassian_error(self) -> None:
        """AtlassianAPIError mapped to correct category."""
        tool = DummyTool(
            execute_error=AtlassianAPIError(
                category="NOT_FOUND",
                message="Issue not found",
                details={"key": "PROJ-999"},
            )
        )
        result = await tool.safe_execute({})
        assert result.success is False
        assert result.error is not None
        assert result.error["type"] == "NOT_FOUND"
        assert result.error["message"] == "Issue not found"

    @pytest.mark.asyncio
    async def test_safe_execute_catches_unexpected_error(self) -> None:
        """Unexpected exceptions mapped to SERVER_ERROR."""
        tool = DummyTool(execute_error=RuntimeError("Something broke"))
        result = await tool.safe_execute({})
        assert result.success is False
        assert result.error is not None
        assert result.error["type"] == "SERVER_ERROR"
        assert "Something broke" in result.error["message"]
