"""Entity Extraction Agent — pulls structured entities from text chunks.

Takes chunks from the ingestion pipeline, sends them to Groq (Llama 3.1 8B)
with the entity extraction prompt, and returns structured entities and
relationships ready to be written into Neo4j.

Processes chunks in batches with delays to respect rate limits.

Usage:
    from backend.src.agents.extraction import ExtractionAgent

    agent = ExtractionAgent()
    results = await agent.extract_from_chunks(chunks)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.src.ingestion.chunker import Chunk
from backend.src.llm.groq_client import get_groq_client
from backend.src.llm.prompts import (
    ENTITY_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_SYSTEM,
)

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """A single extracted entity.

    Attributes:
        name: The entity's canonical name.
        entity_type: One of PERSON, PROJECT, TECHNOLOGY, CONCEPT, ORGANIZATION, DOCUMENT.
        description: Brief description inferred from context.
        source_chunk: Index of the chunk this entity was extracted from.
    """

    name: str
    entity_type: str
    description: str
    source_chunk: int = 0


@dataclass
class Relationship:
    """A relationship between two entities.

    Attributes:
        source: Name of the source entity.
        target: Name of the target entity.
        rel_type: Relationship type (WORKS_ON, USES, etc.).
        description: Brief description of the relationship.
    """

    source: str
    target: str
    rel_type: str
    description: str = ""


@dataclass
class ExtractionResult:
    """Combined output of entity extraction across all chunks.

    Attributes:
        entities: Deduplicated list of extracted entities.
        relationships: List of relationships between entities.
        failed_chunks: Indices of chunks where extraction failed.
    """

    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    failed_chunks: list[int] = field(default_factory=list)


class ExtractionAgent:
    """Agent that extracts entities and relationships from text chunks.

    Uses the 'extraction' pipeline Groq client (Llama 3.1 8B)
    which has a high daily limit (14,400 req/day) suitable for bulk work.

    Args:
        batch_size: Number of chunks to process before pausing.
        delay_between_batches: Seconds to wait between batches.
    """

    def __init__(
        self,
        batch_size: int = 5,
        delay_between_batches: float = 2.0,
    ) -> None:
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self._client = get_groq_client("extraction")

    async def extract_from_chunk(self, chunk: Chunk) -> tuple[list[Entity], list[Relationship]]:
        """Extract entities and relationships from a single chunk.

        Args:
            chunk: A text chunk from the chunker.

        Returns:
            Tuple of (entities, relationships) extracted from this chunk.
        """
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=chunk.text)

        try:
            result = await self._client.generate_structured(
                prompt=prompt,
                system_prompt=ENTITY_EXTRACTION_SYSTEM,
                temperature=0.0,
                max_tokens=4096,
            )

            entities = [
                Entity(
                    name=e.get("name", "Unknown"),
                    entity_type=e.get("type", "CONCEPT"),
                    description=e.get("description", ""),
                    source_chunk=chunk.chunk_index,
                )
                for e in result.get("entities", [])
                if e.get("name")
            ]

            relationships = [
                Relationship(
                    source=r.get("source", ""),
                    target=r.get("target", ""),
                    rel_type=r.get("type", "RELATED_TO"),
                    description=r.get("description", ""),
                )
                for r in result.get("relationships", [])
                if r.get("source") and r.get("target")
            ]

            logger.debug(
                "Chunk %d: extracted %d entities, %d relationships",
                chunk.chunk_index, len(entities), len(relationships),
            )
            return entities, relationships

        except Exception as e:
            logger.error("Extraction failed for chunk %d: %s", chunk.chunk_index, e)
            return [], []

    async def extract_from_chunks(self, chunks: list[Chunk]) -> ExtractionResult:
        """Extract entities from all chunks in rate-limited batches.

        Processes `batch_size` chunks, then waits `delay_between_batches`
        seconds before the next batch. This keeps us well under Groq's
        30 req/min limit.

        Args:
            chunks: List of text chunks from the chunker.

        Returns:
            ExtractionResult with deduplicated entities and all relationships.
        """
        result = ExtractionResult()
        seen_entities: dict[str, Entity] = {}

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]

            logger.info(
                "Processing batch %d/%d (%d chunks)",
                (i // self.batch_size) + 1,
                (len(chunks) + self.batch_size - 1) // self.batch_size,
                len(batch),
            )

            for chunk in batch:
                entities, relationships = await self.extract_from_chunk(chunk)

                if not entities and not relationships:
                    result.failed_chunks.append(chunk.chunk_index)
                    continue

                # Deduplicate entities by name (case-insensitive)
                for entity in entities:
                    key = entity.name.lower().strip()
                    if key not in seen_entities:
                        seen_entities[key] = entity

                result.relationships.extend(relationships)

            # Rate-limit pause between batches
            if i + self.batch_size < len(chunks):
                logger.debug("Batch pause: %.1fs", self.delay_between_batches)
                await asyncio.sleep(self.delay_between_batches)

        result.entities = list(seen_entities.values())

        logger.info(
            "Extraction complete: %d entities, %d relationships, %d failed chunks",
            len(result.entities),
            len(result.relationships),
            len(result.failed_chunks),
        )
        return result
