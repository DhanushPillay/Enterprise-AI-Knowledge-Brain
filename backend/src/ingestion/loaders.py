"""Document loaders for PDF, TXT, and Markdown files.

Each loader reads a file and returns a list of Document objects
with the raw text and metadata (filename, page number, etc.).

Usage:
    from backend.src.ingestion.loaders import load_document

    docs = load_document("report.pdf")
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A single loaded document (or page) with text and metadata.

    Attributes:
        text: The raw text content.
        metadata: Key-value pairs like filename, page_number, file_type.
    """

    text: str
    metadata: dict[str, str | int] = field(default_factory=dict)


def load_txt(file_path: Path) -> list[Document]:
    """Load a plain text file as a single Document."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return [
        Document(
            text=text,
            metadata={
                "source": file_path.name,
                "file_type": "txt",
                "char_count": len(text),
            },
        )
    ]


def load_markdown(file_path: Path) -> list[Document]:
    """Load a Markdown file as a single Document.

    Markdown is treated as plain text — we preserve headings
    and structure so the LLM can use them during extraction.
    """
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return [
        Document(
            text=text,
            metadata={
                "source": file_path.name,
                "file_type": "markdown",
                "char_count": len(text),
            },
        )
    ]


def load_pdf(file_path: Path) -> list[Document]:
    """Load a PDF file, returning one Document per page.

    Uses PyMuPDF (fitz) for fast, reliable text extraction.
    Each page becomes a separate Document with page_number metadata.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF loading. "
            "Install it: pip install PyMuPDF"
        )

    documents: list[Document] = []
    pdf = fitz.open(str(file_path))

    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text("text").strip()

        # Skip empty pages
        if not text:
            continue

        documents.append(
            Document(
                text=text,
                metadata={
                    "source": file_path.name,
                    "file_type": "pdf",
                    "page_number": page_num + 1,
                    "total_pages": len(pdf),
                    "char_count": len(text),
                },
            )
        )

    pdf.close()
    logger.info("Loaded %d pages from %s", len(documents), file_path.name)
    return documents


# ---------------------------------------------------------------------------
# Unified loader: dispatches by file extension
# ---------------------------------------------------------------------------
_LOADERS = {
    ".txt": load_txt,
    ".md": load_markdown,
    ".pdf": load_pdf,
}

SUPPORTED_EXTENSIONS = set(_LOADERS.keys())


def load_document(file_path: str | Path) -> list[Document]:
    """Load a document from disk, dispatching to the right loader.

    Args:
        file_path: Path to the file (PDF, TXT, or MD).

    Returns:
        List of Document objects (one per page for PDFs, one for TXT/MD).

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file type is not supported.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    loader = _LOADERS.get(ext)

    if loader is None:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    logger.info("Loading %s (%s)", path.name, ext)
    return loader(path)
