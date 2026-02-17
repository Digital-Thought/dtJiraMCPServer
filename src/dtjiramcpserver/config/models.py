"""Pydantic configuration models for dtJiraMCPServer.

Configuration is loaded from environment variables at startup:
    JIRA_INSTANCE_URL - Atlassian Cloud instance URL
    JIRA_USER_EMAIL   - Atlassian account email for Basic Auth
    JIRA_API_TOKEN    - Atlassian API token
    LOG_LEVEL         - Application log level (default: INFO)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class JiraConfig(BaseModel):
    """Configuration for Jira Cloud connection."""

    instance_url: str = Field(..., description="Atlassian Cloud instance URL")
    user_email: str = Field(..., description="Atlassian account email for authentication")
    api_token: str = Field(..., repr=False, description="Atlassian API token")
    read_only: bool = Field(default=False, description="When true, only read-only tools are available")

    @field_validator("instance_url")
    @classmethod
    def normalise_instance_url(cls, v: str) -> str:
        """Strip trailing slashes and validate URL format."""
        v = v.strip().rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("instance_url must start with http:// or https://")
        return v

    @field_validator("user_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email format validation."""
        v = v.strip()
        if not v or "@" not in v:
            raise ValueError("user_email must be a valid email address")
        return v

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, v: str) -> str:
        """Ensure API token is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("api_token must not be empty")
        return v


class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a recognised value."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.strip().upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v


class AppConfig(BaseModel):
    """Root application configuration."""

    jira: JiraConfig
    server: ServerConfig = Field(default_factory=ServerConfig)
