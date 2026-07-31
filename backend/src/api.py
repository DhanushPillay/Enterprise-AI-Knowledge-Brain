"""Enterprise AI Knowledge Brain — FastAPI Server.

The main API that the Next.js frontend talks to.
Routes user queries through the security agent, then the query agent.
Also exposes endpoints for document ingestion and graph stats.

Usage:
    uvicorn backend.src.api:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise AI Knowledge Brain API",
    description="Multi-agent knowledge graph Q&A system",
    version="0.1.0",
)

# Allow Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    reasoning: list[str]
    sources: list[dict]
    is_safe: bool = True


class IngestResponse(BaseModel):
    filename: str
    chunks_created: int
    entities_extracted: int
    relationships_extracted: int
    graph_entities_written: int
    graph_relationships_written: int


class GraphStatsResponse(BaseModel):
    nodes: list[dict]
    relationships: list[dict]
    total_chunks: int


# ---------------------------------------------------------------------------
# Chat Endpoint
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Process a user query through security → retrieval → LLM answer.

    The full pipeline:
    1. Security Agent checks for prompt injection.
    2. If safe, Query Agent retrieves context and generates answer.
    3. Returns the answer with reasoning trace and sources.
    """
    from backend.src.agents.security import SecurityAgent
    from backend.src.agents.query import QueryAgent

    # Step 1: Security check
    security = SecurityAgent()
    check = await security.check_query(request.query)

    if not check.is_safe:
        return ChatResponse(
            answer=f"⚠️ Query blocked: {check.reason}",
            reasoning=[
                f"Security check: BLOCKED ({check.method})",
                f"Confidence: {check.confidence:.0%}",
                f"Reason: {check.reason}",
            ],
            sources=[],
            is_safe=False,
        )

    # Step 2: Answer the question
    query_agent = QueryAgent()
    response = await query_agent.answer(request.query)

    return ChatResponse(
        answer=response.answer,
        reasoning=response.reasoning,
        sources=response.sources,
        is_safe=True,
    )


# ---------------------------------------------------------------------------
# Document Ingestion Endpoint
# ---------------------------------------------------------------------------
@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(file: UploadFile = File(...)) -> IngestResponse:
    """Upload and ingest a document into the knowledge graph.

    The pipeline:
    1. Save uploaded file to a temp directory.
    2. Load and preprocess the document.
    3. Chunk the text.
    4. Store chunks in ChromaDB (vector store).
    5. Extract entities with Groq LLM.
    6. Write entities and relationships to Neo4j.
    """
    from backend.src.ingestion.loaders import load_document, SUPPORTED_EXTENSIONS
    from backend.src.ingestion.preprocessor import preprocess
    from backend.src.ingestion.chunker import chunk_documents
    from backend.src.retrieval.vector_store import get_vector_store
    from backend.src.agents.extraction import ExtractionAgent
    from backend.src.agents.graph_builder import GraphBuilderAgent

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Load document
        documents = load_document(tmp_path)

        # Preprocess
        for doc in documents:
            doc.text = preprocess(doc.text)
            doc.metadata["source"] = file.filename

        # Chunk
        from backend.src.config import get_settings
        cfg = get_settings()
        chunks = chunk_documents(
            documents,
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
        )

        # Store in vector store
        vector_store = get_vector_store()
        vector_store.add_chunks(chunks)

        # Extract entities
        extraction_agent = ExtractionAgent()
        extraction_result = await extraction_agent.extract_from_chunks(chunks)

        # Write to graph
        graph_builder = GraphBuilderAgent()
        build_stats = graph_builder.build_from_extraction(extraction_result)

        return IngestResponse(
            filename=file.filename,
            chunks_created=len(chunks),
            entities_extracted=len(extraction_result.entities),
            relationships_extracted=len(extraction_result.relationships),
            graph_entities_written=build_stats.entities_written,
            graph_relationships_written=build_stats.relationships_written,
        )

    finally:
        # Clean up temp file
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Graph Stats Endpoint
# ---------------------------------------------------------------------------
@app.get("/graph/stats", response_model=GraphStatsResponse)
async def graph_stats_endpoint() -> GraphStatsResponse:
    """Return node and relationship counts for the admin dashboard."""
    from backend.src.graph.neo4j_client import get_neo4j_client
    from backend.src.retrieval.vector_store import get_vector_store

    neo4j = get_neo4j_client()
    stats = neo4j.get_stats()
    vector_store = get_vector_store()

    return GraphStatsResponse(
        nodes=stats["nodes"],
        relationships=stats["relationships"],
        total_chunks=vector_store.count(),
    )


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "Enterprise AI Knowledge Brain"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.api:app", host="0.0.0.0", port=8000, reload=True)
