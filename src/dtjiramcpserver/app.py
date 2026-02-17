"""Main application class for dtJiraMCPServer.

Inherits from dtPyAppFramework's AbstractApp to integrate with the
framework's configuration, logging, and lifecycle management.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from dtPyAppFramework.application import AbstractApp

from dtjiramcpserver import __description__, __full_name__, __short_name__, __version__
from dtjiramcpserver.config.models import AppConfig, JiraConfig, ServerConfig

logger = logging.getLogger(__name__)


class JiraMCPServerApp(AbstractApp):
    """Main application class for dtJiraMCPServer."""

    def __init__(self) -> None:
        super().__init__(
            description=__description__,
            version=__version__,
            short_name=__short_name__,
            full_name=__full_name__,
            console_app=True,
        )

    def define_args(self, arg_parser) -> None:  # type: ignore[override]
        """Define command-line arguments.

        No custom arguments needed beyond dtPyAppFramework built-ins.
        The server always runs in stdio mode.
        """

    def main(self, args) -> None:  # type: ignore[override]
        """Main application entry point.

        Creates configuration from environment variables, redirects
        logging to stderr (critical for stdio MCP transport), and
        runs the async MCP server.
        """
        # CRITICAL: Redirect all logging to stderr before any output.
        # stdout is reserved for MCP JSON-RPC protocol messages.
        self._configure_stderr_logging()

        # Load and validate configuration from environment variables
        try:
            config = self._load_config()
        except (KeyError, ValueError) as exc:
            logger.critical("Configuration error: %s", exc)
            logger.critical(
                "Required environment variables: JIRA_INSTANCE_URL, "
                "JIRA_USER_EMAIL, JIRA_API_TOKEN"
            )
            sys.exit(1)

        logger.info("Starting dtJiraMCPServer v%s", __version__)
        logger.info("Jira instance: %s", config.jira.instance_url)

        # Run the async MCP server (blocks until stdin closes)
        from dtjiramcpserver.server import run_stdio_server

        asyncio.run(run_stdio_server(config))

        # When asyncio.run returns, stdin has closed (client disconnected).
        # Just return - dtPyAppFramework handles shutdown (one-shot pattern).
        logger.info("Server shutdown complete")

    def exiting(self) -> None:
        """Cleanup callback on application exit."""
        logger.info("dtJiraMCPServer exiting")

    @staticmethod
    def _configure_stderr_logging() -> None:
        """Ensure all log handlers write to stderr, not stdout.

        The MCP stdio transport uses stdout for JSON-RPC messages.
        Any logging to stdout would corrupt the protocol stream.
        """
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                if handler.stream is sys.stdout:
                    handler.stream = sys.stderr

    @staticmethod
    def _load_config() -> AppConfig:
        """Load configuration from environment variables.

        Returns:
            Validated AppConfig instance.

        Raises:
            KeyError: If a required environment variable is missing.
            ValueError: If a value fails Pydantic validation.
        """
        read_only_str = os.environ.get("JIRA_READ_ONLY", "false").strip().lower()
        read_only = read_only_str in ("true", "1", "yes")

        return AppConfig(
            jira=JiraConfig(
                instance_url=os.environ["JIRA_INSTANCE_URL"],
                user_email=os.environ["JIRA_USER_EMAIL"],
                api_token=os.environ["JIRA_API_TOKEN"],
                read_only=read_only,
            ),
            server=ServerConfig(
                log_level=os.environ.get("LOG_LEVEL", "INFO"),
            ),
        )
