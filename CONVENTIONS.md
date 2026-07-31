# Coding Standards

## Python

- Python 3.11+
- ruff for formatting and linting (replaces black, isort, flake8)
- 88 char line length
- Double quotes for strings, single quotes for dict keys
- Type hints on every function signature

## Naming

| What | Style | Example |
|------|-------|---------|
| Files | snake_case | `groq_client.py` |
| Classes | PascalCase | `EntityExtractionAgent` |
| Functions | snake_case | `extract_entities()` |
| Variables | snake_case | `graph_client` |
| Constants | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE` |
| Private | _leading | `_rate_limit_lock` |
| Agents | *Agent suffix | `IngestionAgent` |
| Config | snake_case | `groq_api_key` |

## Imports

```python
# stdlib first
import os
import logging
from typing import Optional

# third-party next
import chromadb
from langgraph.graph import StateGraph
from neo4j import GraphDatabase

# local last
from src.config import settings
from src.llm.groq_client import GroqClient
```

## Functions

```python
def extract_entities(
    text: str,
    entity_types: list[str],
    confidence_threshold: float = 0.7,
) -> list[ExtractedEntity]:
    """Extract named entities from text using LLM.

    Args:
        text: Raw text to process.
        entity_types: Types to extract (e.g., ["Person", "Project"]).
        confidence_threshold: Minimum confidence to include.

    Returns:
        Extracted entities with type, name, and confidence.

    Raises:
        GroqRateLimitError: If API rate limit exceeded.
    """
    pass
```

## Agent Structure

Every agent follows this pattern:

```python
class SomeAgent:
    """Does one thing."""

    def __init__(self, config: Settings):
        self.config = config
        self.llm = GroqClient(config)
        self.logger = logging.getLogger(__name__)

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """Run the agent."""
        self.logger.info("Starting %s", self.__class__.__name__)
        # validate input
        # process (LLM call, graph query, etc.)
        # validate output
        # return result
```

## Errors

```python
try:
    result = await self.llm.generate(prompt)
except GroqRateLimitError:
    self.logger.warning("Rate limited, backing off")
    await asyncio.sleep(self.config.rate_limit_backoff)
    result = await self.llm.generate(prompt)
except GroqAPIError as e:
    self.logger.error("Groq API error: %s", e)
    raise
```

## Logging

```python
logger = logging.getLogger(__name__)

logger.info("Processing document: %s", doc_path)
logger.warning("Chunk count exceeds limit: %d > %d", count, max_count)
logger.error("Failed to extract entities: %s", str(e))
```

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_entity_extraction():
    agent = EntityExtractionAgent(config)
    result = await agent.run("John led Project Alpha in Q3.")
    assert len(result.entities) >= 2
    assert any(e.name == "John" for e in result.entities)

@pytest.mark.integration
async def test_neo4j_connection():
    """Needs running Neo4j Docker container."""
    pass
```

## Commits

Format: `type(scope): description`

| Type | When |
|------|------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation only |
| refactor | Code change, no bug or feature |
| test | Adding/updating tests |
| chore | Build, CI, deps |

Examples:
- `feat(agents): add entity extraction agent`
- `fix(graph): handle duplicate node creation`
- `docs: update architecture diagram`

## File Layout

- One main class per agent file
- Group utilities by domain
- Tests mirror source: `src/agents/query.py` → `tests/test_query_agent.py`
- Config in `src/config.py` (single source of truth)
