"""Tests for the rate-limit-aware Groq client."""

import asyncio
import time
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from groq import GroqError, RateLimitError

from src.config import get_settings
from src.llm.groq_client import GroqDailyLimitError, RateLimitedGroq, RateLimiter


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure we have a valid test environment."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_1234567890abcdef")
    get_settings()  # Force reload


class TestRateLimiter:
    """Test the token bucket logic directly."""

    @pytest.mark.asyncio
    async def test_rpm_limit_delays_execution(self) -> None:
        # Allow 2 requests per minute
        limiter = RateLimiter(model_id="test-model", rpm=2, tpm=1000, rpd=100)

        start = time.time()
        await limiter.acquire(10)  # 1st request (immediate)
        await limiter.acquire(10)  # 2nd request (immediate)

        # 3rd request should block until the sliding window clears
        # We manually advance the request times to avoid actually sleeping 60s in the test
        limiter.request_times = [time.time() - 59.9, time.time() - 59.9]

        await limiter.acquire(10)
        elapsed = time.time() - start

        # It should have waited roughly 0.1 seconds
        assert elapsed > 0.05
        assert limiter.daily_count == 3

    @pytest.mark.asyncio
    async def test_tpm_limit_paces_execution(self) -> None:
        # Allow 100 tokens per minute
        limiter = RateLimiter(model_id="test-model", rpm=100, tpm=100, rpd=100)

        start = time.time()
        await limiter.acquire(60)  # immediate (60 < 100)

        # Next request is 50 tokens. 60 + 50 = 110 > 100.
        # Should pace execution (sleep 2s).
        await limiter.acquire(50)
        elapsed = time.time() - start

        assert elapsed >= 2.0
        assert limiter.token_count == 50  # Reset and added new tokens

    @pytest.mark.asyncio
    async def test_daily_limit_raises_error(self) -> None:
        limiter = RateLimiter(model_id="test-model", rpm=100, tpm=1000, rpd=2)

        await limiter.acquire(10)
        await limiter.acquire(10)

        with pytest.raises(GroqDailyLimitError):
            await limiter.acquire(10)

    @pytest.mark.asyncio
    async def test_daily_limit_resets_next_day(self) -> None:
        limiter = RateLimiter(model_id="test-model", rpm=100, tpm=1000, rpd=2)

        await limiter.acquire(10)
        await limiter.acquire(10)

        # Simulate moving to next day
        limiter.last_reset_day = "1999-12-31"

        # Should work now
        await limiter.acquire(10)
        assert limiter.daily_count == 1


class TestRateLimitedGroq:
    """Test the AsyncGroq wrapper and backoff logic."""

    @pytest.mark.asyncio
    @patch("src.llm.groq_client.AsyncGroq")
    async def test_successful_generation(
        self, mock_async_groq: MagicMock, mock_settings: None
    ) -> None:
        # Setup mock client
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mock response"))]
        )
        mock_async_groq.return_value = mock_instance

        client = RateLimitedGroq()
        response = await client.generate(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-8b-instant",
        )

        assert response.choices[0].message.content == "Mock response"
        mock_instance.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.llm.groq_client.asyncio.sleep")
    @patch("src.llm.groq_client.AsyncGroq")
    async def test_exponential_backoff_on_rate_limit(
        self, mock_async_groq: MagicMock, mock_sleep: AsyncMock, mock_settings: None
    ) -> None:
        mock_instance = AsyncMock()
        
        # Make it fail twice with RateLimitError, then succeed
        error_response = MagicMock()
        error_response.status_code = 429
        mock_instance.chat.completions.create.side_effect = [
            RateLimitError("Rate limited", response=error_response, body=None),
            RateLimitError("Rate limited again", response=error_response, body=None),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Success!"))]),
        ]
        mock_async_groq.return_value = mock_instance

        client = RateLimitedGroq()
        response = await client.generate(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.1-8b-instant",
        )

        assert response.choices[0].message.content == "Success!"
        assert mock_instance.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2  # Slept twice due to backoff

    @pytest.mark.asyncio
    @patch("src.llm.groq_client.AsyncGroq")
    async def test_fails_immediately_on_other_errors(
        self, mock_async_groq: MagicMock, mock_settings: None
    ) -> None:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create.side_effect = GroqError("Auth failed")
        mock_async_groq.return_value = mock_instance

        client = RateLimitedGroq()

        with pytest.raises(GroqError):
            await client.generate(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama-3.1-8b-instant",
            )

        # Should only call once, no backoff for non-429 errors
        assert mock_instance.chat.completions.create.call_count == 1
