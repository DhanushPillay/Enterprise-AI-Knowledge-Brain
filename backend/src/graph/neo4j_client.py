"""Neo4j client — all graph database operations go through here.

Wraps the Neo4j Python driver with async-friendly methods.
No other module should import neo4j directly.

Usage:
    from backend.src.graph.neo4j_client import get_neo4j_client

    client = get_neo4j_client()
    await client.merge_entity("Neo4j", "Technology", "Graph database")
"""

import logging
from typing import Any, Optional

from neo4j import GraphDatabase, Driver

from backend.src.graph.schema import NodeType, RelationType, resolve_node_type, resolve_rel_type
from backend.src.graph import queries

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Synchronous Neo4j client wrapping the official driver.

    Neo4j's Python driver is synchronous, so we use sync methods
    and call them from async context via asyncio.to_thread when needed.

    Args:
        uri: Bolt connection URI (e.g. bolt://localhost:7687).
        user: Neo4j username.
        password: Neo4j password.
    """

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Neo4j client initialized: %s", uri)

    def close(self) -> None:
        """Close the driver connection."""
        self._driver.close()
        logger.info("Neo4j connection closed")

    def verify_connection(self) -> bool:
        """Check that Neo4j is reachable."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error("Neo4j connection failed: %s", e)
            return False

    def _run_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results as a list of dicts."""
        with self._driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def merge_entity(
        self,
        name: str,
        entity_type: str,
        description: str = "",
        source_chunk: int = 0,
    ) -> None:
        """Create or update an entity node in the graph.

        Uses MERGE so repeated calls are idempotent.
        The node label is determined by entity_type.

        Args:
            name: The entity's canonical name.
            entity_type: Raw type string from extraction (mapped via schema).
            description: Brief description of the entity.
            source_chunk: Index of the source chunk.
        """
        node_type = resolve_node_type(entity_type)
        query = queries.MERGE_ENTITY.format(label=node_type.value)

        self._run_query(query, {
            "name": name,
            "description": description,
            "source_chunk": source_chunk,
        })
        logger.debug("Merged entity: %s (%s)", name, node_type.value)

    def create_relationship(
        self,
        source_name: str,
        target_name: str,
        rel_type: str,
        description: str = "",
    ) -> None:
        """Create a relationship between two existing entities.

        Uses MERGE so repeated calls are idempotent.

        Args:
            source_name: Name of the source entity.
            target_name: Name of the target entity.
            rel_type: Raw relationship type string (mapped via schema).
            description: Brief description of the relationship.
        """
        resolved_type = resolve_rel_type(rel_type)
        query = queries.CREATE_RELATIONSHIP.format(rel_type=resolved_type.value)

        self._run_query(query, {
            "source_name": source_name,
            "target_name": target_name,
            "description": description,
        })
        logger.debug(
            "Created relationship: %s -[%s]-> %s",
            source_name, resolved_type.value, target_name,
        )

    def find_entity(self, name: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for entities by name (case-insensitive substring match)."""
        return self._run_query(queries.FIND_ENTITY_BY_NAME, {
            "name": name,
            "limit": limit,
        })

    def find_neighbors(self, name: str, limit: int = 20) -> list[dict[str, Any]]:
        """Find all entities connected to a given entity."""
        return self._run_query(queries.FIND_NEIGHBORS, {
            "name": name,
            "limit": limit,
        })

    def find_path(
        self,
        source_name: str,
        target_name: str,
        max_depth: int = 4,
    ) -> list[dict[str, Any]]:
        """Find the shortest path between two entities."""
        query = queries.FIND_PATH_BETWEEN.format(max_depth=max_depth)
        return self._run_query(query, {
            "source_name": source_name,
            "target_name": target_name,
        })

    def find_by_type(self, node_type: str, limit: int = 50) -> list[dict[str, Any]]:
        """Find all entities of a specific type."""
        resolved = resolve_node_type(node_type)
        query = queries.FIND_ENTITIES_BY_TYPE.format(label=resolved.value)
        return self._run_query(query, {"limit": limit})

    def get_stats(self) -> dict[str, list[dict[str, Any]]]:
        """Get node and relationship counts for the dashboard."""
        return {
            "nodes": self._run_query(queries.GET_GRAPH_STATS),
            "relationships": self._run_query(queries.GET_RELATIONSHIP_STATS),
        }

    def get_subgraph(self, name: str, depth: int = 2) -> list[dict[str, Any]]:
        """Get a subgraph centered around an entity (for visualization)."""
        query = queries.SUBGRAPH_AROUND_ENTITY.format(depth=depth)
        return self._run_query(query, {"name": name})


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------
_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create the global Neo4j client."""
    global _client
    if _client is None:
        from backend.src.config import get_settings
        cfg = get_settings()
        _client = Neo4jClient(
            uri=cfg.neo4j_uri,
            user=cfg.neo4j_user,
            password=cfg.neo4j_password,
        )
    return _client
