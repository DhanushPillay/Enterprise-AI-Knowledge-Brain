"""Groq client wrapper with strict rate-limiting and exponential backoff.

All agents MUST use this client instead of calling the Groq SDK directly.
This ensures we don't hit 429 Rate Limit errors on the free tier.
"""

import asyncio
import logging
import time
from datetime import date
from typing import Any

from groq import AsyncGroq, GroqError, RateLimitError
from groq.types.chat import ChatCompletion

from src.config import get_settings

logger = logging.getLogger(__name__)


class GroqDailyLimitError(Exception):
    """Raised when the daily request limit is exceeded."""


class RateLimiter:
    """Token bucket rate limiter for a specific Groq model.

    Tracks RPM (Requests Per Minute), TPM (Tokens Per Minute),
    and RPD (Requests Per Day).
    """

    def __init__(self, model_id: str, rpm: int, tpm: int, rpd: int):
        self.model_id = model_id
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd

        # Sliding window for RPM tracking
        self.request_times: list[float] = []

        # Token and daily tracking
        self.token_count: int = 0
        self.daily_count: int = 0
        self.last_reset_day: str = date.today().isoformat()

        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 500) -> None:
        """Wait until we can make a request without hitting limits."""
        async with self._lock:
            now = time.time()
            today = date.today().isoformat()

            # Reset daily counts if it's a new day
            if today != self.last_reset_day:
                self.daily_count = 0
                self.last_reset_day = today

            # Check daily limit first (hard stop)
            if self.daily_count >= self.rpd:
                raise GroqDailyLimitError(
                    f"Daily limit ({self.rpd}) exceeded for {self.model_id}"
                )

            # Clean up old request times (requests older than 60s)
            self.request_times = [t for t in self.request_times if now - t < 60]

            # 1. Enforce Requests Per Minute (RPM)
            if len(self.request_times) >= self.rpm:
                oldest_request = self.request_times[0]
                wait_time = 60.0 - (now - oldest_request)
                if wait_time > 0:
                    logger.debug("RPM limit reached. Waiting %.2fs", wait_time)
                    await asyncio.sleep(wait_time)
                    now = time.time()  # update time after sleep

            # 2. Enforce Tokens Per Minute (TPM)
            # If this single request would push us over, we must wait
            if self.token_count + estimated_tokens > self.tpm:
                # We wait a short burst and reset token count.
                # In a perfect token bucket, we'd wait for tokens to drip back,
                # but a simple 1s pause usually clears Groq's sliding window
                # if we are pacing ourselves. To be safe, we wait a bit longer.
                logger.debug("TPM limit reached. Pacing requests.")
                await asyncio.sleep(2.0)
                self.token_count = 0

            # Record this request
            self.request_times.append(time.time())
            self.token_count += estimated_tokens
            self.daily_count += 1


class RateLimitedGroq:
    """Wrapper around AsyncGroq that enforces rate limits per model."""

    def __init__(self, api_key: str | None = None):
        self.settings = get_settings()
        self.client = AsyncGroq(api_key=api_key or self.settings.groq_api_key)

        # One rate limiter per model, since limits are per-model
        self._limiters: dict[str, RateLimiter] = {}

    def _get_limiter(self, model: str) -> RateLimiter:
        """Get or create the rate limiter for a specific model."""
        if model not in self._limiters:
            limits = self.settings.get_model_limits(model)
            self._limiters[model] = RateLimiter(
                model_id=model,
                rpm=limits["rpm"],
                tpm=limits["tpm"],
                rpd=limits["rpd"],
            )
        return self._limiters[model]

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Roughly estimate token count: 1 token ~= 4 chars."""
        text_length = sum(len(str(m.get("content", ""))) for m in messages)
        # Add some padding for the response (assuming we generate max 1024 tokens)
        return (text_length // 4) + 1024

    async def generate(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        response_format: dict[str, str] | None = None,
    ) -> ChatCompletion:
        """Generate a response with rate limits and exponential backoff."""
        limiter = self._get_limiter(model)
        estimated_tokens = self._estimate_tokens(messages)

        max_retries = self.settings.groq_max_retries
        base_backoff = self.settings.groq_base_backoff_seconds

        for attempt in range(max_retries):
            try:
                # Wait for capacity in the token bucket
                await limiter.acquire(estimated_tokens)

                # Make the actual API call
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = await self.client.chat.completions.create(**kwargs)
                return response

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    logger.error("Max retries reached on RateLimitError.")
                    raise

                # Exponential backoff: 2s, 4s, 8s...
                wait_time = base_backoff * (2 ** attempt)
                logger.warning(
                    "Groq RateLimitError (429). Retrying in %.1fs (attempt %d/%d). %s",
                    wait_time,
                    attempt + 1,
                    max_retries,
                    str(e),
                )
                await asyncio.sleep(wait_time)

            except GroqError as e:
                # Other API errors (auth, bad request) fail immediately
                logger.error("Groq API Error: %s", str(e))
                raise

        raise RuntimeError("Unreachable")
