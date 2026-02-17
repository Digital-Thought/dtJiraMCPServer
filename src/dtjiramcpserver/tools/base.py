"""Base tool class and response models for the MCP tool framework.

Defines the contract that all tools must implement (AD-004):
    - name, category, description, input_schema class attributes
    - execute() for tool logic
    - get_guide() for self-documentation
    - safe_execute() wraps execute() with exception-to-ToolResult mapping
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Self-documentation models (AD-004)
# --------------------------------------------------------------------------- #


class ParameterGuide(BaseModel):
    """Documentation for a single tool parameter."""

    name: str
    type: str
    required: bool
    description: str
    default: Any = None
    valid_values: list[str] | None = None
    constraints: str | None = None


class ToolExample(BaseModel):
    """Example invocation of a tool."""

    description: str
    parameters: dict[str, Any]
    expected_behaviour: str


class ToolGuide(BaseModel):
    """Structured documentation for a tool, returned by get_guide()."""

    name: str
    category: str
    description: str
    parameters: list[ParameterGuide]
    response_format: dict[str, Any] = Field(default_factory=dict)
    examples: list[ToolExample] = Field(default_factory=list)
    prerequisites: list[str] | None = None
    related_tools: list[str] | None = None
    notes: list[str] | None = None


# --------------------------------------------------------------------------- #
# Tool response model
# --------------------------------------------------------------------------- #


class ToolResult(BaseModel):
    """Standardised tool response format.

    All tools return this model to ensure consistent response structure
    for the LLM client.
    """

    success: bool
    data: Any = None
    pagination: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @classmethod
    def ok(cls, data: Any, pagination: dict[str, Any] | None = None) -> ToolResult:
        """Create a successful response."""
        return cls(success=True, data=data, pagination=pagination)

    @classmethod
    def fail(
        cls,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create an error response."""
        error: dict[str, Any] = {"type": error_type, "message": message}
        if details:
            error["details"] = details
        return cls(success=False, error=error)


# --------------------------------------------------------------------------- #
# Base tool class
# --------------------------------------------------------------------------- #


class BaseTool(ABC):
    """Abstract base class for all MCP tools.

    Every tool must:
        1. Set name, category, description class attributes
        2. Define input_schema (JSON Schema dict) for MCP registration
        3. Implement execute() for the actual logic
        4. Implement get_guide() for self-documentation

    The safe_execute() method wraps execute() with top-level exception
    handling, mapping all known exceptions to ToolResult.fail() responses.
    Individual tool implementations should raise exceptions rather than
    catching them internally.
    """

    name: str
    category: str
    description: str
    input_schema: dict[str, Any]
    mutates: bool = False

    def __init__(
        self,
        platform_client: Any = None,
        jsm_client: Any = None,
        **kwargs: Any,
    ) -> None:
        self._platform_client = platform_client
        self._jsm_client = jsm_client

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given arguments.

        Implementations should:
            1. Validate arguments using validation utilities
            2. Call the appropriate Atlassian client method
            3. Return ToolResult.ok() or raise an exception

        Args:
            arguments: Tool parameters from the MCP client.

        Returns:
            ToolResult with the operation outcome.
        """
        ...

    @abstractmethod
    def get_guide(self) -> ToolGuide:
        """Return structured self-documentation for this tool.

        The guide is served by the get_tool_guide meta-tool to help
        the LLM understand how to invoke this tool correctly.
        """
        ...

    async def safe_execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Execute with top-level exception handling.

        Catches InputValidationError and AtlassianAPIError and converts
        them to ToolResult.fail() responses. This is the method called
        by the registry, not execute() directly.
        """
        from dtjiramcpserver.exceptions import AtlassianAPIError, InputValidationError

        try:
            return await self.execute(arguments)
        except InputValidationError as exc:
            return ToolResult.fail(
                error_type="VALIDATION_ERROR",
                message=str(exc),
                details=(
                    {"field": exc.field, "reason": exc.reason}
                    if exc.field
                    else None
                ),
            )
        except AtlassianAPIError as exc:
            return ToolResult.fail(
                error_type=exc.category,
                message=exc.message,
                details=exc.details,
            )
        except Exception as exc:
            logger.exception("Unexpected error in tool %s", self.name)
            return ToolResult.fail(
                error_type="SERVER_ERROR",
                message=f"Unexpected error: {exc}",
            )
