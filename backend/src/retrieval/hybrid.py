"""Hybrid retriever — combines vector search with graph traversal.

When answering a question, we don't rely on just one source.
The hybrid retriever queries both ChromaDB (semantic similarity)
and Neo4j (structural connections) then merges the results.

Usage:
    from backend.src.retrieval.hybrid import HybridRetriever

    retriever = HybridRetriever()
    context = retriever.retrieve("Who manages the ML pipeline?")
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.src.retrieval.vector_store import get_vector_store
from backend.src.graph.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """A single piece of retrieved context.

    Attributes:
        text: The relevant text content.
        source: Where this came from ('vector' or 'graph').
        score: Relevance score (0-1, higher is better).
        metadata: Additional context (source file, entity names, etc.).
    """

    text: str
    source: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


class HybridRetriever:
    """Retriever that combines vector similarity and graph traversal.

    The retrieval strategy:
    1. Vector search: Find chunks semantically similar to the query.
    2. Entity extraction: Identify entity names mentioned in the query.
    3. Graph search: Find neighbors and paths for those entities.
    4. Merge: Combine and deduplicate results from both sources.

    Args:
        vector_weight: Weight for vector search results (0-1).
        graph_weight: Weight for graph search results (0-1).
        top_k: Number of results to return from each source.
    """

    def __init__(
        self,
        vector_weight: float = 0.5,
        graph_weight: float = 0.5,
        top_k: int = 10,
    ) -> None:
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
        self.top_k = top_k
        self._vector_store = get_vector_store()
        self._neo4j = get_neo4j_client()

    def retrieve(self, query: str) -> list[RetrievalResult]:
        """Retrieve relevant context for a query from both sources.

        Args:
            query: The user's question.

        Returns:
            List of RetrievalResult objects, sorted by score (descending).
        """
        results: list[RetrievalResult] = []

        # Source 1: Vector search (semantic similarity)
        vector_results = self._vector_search(query)
        results.extend(vector_results)

        # Source 2: Graph search (structural connections)
        graph_results = self._graph_search(query)
        results.extend(graph_results)

        # Sort by score (highest first) and deduplicate
        results = self._deduplicate(results)
        results.sort(key=lambda r: r.score, reverse=True)

        logger.info(
            "Hybrid retrieval: %d vector + %d graph = %d total results",
            len(vector_results), len(graph_results), len(results),
        )
        return results[:self.top_k]

    def _vector_search(self, query: str) -> list[RetrievalResult]:
        """Run semantic similarity search via ChromaDB."""
        try:
            raw_results = self._vector_store.search(query, top_k=self.top_k)

            return [
                RetrievalResult(
                    text=r["text"],
                    source="vector",
                    # ChromaDB returns distance (lower = closer).
                    # Convert to score (higher = better).
                    score=(1 - r["distance"]) * self.vector_weight,
                    metadata=r.get("metadata", {}),
                )
                for r in raw_results
            ]
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            return []

    def _graph_search(self, query: str) -> list[RetrievalResult]:
        """Search the knowledge graph for entities mentioned in the query.

        Uses a simple heuristic: split the query into words and search
        for each word as a potential entity name. More sophisticated
        entity detection can be added later.
        """
        results: list[RetrievalResult] = []

        try:
            # Extract potential entity names (words with 3+ chars)
            words = [w.strip("?.,!") for w in query.split() if len(w) > 3]

            seen_entities: set[str] = set()

            for word in words:
                entities = self._neo4j.find_entity(word, limit=3)

                for entity in entities:
                    name = entity.get("name", "")
                    if name.lower() in seen_entities:
                        continue
                    seen_entities.add(name.lower())

                    # Get neighbors of this entity
                    neighbors = self._neo4j.find_neighbors(name, limit=5)

                    # Build context text from the entity and its neighbors
                    context_parts = [
                        f"{name} ({entity.get('type', 'Unknown')}): "
                        f"{entity.get('description', 'No description')}"
                    ]
                    for n in neighbors:
                        context_parts.append(
                            f"  - {n.get('relationship', '?')} -> "
                            f"{n.get('target', '?')} ({n.get('target_type', '?')})"
                        )

                    results.append(
                        RetrievalResult(
                            text="\n".join(context_parts),
                            source="graph",
                            score=self.graph_weight * 0.8,
                            metadata={"entity": name, "type": entity.get("type", "")},
                        )
                    )

        except Exception as e:
            logger.error("Graph search failed: %s", e)

        return results

    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Remove duplicate results based on text content."""
        seen: set[str] = set()
        unique: list[RetrievalResult] = []

        for r in results:
            # Use first 100 chars as dedup key
            key = r.text[:100].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique

    def format_context(self, results: list[RetrievalResult]) -> str:
        """Format retrieval results into a context string for the LLM.

        Args:
            results: List of RetrievalResult objects.

        Returns:
            A formatted string ready to inject into the LLM prompt.
        """
        if not results:
            return "No relevant context found."

        parts = []
        for i, r in enumerate(results, 1):
            source_label = f"[{r.source.upper()}]"
            parts.append(f"--- Source {i} {source_label} (score: {r.score:.2f}) ---\n{r.text}")

        return "\n\n".join(parts)
