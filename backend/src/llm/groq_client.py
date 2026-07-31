"""Rate-limit-aware Groq LLM client with pipeline key isolation.

Every LLM call in this project goes through this module.
Each pipeline (query, extraction, security) uses its own API key
so they never starve each other under rate limits.

Usage:
    from backend.src.llm.groq_client import get_groq_client

    client = get_groq_client("query")
    answer = await client.generate("What is Neo4j?")
"""

import asyncio
import json
import logging
import time
from typing import Any, Optional

from groq import AsyncGroq, RateLimitError as GroqRateLimitError

logger = logging.getLogger(__name__)


class GroqDailyLimitError(Exception):
    """Raised when daily request limit is exhausted."""


class RateLimiter:
    """Token-bucket rate limiter scoped to a single API key.

    Tracks requests-per-minute, tokens-per-minute, and requests-per-day
    using a sliding window. Blocks the caller with asyncio.sleep
    instead of raising immediately.
    """

    def __init__(self, rpm: int = 30, tpm: int = 6000, rpd: int = 1000) -> None:
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd
        self.request_times: list[float] = []
        self.token_count: int = 0
        self.daily_count: int = 0
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 500) -> None:
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.time()

            # Sliding window: drop requests older than 60s
            self.request_times = [
                t for t in self.request_times if now - t < 60
            ]

            # Wait if at RPM ceiling
            if len(self.request_times) >= self.rpm:
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    logger.warning("RPM limit hit, waiting %.1fs", wait_time)
                    await asyncio.sleep(wait_time)

            # Wait if at TPM ceiling
            if self.token_count + estimated_tokens > self.tpm:
                logger.warning("TPM limit hit, waiting 1s")
                await asyncio.sleep(1)
                self.token_count = 0

            # Hard stop on daily limit
            if self.daily_count >= self.rpd:
                raise GroqDailyLimitError(
                    f"Daily request limit ({self.rpd}) exhausted. "
                    "Try again tomorrow or use a different API key."
                )

            self.request_times.append(time.time())
            self.token_count += estimated_tokens
            self.daily_count += 1


class GroqClient:
    """Async Groq client for a single pipeline.

    Each instance holds one API key and its own rate limiter,
    ensuring pipeline isolation.

    Args:
        api_key: The Groq API key for this pipeline.
        pipeline_name: Human-readable name for logging ('query', 'extraction', 'security').
        default_model: Default model ID to use if none specified.
        rpm: Requests per minute limit.
        tpm: Tokens per minute limit.
        rpd: Requests per day limit.
        max_retries: Number of retries on 429 errors.
        base_backoff: Base seconds for exponential backoff.
    """

    def __init__(
        self,
        api_key: str,
        pipeline_name: str,
        default_model: str = "llama-3.1-8b-instant",
        rpm: int = 30,
        tpm: int = 6000,
        rpd: int = 1000,
        max_retries: int = 3,
        base_backoff: float = 2.0,
    ) -> None:
        self.pipeline_name = pipeline_name
        self.default_model = default_model
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self._client = AsyncGroq(api_key=api_key)
        self._rate_limiter = RateLimiter(rpm=rpm, tpm=tpm, rpd=rpd)
        self._usage_requests: int = 0
        self._usage_tokens: int = 0

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a text completion with automatic rate limiting and retry.

        Args:
            prompt: The user message.
            model: Groq model ID. Falls back to self.default_model.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens: Maximum tokens in the response.
            system_prompt: Optional system message prepended to the conversation.

        Returns:
            The generated text string.
        """
        model = model or self.default_model
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                estimated_tokens = len(prompt) // 4
                await self._rate_limiter.acquire(estimated_tokens)

                response = await self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                result = response.choices[0].message.content or ""
                tokens_used = response.usage.total_tokens if response.usage else estimated_tokens
                self._usage_requests += 1
                self._usage_tokens += tokens_used

                logger.debug(
                    "[%s] Generated %d tokens with %s",
                    self.pipeline_name, tokens_used, model,
                )
                return result

            except GroqRateLimitError:
                if attempt == self.max_retries - 1:
                    raise
                wait = self.base_backoff * (2 ** attempt)
                logger.warning(
                    "[%s] Rate limited, retry %d/%d in %.1fs",
                    self.pipeline_name, attempt + 1, self.max_retries, wait,
                )
                await asyncio.sleep(wait)

        # Should never reach here, but satisfy type checker
        raise RuntimeError("Exhausted retries without success or exception")

    async def generate_structured(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a JSON-structured response.

        Wraps generate() and parses the result as JSON.
        If the LLM returns markdown-fenced JSON, strips the fences first.

        Returns:
            Parsed dictionary from the LLM's JSON output.
        """
        raw = await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                "[%s] Failed to parse LLM JSON output: %s\nRaw: %s",
                self.pipeline_name, e, raw[:500],
            )
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

    def get_usage(self) -> dict[str, int]:
        """Return cumulative usage stats for this pipeline."""
        return {
            "pipeline": self.pipeline_name,
            "total_requests": self._usage_requests,
            "total_tokens": self._usage_tokens,
        }


# ---------------------------------------------------------------------------
# Factory: creates pipeline-specific clients from Settings
# ---------------------------------------------------------------------------
_clients: dict[str, GroqClient] = {}


def get_groq_client(pipeline: str) -> GroqClient:
    """Get or create a GroqClient for a specific pipeline.

    Args:
        pipeline: One of 'query', 'extraction', 'security'.

    Returns:
        A GroqClient instance with the correct API key and rate limits.
    """
    if pipeline in _clients:
        return _clients[pipeline]

    from backend.src.config import get_settings, GroqModelConfig

    cfg = get_settings()
    api_key = cfg.get_groq_key_for_pipeline(pipeline)

    # Choose default model and limits per pipeline
    pipeline_config = {
        "query": {
            "model": GroqModelConfig.LLAMA_70B,
            "limits": GroqModelConfig.LIMITS[GroqModelConfig.LLAMA_70B],
        },
        "extraction": {
            "model": GroqModelConfig.LLAMA_8B,
            "limits": GroqModelConfig.LIMITS[GroqModelConfig.LLAMA_8B],
        },
        "security": {
            "model": GroqModelConfig.LLAMA_8B,
            "limits": GroqModelConfig.LIMITS[GroqModelConfig.LLAMA_8B],
        },
    }

    pcfg = pipeline_config[pipeline]
    client = GroqClient(
        api_key=api_key,
        pipeline_name=pipeline,
        default_model=pcfg["model"],
        rpm=pcfg["limits"]["rpm"],
        tpm=pcfg["limits"]["tpm"],
        rpd=pcfg["limits"]["rpd"],
        max_retries=cfg.groq_max_retries,
        base_backoff=cfg.groq_base_backoff_seconds,
    )
    _clients[pipeline] = client
    return client
