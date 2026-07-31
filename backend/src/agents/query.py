"""Query Agent — answers user questions using retrieved context.

Takes a user question, retrieves relevant context from the hybrid
retriever, and generates an answer using Groq (Llama 3.3 70B).

Usage:
    from backend.src.agents.query import QueryAgent

    agent = QueryAgent()
    response = await agent.answer("Who manages the ML pipeline?")
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.src.llm.groq_client import get_groq_client
from backend.src.llm.prompts import QUERY_ANSWER_PROMPT, QUERY_ANSWER_SYSTEM
from backend.src.retrieval.hybrid import HybridRetriever, RetrievalResult
from backend.src.retrieval.reranker import rerank

logger = logging.getLogger(__name__)


@dataclass
class QueryResponse:
    """Structured response to a user query.

    Attributes:
        answer: The generated answer text.
        reasoning: Step-by-step reasoning trace for transparency.
        sources: Retrieved context chunks used to form the answer.
        is_safe: Whether the query passed security checks.
    """

    answer: str
    reasoning: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    is_safe: bool = True


class QueryAgent:
    """Agent that answers user questions with citations.

    Uses the 'query' pipeline Groq client (Llama 3.3 70B) for
    high-quality reasoning and answer generation.

    Args:
        top_k: Number of context chunks to use in the prompt.
    """

    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k
        self._client = get_groq_client("query")
        self._retriever = HybridRetriever(top_k=top_k)

    async def answer(self, question: str) -> QueryResponse:
        """Answer a user question using hybrid retrieval + LLM.

        The pipeline:
        1. Retrieve relevant context from vector store + graph.
        2. Rerank results for quality.
        3. Format context into the LLM prompt.
        4. Generate answer with Llama 3.3 70B.

        Args:
            question: The user's question.

        Returns:
            QueryResponse with the answer, reasoning, and sources.
        """
        reasoning: list[str] = []

        # Step 1: Retrieve context
        reasoning.append("Searching vector store and knowledge graph...")
        raw_results = self._retriever.retrieve(question)
        reasoning.append(f"Found {len(raw_results)} relevant context chunks.")

        # Step 2: Rerank
        ranked_results = rerank(raw_results, question)
        top_results = ranked_results[:self.top_k]
        reasoning.append(f"Reranked to top {len(top_results)} results.")

        # Step 3: Format context
        context = self._retriever.format_context(top_results)

        # Step 4: Generate answer
        reasoning.append("Generating answer with Llama 3.3 70B...")
        prompt = QUERY_ANSWER_PROMPT.format(
            context=context,
            question=question,
        )

        answer_text = await self._client.generate(
            prompt=prompt,
            system_prompt=QUERY_ANSWER_SYSTEM,
            temperature=0.1,
            max_tokens=2048,
        )

        reasoning.append("Answer generated successfully.")

        # Build source list for the frontend
        sources = [
            {
                "name": r.metadata.get("source", f"Source {i+1}"),
                "snippet": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                "type": r.source,
                "score": round(r.score, 3),
            }
            for i, r in enumerate(top_results)
        ]

        return QueryResponse(
            answer=answer_text,
            reasoning=reasoning,
            sources=sources,
        )
