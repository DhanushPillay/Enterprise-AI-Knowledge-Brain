"""Graph Builder Agent — writes extracted entities into Neo4j.

Takes the output of the ExtractionAgent (entities + relationships)
and creates the corresponding nodes and edges in Neo4j.

This is the bridge between the LLM extraction pipeline and
the knowledge graph.

Usage:
    from backend.src.agents.graph_builder import GraphBuilderAgent

    agent = GraphBuilderAgent()
    stats = agent.build_from_extraction(extraction_result)
"""

import logging
from dataclasses import dataclass

from backend.src.agents.extraction import ExtractionResult
from backend.src.graph.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


@dataclass
class BuildStats:
    """Statistics from a graph build operation.

    Attributes:
        entities_written: Number of entity nodes created/updated.
        relationships_written: Number of relationships created.
        errors: Number of write failures.
    """

    entities_written: int = 0
    relationships_written: int = 0
    errors: int = 0


class GraphBuilderAgent:
    """Agent that writes extracted entities and relationships to Neo4j.

    Connects to Neo4j via the centralized client and uses MERGE
    operations for idempotent writes (safe to re-run).
    """

    def __init__(self) -> None:
        self._client = get_neo4j_client()

    def build_from_extraction(self, result: ExtractionResult) -> BuildStats:
        """Write all entities and relationships from an extraction result.

        Entities are written first (since relationships reference them).
        Failures are logged but don't halt the process — partial
        graph builds are better than no graph at all.

        Args:
            result: The output of ExtractionAgent.extract_from_chunks().

        Returns:
            BuildStats with counts of successful writes and errors.
        """
        stats = BuildStats()

        # Step 1: Write entity nodes
        for entity in result.entities:
            try:
                self._client.merge_entity(
                    name=entity.name,
                    entity_type=entity.entity_type,
                    description=entity.description,
                    source_chunk=entity.source_chunk,
                )
                stats.entities_written += 1
            except Exception as e:
                logger.error("Failed to write entity '%s': %s", entity.name, e)
                stats.errors += 1

        # Step 2: Write relationships (entities must exist first)
        for rel in result.relationships:
            try:
                self._client.create_relationship(
                    source_name=rel.source,
                    target_name=rel.target,
                    rel_type=rel.rel_type,
                    description=rel.description,
                )
                stats.relationships_written += 1
            except Exception as e:
                logger.error(
                    "Failed to write relationship '%s' -> '%s': %s",
                    rel.source, rel.target, e,
                )
                stats.errors += 1

        logger.info(
            "Graph build complete: %d entities, %d relationships, %d errors",
            stats.entities_written, stats.relationships_written, stats.errors,
        )
        return stats
