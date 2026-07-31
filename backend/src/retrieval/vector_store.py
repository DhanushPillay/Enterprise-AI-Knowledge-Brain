"""ChromaDB vector store — stores and searches document chunk embeddings.

Uses sentence-transformers for local embedding generation (no API calls)
and ChromaDB for persistent vector storage and similarity search.

Usage:
    from backend.src.retrieval.vector_store import get_vector_store

    store = get_vector_store()
    store.add_chunks(chunks)
    results = store.search("What is Neo4j?", top_k=5)
"""

import logging
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.src.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-backed vector store with local sentence-transformer embeddings.

    Chunks are embedded locally using all-MiniLM-L6-v2 (384 dims).
    No external API calls needed — runs entirely on CPU.

    Args:
        persist_dir: Directory for ChromaDB's SQLite storage.
        collection_name: Name of the ChromaDB collection.
        embedding_model: Sentence-transformer model name.
    """

    def __init__(
        self,
        persist_dir: str = ".chroma",
        collection_name: str = "knowledge_chunks",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)

        # Use sentence-transformers for embedding
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
        )

        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "VectorStore initialized: %s (%d existing documents)",
            collection_name,
            self._collection.count(),
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add text chunks to the vector store.

        Each chunk is embedded and stored with its metadata.
        IDs are generated from source filename + chunk index
        to ensure idempotent re-ingestion.

        Args:
            chunks: List of Chunk objects from the chunker.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            source = chunk.metadata.get("source", "unknown")
            chunk_id = f"{source}__chunk_{chunk.chunk_index}"

            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                k: str(v) for k, v in chunk.metadata.items()
            })

        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info("Added %d chunks to vector store", len(chunks))
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Search for chunks semantically similar to the query.

        Args:
            query: The search query text.
            top_k: Number of results to return.
            where: Optional metadata filter (ChromaDB where clause).

        Returns:
            List of dicts with keys: text, metadata, distance.
        """
        kwargs: dict = {
            "query_texts": [query],
            "n_results": min(top_k, self._collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        output = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })

        logger.debug("Vector search for '%s': %d results", query[:50], len(output))
        return output

    def count(self) -> int:
        """Return the total number of stored chunks."""
        return self._collection.count()

    def delete_by_source(self, source: str) -> None:
        """Delete all chunks from a specific source document."""
        self._collection.delete(where={"source": source})
        logger.info("Deleted chunks from source: %s", source)


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore instance."""
    global _store
    if _store is None:
        from backend.src.config import get_settings
        cfg = get_settings()
        _store = VectorStore(
            persist_dir=cfg.chroma_persist_dir,
            collection_name=cfg.chroma_collection_name,
            embedding_model=cfg.embedding_model,
        )
    return _store
