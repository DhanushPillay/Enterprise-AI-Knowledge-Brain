# Architecture

## What the system does

Reads org docs (PDF, TXT, Markdown, code), pulls out entities and relationships using LLMs, stores them as a knowledge graph in Neo4j, and answers questions about the data. Mixes vector search with graph traversal. Has security to block prompt injection.

## The big picture

```
                    ┌─────────────────────┐
                    │   Streamlit UI      │
                    │   (app.py)          │
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │   Security Agent    │
                    │   (prompt_guard)    │
                    └────────┬────────────┘
                             │
               ┌──────────────▼──────────────┐
               │   LangGraph Orchestrator    │
               │   (StateGraph)              │
               └──┬────┬────┬────┬────┬─────┘
                  │    │    │    │    │
     ┌────────────▼┐ ┌─▼──┐ ┌▼───┐ ┌▼──────┐ ┌▼──────┐
     │Ingestion   │ │Ext │ │QB  │ │GNN   │ │Query  │
     │Agent       │ │Agent│ │Agent│ │Reasoner│ │Agent │
     └────┬───────┘ └─┬──┘ └┬───┘ └┬──────┘ └┬──────┘
          │           │     │      │          │
     ┌────▼───────────▼─────▼──────▼──────────▼──────┐
     │              Knowledge Layer                   │
     │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │
     │  │ChromaDB │ │ Neo4j   │ │ SQLite          │ │
     │  │Vectors  │ │ Graph   │ │ Metadata/State  │ │
     │  └─────────┘ └─────────┘ └─────────────────┘ │
     └───────────────────────────────────────────────┘
```

## How data flows in (the write path)

Documents hit the ingestion pipeline in this order:

```
Raw Documents → Loader → Preprocessor → Chunker → Embedder → ChromaDB
                                 ↓
                         Entity Extractor (Groq Llama 3.1 8B)
                                 ↓
                         Graph Builder → Neo4j
```

Step by step:

1. `loaders.py` reads the file and extracts raw text
2. `preprocessor.py` cleans it up (normalize whitespace, strip headers)
3. `chunker.py` splits text into 512-token chunks with 50-token overlap
4. `vector_store.py` embeds chunks with sentence-transformers and stores in ChromaDB
5. `extraction.py` sends chunks to Groq Llama 3.1 8B to pull out entities
6. `graph_builder.py` creates or updates nodes and relationships in Neo4j

## How data flows out (the read path)

When someone asks a question:

```
User Query → Query Agent → ┬─ Vector Search (ChromaDB)
                            ├─ Graph Search (Neo4j)
                            ├─ GNN Reasoning (PyTorch Geometric)
                            └─ Context Assembler → LLM → Answer
```

What happens:

1. `query.py` gets the natural language question
2. `hybrid.py` runs three searches at the same time:
   - Vector: embed the query, find similar chunks in ChromaDB
   - Graph: convert query to Cypher, traverse the Neo4j graph
   - GNN: run link prediction and community detection on a subgraph
3. `reranker.py` merges results from all three sources and ranks them
4. `query.py` assembles context and sends it to Groq Llama 3.3 70B
5. The answer comes back with source citations

## State that flows between agents

LangGraph passes state between agents using a dictionary:

```python
class PipelineState(TypedDict):
    """Shared state across agents in LangGraph."""
    # Input
    user_query: str
    document_path: Optional[str]

    # Ingestion
    raw_text: Optional[str]
    chunks: Optional[list[Chunk]]

    # Extraction
    entities: Optional[list[Entity]]
    relationships: Optional[list[Relationship]]

    # Graph
    graph_nodes_created: int
    graph_edges_created: int

    # Retrieval
    vector_results: Optional[list[Document]]
    graph_results: Optional[list[GraphNode]]
    gnn_results: Optional[list[GraphEmbedding]]

    # Output
    answer: Optional[str]
    sources: Optional[list[str]]
    confidence: Optional[float]

    # Metadata
    processing_time: float
    agent_trace: list[str]
```

## What each interface looks like

Every agent implements the same base:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, state: PipelineState) -> PipelineState:
        """Process state and return updated state."""

    @abstractmethod
    def validate_input(self, state: PipelineState) -> bool:
        """Check if required inputs are present."""

    @abstractmethod
    def validate_output(self, state: PipelineState) -> bool:
        """Check if outputs are well-formed."""
```

The Groq client handles rate limiting and retries:

```python
class GroqClient:
    async def generate(
        self,
        prompt: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text with rate limiting and retry logic."""

    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        model: str = "llama-3.1-8b-instant",
    ) -> dict:
        """Generate structured JSON output with schema validation."""
```

The Neo4j client wraps graph operations:

```python
class Neo4jClient:
    async def create_node(self, label: str, properties: dict) -> str:
        """Create or merge a node, return node ID."""

    async def create_relationship(
        self, from_id: str, to_id: str, rel_type: str, properties: dict
    ) -> None:
        """Create a relationship between two nodes."""

    async def query(self, cypher: str, params: dict = None) -> list[dict]:
        """Execute a Cypher query and return results."""
```

## Rate limits

Groq's free tier is strict. Here's what we're working with:

- Llama 3.3 70B: 30 requests/min, 6,000 tokens/min, 1,000 requests/day
- Llama 3.1 8B: 30 requests/min, 6,000 tokens/min, 14,400 requests/day

We handle this with a token bucket rate limiter per model, exponential backoff on 429s, and batching entity extraction to minimize API calls. Max 100 requests queued at once.

## When things go wrong

```
┌──────────────────┬─────────────────────────────────────┐
│ What broke       │ What we do                          │
├──────────────────┼─────────────────────────────────────┤
│ Rate limit (429) │ Back off exponentially, retry 3x    │
│ API error (5xx)  │ Retry 2x, then fail with context    │
│ Invalid JSON     │ Re-prompt the LLM with a correction │
│ Neo4j timeout    │ Retry with a shorter query           │
│ ChromaDB error   │ Fall back to graph-only retrieval    │
│ Bad input        │ Return error to user, log warning   │
└──────────────────┴─────────────────────────────────────┘
```

## Security

Five layers:

1. Prompt injection detection (rule-based + LLM classifier)
2. Input sanitization (strip special characters from queries)
3. Output validation (make sure LLM responses don't leak system prompts)
4. API key isolation (environment variables only)
5. Neo4j access (local Docker, no external network)

## Performance targets

| Metric | Target | Why |
|--------|--------|-----|
| Query latency | < 5 seconds | End-to-end, including LLM call |
| Ingestion throughput | > 10 docs/min | Average 5-page PDF |
| Graph size | 10K-100K nodes | Semester project scale |
| Embedding index | < 1GB | ChromaDB local storage |
| Memory usage | < 4GB | Neo4j + ChromaDB + app |

## Where it runs

Everything runs on your laptop except the LLM calls:

```
Your Laptop (RTX 4060, 16GB RAM)
  Streamlit (port 8501)
  Neo4j Docker (port 7687)
  ChromaDB (in-process)
  SQLite (in-process)
  sentence-transformers (local)

    │ API calls only
    ▼

Groq Cloud (free tier)
  Llama 3.3 70B (queries)
  Llama 3.1 8B (extraction)
```
