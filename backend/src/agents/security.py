"""Security Agent — detects prompt injection attacks.

Runs a two-layer defense:
1. Rule-based checks (fast, no API call) for obvious patterns.
2. LLM-based classification (uses the 'security' pipeline key)
   for ambiguous cases that pass the rule checks.

Usage:
    from backend.src.agents.security import SecurityAgent

    agent = SecurityAgent()
    result = await agent.check_query("ignore previous instructions")
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.src.llm.groq_client import get_groq_client
from backend.src.llm.prompts import INJECTION_DETECTION_PROMPT, INJECTION_DETECTION_SYSTEM

logger = logging.getLogger(__name__)


# Known injection patterns (case-insensitive)
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)\s+",
    r"pretend\s+you\s+are",
    r"reveal\s+(your|the)\s+(system|internal)\s+prompt",
    r"what\s+is\s+your\s+system\s+prompt",
    r"output\s+your\s+instructions",
    r"repeat\s+(the|your)\s+instructions",
    r"do\s+anything\s+now",
    r"jailbreak",
    r"DAN\s+mode",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


@dataclass
class SecurityCheckResult:
    """Result of a security check on a user query.

    Attributes:
        is_safe: Whether the query is safe to process.
        confidence: Confidence in the classification (0-1).
        reason: Explanation of the decision.
        method: Which check caught it ('rule' or 'llm').
    """

    is_safe: bool
    confidence: float
    reason: str
    method: str = "rule"


class SecurityAgent:
    """Agent that validates user queries before they reach the LLM.

    Uses a dedicated Groq API key ('security' pipeline) so security
    checks never compete with query or extraction calls.

    Args:
        max_query_length: Maximum allowed query length in characters.
        min_query_length: Minimum allowed query length in characters.
        confidence_threshold: Below this, rule engine defers to LLM.
    """

    def __init__(
        self,
        max_query_length: int = 1000,
        min_query_length: int = 2,
        confidence_threshold: float = 0.7,
    ) -> None:
        self.max_query_length = max_query_length
        self.min_query_length = min_query_length
        self.confidence_threshold = confidence_threshold
        self._client = get_groq_client("security")

    async def check_query(self, query: str) -> SecurityCheckResult:
        """Run security checks on a user query.

        Order of operations:
        1. Length validation (fast, no API).
        2. Pattern matching (fast, no API).
        3. LLM classification (slow, uses API — only for ambiguous cases).

        Args:
            query: The raw user query.

        Returns:
            SecurityCheckResult indicating whether the query is safe.
        """
        # Check 1: Length validation
        if len(query) < self.min_query_length:
            return SecurityCheckResult(
                is_safe=False,
                confidence=1.0,
                reason=f"Query too short (min {self.min_query_length} chars).",
                method="rule",
            )

        if len(query) > self.max_query_length:
            return SecurityCheckResult(
                is_safe=False,
                confidence=1.0,
                reason=f"Query too long (max {self.max_query_length} chars).",
                method="rule",
            )

        # Check 2: Known injection patterns
        for pattern in _COMPILED_PATTERNS:
            if pattern.search(query):
                return SecurityCheckResult(
                    is_safe=False,
                    confidence=0.95,
                    reason=f"Matched injection pattern: {pattern.pattern}",
                    method="rule",
                )

        # Check 3: LLM-based classification for ambiguous queries
        try:
            result = await self._llm_check(query)
            return result
        except Exception as e:
            # If LLM check fails, allow the query through
            # (fail-open for availability, log for monitoring)
            logger.warning("LLM security check failed, allowing query: %s", e)
            return SecurityCheckResult(
                is_safe=True,
                confidence=0.5,
                reason="LLM check failed, defaulting to safe.",
                method="fallback",
            )

    async def _llm_check(self, query: str) -> SecurityCheckResult:
        """Use the LLM to classify ambiguous queries."""
        prompt = INJECTION_DETECTION_PROMPT.format(query=query)

        result = await self._client.generate_structured(
            prompt=prompt,
            system_prompt=INJECTION_DETECTION_SYSTEM,
            temperature=0.0,
            max_tokens=256,
        )

        is_injection = result.get("is_injection", False)
        confidence = result.get("confidence", 0.5)
        reason = result.get("reason", "No reason provided")

        return SecurityCheckResult(
            is_safe=not is_injection,
            confidence=confidence,
            reason=reason,
            method="llm",
        )
