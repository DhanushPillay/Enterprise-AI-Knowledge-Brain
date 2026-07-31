"""Result reranker — scores and reorders retrieval results.

After the hybrid retriever returns a combined set of results
from vector search and graph traversal, the reranker applies
a final scoring pass to prioritize the most relevant context.

Usage:
    from backend.src.retrieval.reranker import rerank

    ranked = rerank(results, query="Who manages the ML pipeline?")
"""

import logging
from backend.src.retrieval.hybrid import RetrievalResult

logger = logging.getLogger(__name__)


def rerank(
    results: list[RetrievalResult],
    query: str,
    boost_graph: float = 1.2,
    boost_keyword_match: float = 1.5,
) -> list[RetrievalResult]:
    """Rerank retrieval results using simple heuristics.

    Applies boosts for:
    - Graph results (structural connections are high-signal)
    - Keyword overlap between query and result text

    A lightweight approach that avoids an extra LLM call.
    Can be replaced with a cross-encoder reranker later
    if accuracy demands it.

    Args:
        results: Combined retrieval results from the hybrid retriever.
        query: The original user query for keyword matching.
        boost_graph: Multiplier for graph-sourced results.
        boost_keyword_match: Multiplier when query keywords appear in text.

    Returns:
        The same results, rescored and sorted by relevance (descending).
    """
    query_words = {
        w.lower().strip("?.,!") for w in query.split() if len(w) > 3
    }

    for result in results:
        score = result.score

        # Boost graph results (structural context is usually high-signal)
        if result.source == "graph":
            score *= boost_graph

        # Boost results where query keywords appear in the text
        result_words = set(result.text.lower().split())
        overlap = query_words & result_words
        if overlap:
            keyword_ratio = len(overlap) / max(len(query_words), 1)
            score *= 1 + (keyword_ratio * (boost_keyword_match - 1))

        result.score = score

    results.sort(key=lambda r: r.score, reverse=True)
    logger.debug("Reranked %d results", len(results))
    return results
