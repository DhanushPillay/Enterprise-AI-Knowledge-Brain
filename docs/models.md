# Model Selection

Which Groq model to use when. All free, but rate limits differ.

---

## Llama 3.3 70B Versatile

**Model ID:** `llama-3.3-70b-versatile`

Use this for anything that needs reasoning: answering questions, generating responses with citations, handling ambiguous text.

| Limit | Value |
|-------|-------|
| Requests/min | 30 |
| Tokens/min | 6,000 |
| Requests/day | 1,000 |
| Context window | 128K tokens |
| Max output | 32,768 tokens |

It's slower than the 8B model, but smarter. Use it when accuracy matters more than speed.

```python
answer = await groq_client.generate(
    prompt=f"Answer the question using ONLY the provided context.\n\nContext:\n{context}\n\nQuestion: {question}",
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=2048,
)
```

---

## Llama 3.1 8B Instant

**Model ID:** `llama-3.1-8b-instant`

Use this for bulk work: entity extraction, text classification, prompt injection detection. Fast and has a much higher daily limit.

| Limit | Value |
|-------|-------|
| Requests/min | 30 |
| Tokens/min | 6,000 |
| Requests/day | 14,400 |
| Context window | 128K tokens |
| Max output | 8,192 tokens |

Roughly 2x faster than the 70B. The daily limit is 14x higher, which matters when you're processing lots of documents.

```python
entities = await groq_client.generate_structured(
    prompt=f"Extract entities from:\n{text}",
    schema=entity_schema,
    model="llama-3.1-8b-instant",
    temperature=0.0,
)
```

---

## Embedding Model (Local)

**Model:** `all-MiniLM-L6-v2` (via sentence-transformers)

Runs on your machine. No API calls, no rate limits.

- 384-dimensional embeddings
- ~80MB model size
- Fast on CPU

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks, show_progress_bar=True)
```

---

## Which model when

```
Task incoming
    │
    ├─ Answering a question?
    │   └─ Yes → Llama 3.3 70B
    │
    ├─ Extracting entities?
    │   ├─ More than 100 chunks → Llama 3.1 8B
    │   └─ Fewer than 100 → Llama 3.3 70B
    │
    ├─ Classifying text?
    │   └─ Yes → Llama 3.1 8B
    │
    ├─ Embedding?
    │   └─ Yes → sentence-transformers (local)
    │
    └─ Default → Llama 3.1 8B (faster, cheaper)
```

---

## Rate Limiting

### Token bucket

```python
import asyncio
import time

class RateLimiter:
    """Token bucket rate limiter for Groq API."""

    def __init__(
        self,
        rpm: int = 30,
        tpm: int = 6000,
        rpd: int = 1000,
    ):
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd
        self.request_times: list[float] = []
        self.token_count: int = 0
        self.daily_count: int = 0
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 500) -> None:
        """Wait until we can make a request."""
        async with self._lock:
            now = time.time()

            # Clean up old request times (sliding window)
            self.request_times = [
                t for t in self.request_times if now - t < 60
            ]

            # Wait if at RPM limit
            if len(self.request_times) >= self.rpm:
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # Wait if at TPM limit
            if self.token_count + estimated_tokens > self.tpm:
                await asyncio.sleep(1)
                self.token_count = 0

            # Check daily limit
            if self.daily_count >= self.rpd:
                raise GroqDailyLimitError("Daily request limit exceeded")

            # Record this request
            self.request_times.append(time.time())
            self.token_count += estimated_tokens
            self.daily_count += 1
```

### Retry with backoff

```python
async def generate_with_retry(
    self,
    prompt: str,
    model: str,
    max_retries: int = 3,
) -> str:
    """Generate with exponential backoff on rate limits."""
    for attempt in range(max_retries):
        try:
            await self.rate_limiter.acquire(len(prompt) // 4)
            return await self._call_groq(prompt, model)
        except GroqRateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt * 2  # 2, 4, 8 seconds
            logger.warning(
                "Rate limited, retrying in %ds (attempt %d/%d)",
                wait_time, attempt + 1, max_retries,
            )
            await asyncio.sleep(wait_time)
```

---

## Saving tokens

A few things that help:

- Batch entity extraction (groups of 5 chunks, 2-second delay between batches)
- Keep prompts short
- Use JSON schema constraints for structured output
- Don't repeat context in multi-turn conversations
- Cache common entity types

```python
async def extract_entities_batched(
    self,
    chunks: list[Chunk],
    batch_size: int = 5,
    delay_between_batches: float = 2.0,
) -> list[Entity]:
    """Extract entities in batches to stay within rate limits."""
    all_entities = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        result = await self._extract_batch(batch)
        all_entities.extend(result.entities)

        if i + batch_size < len(chunks):
            await asyncio.sleep(delay_between_batches)

    return all_entities
```

---

## Tracking usage

Keep an eye on how many requests and tokens you've burned:

```python
class UsageTracker:
    def __init__(self):
        self.daily_requests: dict[str, int] = {}
        self.daily_tokens: dict[str, int] = {}

    def log_request(self, model: str, tokens: int) -> None:
        today = date.today().isoformat()
        key = f"{today}:{model}"
        self.daily_requests[key] = self.daily_requests.get(key, 0) + 1
        self.daily_tokens[key] = self.daily_tokens.get(key, 0) + tokens

    def get_usage(self, model: str) -> dict:
        today = date.today().isoformat()
        key = f"{today}:{model}"
        return {
            "requests": self.daily_requests.get(key, 0),
            "tokens": self.daily_tokens.get(key, 0),
        }
```
