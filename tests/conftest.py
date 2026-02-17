"""Shared pytest fixtures for dtJiraMCPServer tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from dtjiramcpserver.config.models import AppConfig, JiraConfig, ServerConfig
from dtjiramcpserver.tools.registry import ToolRegistry

# Central constant: update here when tools are added/removed.
# meta (2) + issues (7) + servicedesk (10) + requesttypes (6) + fields (10)
# + workflows (8) + kb (1) + sla (2) + assets (1) + projects (5) + lookup (3)
# + groups (6) = 61
EXPECTED_TOOL_COUNT = 61


@pytest.fixture
def sample_jira_config() -> JiraConfig:
    """Valid JiraConfig for testing."""
    return JiraConfig(
        instance_url="https://test.atlassian.net",
        user_email="test@example.com",
        api_token="test-api-token-123",
    )


@pytest.fixture
def sample_config(sample_jira_config: JiraConfig) -> AppConfig:
    """Valid AppConfig for testing."""
    return AppConfig(
        jira=sample_jira_config,
        server=ServerConfig(log_level="DEBUG"),
    )


@pytest.fixture
def mock_platform_client() -> AsyncMock:
    """Mocked PlatformClient."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/api/3"
    return client


@pytest.fixture
def mock_jsm_client() -> AsyncMock:
    """Mocked JsmClient."""
    client = AsyncMock()
    client.base_url = "https://test.atlassian.net/rest/servicedeskapi"
    return client


@pytest.fixture
def tool_registry(mock_platform_client: AsyncMock, mock_jsm_client: AsyncMock) -> ToolRegistry:
    """ToolRegistry with mocked clients and meta tools registered."""
    registry = ToolRegistry(
        platform_client=mock_platform_client,
        jsm_client=mock_jsm_client,
    )
    registry.discover_and_register()
    return registry
