"""Tests for configuration models."""

from __future__ import annotations

import pytest

from dtjiramcpserver.config.models import AppConfig, JiraConfig, ServerConfig


class TestJiraConfig:
    """Tests for JiraConfig validation."""

    def test_valid_config(self) -> None:
        """Valid config creates successfully."""
        config = JiraConfig(
            instance_url="https://test.atlassian.net",
            user_email="user@example.com",
            api_token="token123",
        )
        assert config.instance_url == "https://test.atlassian.net"
        assert config.user_email == "user@example.com"
        assert config.api_token == "token123"

    def test_strips_trailing_slash(self) -> None:
        """URL normalisation strips trailing slashes."""
        config = JiraConfig(
            instance_url="https://test.atlassian.net/",
            user_email="user@example.com",
            api_token="token123",
        )
        assert config.instance_url == "https://test.atlassian.net"

    def test_strips_multiple_trailing_slashes(self) -> None:
        """URL normalisation strips multiple trailing slashes."""
        config = JiraConfig(
            instance_url="https://test.atlassian.net///",
            user_email="user@example.com",
            api_token="token123",
        )
        assert config.instance_url == "https://test.atlassian.net"

    def test_missing_protocol_raises(self) -> None:
        """URL without http/https raises ValueError."""
        with pytest.raises(ValueError, match="must start with http"):
            JiraConfig(
                instance_url="test.atlassian.net",
                user_email="user@example.com",
                api_token="token123",
            )

    def test_invalid_email_raises(self) -> None:
        """Email without @ raises ValueError."""
        with pytest.raises(ValueError, match="valid email"):
            JiraConfig(
                instance_url="https://test.atlassian.net",
                user_email="not-an-email",
                api_token="token123",
            )

    def test_empty_email_raises(self) -> None:
        """Empty email raises ValueError."""
        with pytest.raises(ValueError, match="valid email"):
            JiraConfig(
                instance_url="https://test.atlassian.net",
                user_email="",
                api_token="token123",
            )

    def test_empty_api_token_raises(self) -> None:
        """Empty API token raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            JiraConfig(
                instance_url="https://test.atlassian.net",
                user_email="user@example.com",
                api_token="",
            )

    def test_api_token_not_in_repr(self) -> None:
        """API token is excluded from string representation."""
        config = JiraConfig(
            instance_url="https://test.atlassian.net",
            user_email="user@example.com",
            api_token="secret-token",
        )
        repr_str = repr(config)
        assert "secret-token" not in repr_str

    def test_whitespace_stripped(self) -> None:
        """Whitespace is stripped from all string fields."""
        config = JiraConfig(
            instance_url="  https://test.atlassian.net  ",
            user_email="  user@example.com  ",
            api_token="  token123  ",
        )
        assert config.instance_url == "https://test.atlassian.net"
        assert config.user_email == "user@example.com"
        assert config.api_token == "token123"


class TestServerConfig:
    """Tests for ServerConfig validation."""

    def test_default_log_level(self) -> None:
        """Default log level is INFO."""
        config = ServerConfig()
        assert config.log_level == "INFO"

    def test_valid_log_levels(self) -> None:
        """All standard log levels are accepted."""
        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            config = ServerConfig(log_level=level)
            assert config.log_level == level

    def test_case_insensitive_log_level(self) -> None:
        """Log level is normalised to uppercase."""
        config = ServerConfig(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_invalid_log_level_raises(self) -> None:
        """Invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="log_level must be one of"):
            ServerConfig(log_level="TRACE")


class TestAppConfig:
    """Tests for AppConfig."""

    def test_valid_config(self, sample_jira_config: JiraConfig) -> None:
        """Valid AppConfig creates successfully."""
        config = AppConfig(jira=sample_jira_config)
        assert config.jira.instance_url == "https://test.atlassian.net"
        assert config.server.log_level == "INFO"  # default

    def test_server_config_defaults(self, sample_jira_config: JiraConfig) -> None:
        """ServerConfig defaults are applied when not specified."""
        config = AppConfig(jira=sample_jira_config)
        assert config.server.log_level == "INFO"
