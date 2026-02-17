"""Rate limit handler with exponential backoff for Atlassian API calls.

Retry strategy from architecture specification:
    429 (Rate Limited): max 5 retries, 5s initial delay, 2x backoff, 60s max
    5xx (Server Error): max 3 retries, 2s initial delay, 2x backoff, 30s max
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from dtjiramcpserver.exceptions import RateLimitError, ServerError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Exponential backoff retry handler for transient HTTP errors."""

    def __init__(
        self,
        max_retries_rate_limit: int = 5,
        max_retries_server_error: int = 3,
        initial_delay_rate_limit: float = 5.0,
        initial_delay_server_error: float = 2.0,
        backoff_multiplier: float = 2.0,
        max_delay_rate_limit: float = 60.0,
        max_delay_server_error: float = 30.0,
    ) -> None:
        self.max_retries_rate_limit = max_retries_rate_limit
        self.max_retries_server_error = max_retries_server_error
        self.initial_delay_rate_limit = initial_delay_rate_limit
        self.initial_delay_server_error = initial_delay_server_error
        self.backoff_multiplier = backoff_multiplier
        self.max_delay_rate_limit = max_delay_rate_limit
        self.max_delay_server_error = max_delay_server_error

    def _get_retry_params(
        self, status_code: int
    ) -> tuple[int, float, float] | None:
        """Return (max_retries, initial_delay, max_delay) for a retryable status code.

        Returns None if the status code is not retryable.
        """
        if status_code == 429:
            return (
                self.max_retries_rate_limit,
                self.initial_delay_rate_limit,
                self.max_delay_rate_limit,
            )
        if 500 <= status_code < 600:
            return (
                self.max_retries_server_error,
                self.initial_delay_server_error,
                self.max_delay_server_error,
            )
        return None

    def _calculate_delay(
        self,
        attempt: int,
        initial_delay: float,
        max_delay: float,
        retry_after: float | None = None,
    ) -> float:
        """Calculate the delay before the next retry attempt.

        Uses the Retry-After header value if provided, otherwise
        calculates exponential backoff.
        """
        if retry_after is not None and retry_after > 0:
            return min(retry_after, max_delay)
        delay = initial_delay * (self.backoff_multiplier ** attempt)
        return min(delay, max_delay)

    async def execute_with_retry(
        self,
        request_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute an HTTP request with automatic retry on retryable errors.

        Args:
            request_func: Async callable that returns an httpx.Response.
            *args: Positional arguments for request_func.
            **kwargs: Keyword arguments for request_func.

        Returns:
            The httpx.Response from a successful request.

        Raises:
            RateLimitError: If max retries exhausted on 429 responses.
            ServerError: If max retries exhausted on 5xx responses.
        """
        last_response: httpx.Response | None = None
        attempt = 0

        while True:
            response: httpx.Response = await request_func(*args, **kwargs)
            status_code = response.status_code

            # Success - return immediately
            if status_code < 400:
                return response

            # Check if retryable
            retry_params = self._get_retry_params(status_code)
            if retry_params is None:
                # Not retryable, return the response for error classification
                return response

            max_retries, initial_delay, max_delay = retry_params
            last_response = response

            if attempt >= max_retries:
                # Exhausted retries, return the last response
                logger.error(
                    "Max retries (%d) exhausted for HTTP %d",
                    max_retries,
                    status_code,
                )
                return last_response

            # Parse Retry-After header
            retry_after: float | None = None
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    retry_after = None

            delay = self._calculate_delay(attempt, initial_delay, max_delay, retry_after)

            logger.warning(
                "HTTP %d received, retrying in %.1fs (attempt %d/%d)",
                status_code,
                delay,
                attempt + 1,
                max_retries,
            )

            await asyncio.sleep(delay)
            attempt += 1
