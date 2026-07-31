"""Text preprocessor — cleans and normalizes raw document text.

Runs before chunking to remove noise that would confuse the LLM.
Handles common issues in extracted text: excessive whitespace,
page headers/footers, encoding artifacts, etc.

Usage:
    from backend.src.ingestion.preprocessor import preprocess

    clean_text = preprocess(raw_text)
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


def normalize_unicode(text: str) -> str:
    """Normalize unicode characters to their canonical form.

    Converts fancy quotes, em-dashes, and other typographic
    characters to their ASCII equivalents where possible.
    """
    # NFKD decomposition: breaks composed characters apart
    text = unicodedata.normalize("NFKD", text)

    # Replace common typographic characters
    replacements = {
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2013": "-",   # en-dash
        "\u2014": "-",   # em-dash
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
        "\u200b": "",    # zero-width space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces or newlines.

    Preserves paragraph breaks (double newlines) but removes
    triple+ newlines and runs of spaces/tabs.
    """
    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Collapse runs of spaces (not newlines) into single space
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3+ newlines into double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_page_artifacts(text: str) -> str:
    """Remove common PDF extraction artifacts.

    Strips page numbers, headers/footers patterns, and
    form-feed characters that PDF extractors leave behind.
    """
    # Remove form-feed characters
    text = text.replace("\f", "\n")

    # Remove standalone page numbers (lines with just a number)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Remove "Page X of Y" patterns
    text = re.sub(
        r"(?i)page\s+\d+\s*(of\s+\d+)?",
        "",
        text,
    )

    return text


def remove_urls(text: str) -> str:
    """Remove URLs — they add noise without semantic value for extraction."""
    return re.sub(r"https?://\S+", "", text)


def preprocess(text: str) -> str:
    """Full preprocessing pipeline for raw document text.

    Order matters:
    1. Unicode normalization (fix encoding weirdness)
    2. Page artifact removal (strip PDF junk)
    3. URL removal (reduce noise)
    4. Whitespace collapse (clean up the result)

    Args:
        text: Raw text from a document loader.

    Returns:
        Cleaned text ready for chunking and LLM processing.
    """
    if not text:
        return ""

    text = normalize_unicode(text)
    text = remove_page_artifacts(text)
    text = remove_urls(text)
    text = collapse_whitespace(text)

    logger.debug("Preprocessed text: %d chars", len(text))
    return text
