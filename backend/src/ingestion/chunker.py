"""Text chunker — splits documents into overlapping chunks.

Uses a sliding window approach: each chunk is `chunk_size` characters
with `chunk_overlap` characters shared between consecutive chunks.
Overlap prevents entity mentions from being cut off at chunk boundaries.

Usage:
    from backend.src.ingestion.chunker import chunk_documents
    from backend.src.ingestion.loaders import Document

    chunks = chunk_documents(documents, chunk_size=512, chunk_overlap=50)
"""

import logging
from dataclasses import dataclass, field

from backend.src.ingestion.loaders import Document

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A single text chunk derived from a Document.

    Attributes:
        text: The chunk text content.
        chunk_index: Position of this chunk within its source document.
        metadata: Inherited from the source Document, plus chunk-specific fields.
    """

    text: str
    chunk_index: int
    metadata: dict[str, str | int] = field(default_factory=dict)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks by character count.

    The logic:
    - Start at position 0.
    - Take `chunk_size` characters.
    - Slide the window forward by `chunk_size - chunk_overlap`.
    - Repeat until we've consumed the entire text.

    Args:
        text: The raw text to split.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Characters shared between consecutive chunks.

    Returns:
        List of text strings, each at most `chunk_size` characters.
    """
    if not text or not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be less than "
            f"chunk_size ({chunk_size})"
        )

    chunks: list[str] = []
    step = chunk_size - chunk_overlap
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Split a list of Documents into Chunks.

    Each Chunk inherits the metadata of its parent Document,
    with additional fields for chunk_index and total_chunks.

    Args:
        documents: List of Document objects from the loader.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        Flat list of Chunk objects across all input documents.
    """
    all_chunks: list[Chunk] = []

    for doc in documents:
        text_chunks = chunk_text(doc.text, chunk_size, chunk_overlap)

        for i, text in enumerate(text_chunks):
            chunk_meta = {
                **doc.metadata,
                "chunk_index": i,
                "total_chunks": len(text_chunks),
            }
            all_chunks.append(
                Chunk(text=text, chunk_index=i, metadata=chunk_meta)
            )

    logger.info(
        "Chunked %d documents into %d chunks (size=%d, overlap=%d)",
        len(documents), len(all_chunks), chunk_size, chunk_overlap,
    )
    return all_chunks
