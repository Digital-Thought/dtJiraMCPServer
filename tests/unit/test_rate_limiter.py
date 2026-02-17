"""Tests for rate limiter with exponential backoff."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from dtjiramcpserver.client.rate_limiter import RateLimiter


def _make_response(status_code: int, headers: dict | None = None) -> httpx.Response:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.headers = headers or {}
    return response


class TestRateLimiter:
    """Tests for RateLimiter retry behaviour."""

    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self) -> None:
        """200 response returns immediately without retry."""
        limiter = RateLimiter()
        request_func = AsyncMock(return_value=_make_response(200))

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 200
        assert request_func.call_count == 1

    @pytest.mark.asyncio
    async def test_non_retryable_error_returns_immediately(self) -> None:
        """Non-retryable errors (e.g. 404) return without retry."""
        limiter = RateLimiter()
        request_func = AsyncMock(return_value=_make_response(404))

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 404
        assert request_func.call_count == 1

    @pytest.mark.asyncio
    @patch("dtjiramcpserver.client.rate_limiter.asyncio.sleep", new_callable=AsyncMock)
    async def test_429_retries_then_succeeds(self, mock_sleep: AsyncMock) -> None:
        """Rate limited requests retry and succeed."""
        limiter = RateLimiter(initial_delay_rate_limit=1.0)
        request_func = AsyncMock(
            side_effect=[
                _make_response(429),
                _make_response(429),
                _make_response(200),
            ]
        )

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 200
        assert request_func.call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("dtjiramcpserver.client.rate_limiter.asyncio.sleep", new_callable=AsyncMock)
    async def test_429_respects_retry_after_header(self, mock_sleep: AsyncMock) -> None:
        """Uses Retry-After header value for delay."""
        limiter = RateLimiter()
        request_func = AsyncMock(
            side_effect=[
                _make_response(429, headers={"Retry-After": "7"}),
                _make_response(200),
            ]
        )

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 200
        mock_sleep.assert_called_once_with(7.0)

    @pytest.mark.asyncio
    @patch("dtjiramcpserver.client.rate_limiter.asyncio.sleep", new_callable=AsyncMock)
    async def test_429_exceeds_max_retries(self, mock_sleep: AsyncMock) -> None:
        """Returns last response when max retries exhausted on 429."""
        limiter = RateLimiter(max_retries_rate_limit=2, initial_delay_rate_limit=0.1)
        request_func = AsyncMock(return_value=_make_response(429))

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 429
        # Initial call + 2 retries = 3 calls total
        assert request_func.call_count == 3

    @pytest.mark.asyncio
    @patch("dtjiramcpserver.client.rate_limiter.asyncio.sleep", new_callable=AsyncMock)
    async def test_500_retries_then_succeeds(self, mock_sleep: AsyncMock) -> None:
        """Server error retries and succeeds."""
        limiter = RateLimiter(initial_delay_server_error=0.1)
        request_func = AsyncMock(
            side_effect=[
                _make_response(500),
                _make_response(200),
            ]
        )

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 200
        assert request_func.call_count == 2

    @pytest.mark.asyncio
    @patch("dtjiramcpserver.client.rate_limiter.asyncio.sleep", new_callable=AsyncMock)
    async def test_500_exceeds_max_retries(self, mock_sleep: AsyncMock) -> None:
        """Returns last response when max retries exhausted on 5xx."""
        limiter = RateLimiter(max_retries_server_error=1, initial_delay_server_error=0.1)
        request_func = AsyncMock(return_value=_make_response(500))

        result = await limiter.execute_with_retry(request_func)

        assert result.status_code == 500
        # Initial call + 1 retry = 2 calls
        assert request_func.call_count == 2

    def test_backoff_delay_calculation(self) -> None:
        """Exponential backoff calculates correct delays."""
        limiter = RateLimiter(backoff_multiplier=2.0)

        delay_0 = limiter._calculate_delay(0, 5.0, 60.0)
        delay_1 = limiter._calculate_delay(1, 5.0, 60.0)
        delay_2 = limiter._calculate_delay(2, 5.0, 60.0)

        assert delay_0 == 5.0    # 5 * 2^0
        assert delay_1 == 10.0   # 5 * 2^1
        assert delay_2 == 20.0   # 5 * 2^2

    def test_max_delay_cap_respected(self) -> None:
        """Delay never exceeds the maximum."""
        limiter = RateLimiter(backoff_multiplier=2.0)

        delay = limiter._calculate_delay(10, 5.0, 60.0)

        assert delay == 60.0

    def test_retry_after_overrides_calculation(self) -> None:
        """Retry-After value takes precedence over calculated delay."""
        limiter = RateLimiter()

        delay = limiter._calculate_delay(0, 5.0, 60.0, retry_after=15.0)

        assert delay == 15.0

    def test_retry_after_capped_at_max(self) -> None:
        """Retry-After value is capped at max delay."""
        limiter = RateLimiter()

        delay = limiter._calculate_delay(0, 5.0, 60.0, retry_after=120.0)

        assert delay == 60.0
