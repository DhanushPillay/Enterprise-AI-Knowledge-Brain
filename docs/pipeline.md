# Data Pipeline

Two pipelines. One for writing data in, one for reading it back out. LangGraph ties them together with `PipelineState`.

---

## Ingestion Pipeline (write path)

Documents go through six steps before they're searchable:

```
┌──────────────┐
│ Raw Document │  (PDF, TXT, MD, code)
└──────┬───────┘
       │
       ▼
┌──────────────┐     src/ingestion/loaders.py
│    Loader    │     Extracts raw text from file format
└──────┬───────┘
       │
       ▼
┌──────────────┐     src/ingestion/preprocessor.py
│ Preprocessor │     Cleans text, normalizes whitespace
└──────┬───────┘
       │
       ▼
┌──────────────┐     src/ingestion/chunker.py
│   Chunker    │     Splits into overlapping chunks (512 tokens)
└──────┬───────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────┐
│  Embedder    │     │   Entity     │
│ (MiniLM-L6)  │     │  Extractor   │
└──────┬───────┘     │(Llama 3.1 8B)│
       │             └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│  ChromaDB    │     │   Graph      │
│  (vectors)   │     │   Builder    │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Neo4j     │
                     │  (graph)     │
                     └──────────────┘
```

### Step 1: Loading

```python
class DocumentLoader:
    def load(self, file_path: str) -> RawDocument:
        """Load file based on extension."""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self._load_pdf(file_path)
        elif ext == ".txt":
            return self._load_text(file_path)
        elif ext == ".md":
            return self._load_markdown(file_path)
        elif ext in (".py", ".js", ".ts", ".java", ".go"):
            return self._load_code(file_path)
        else:
            raise UnsupportedFormatError(ext)
```

### Step 2: Preprocessing

```python
class TextPreprocessor:
    def preprocess(self, text: str) -> str:
        """Clean and normalize text."""
        text = self._normalize_whitespace(text)
        text = self._remove_headers_footers(text)
        text = self._fix_encoding(text)
        return text
```

### Step 3: Chunking

```python
class TextChunker:
    def chunk(
        self,
        text: str,
        chunk_size: int = 512,      # tokens
        chunk_overlap: int = 50,     # tokens
    ) -> list[Chunk]:
        """Split text into overlapping chunks."""
        # Token-aware splitting using tiktoken or sentencepiece
        # Each chunk: {text, index, start_pos, end_pos, doc_id}
```

### Step 4: Embedding

```python
class VectorStore:
    def add_documents(self, chunks: list[Chunk]) -> None:
        """Embed chunks and store in ChromaDB."""
        # sentence-transformers all-MiniLM-L6-v2
        # 384 dimensions
        # Stores: chunk text, metadata, embedding vector
```

### Step 5: Entity Extraction

```python
class EntityExtractionAgent:
    async def extract(self, chunks: list[Chunk]) -> ExtractionOutput:
        """Extract entities from chunks using LLM."""
        # For each batch of 5 chunks:
        #   1. Construct extraction prompt
        #   2. Send to Groq Llama 3.1 8B
        #   3. Parse JSON response
        #   4. Deduplicate entities
        # Rate limit: 2-second delay between batches
```

The extraction prompt:

```
Extract all named entities and relationships from the following text.

Entity types: Person, Organization, Project, Technology, Concept, Date, Location
Relationship types: WORKS_ON, WORKS_FOR, USES, DEPENDS_ON, MENTIONS, AUTHORED_BY, MANAGES, PART_OF

Return JSON:
{
    "entities": [
        {"name": "...", "type": "...", "confidence": 0.9}
    ],
    "relationships": [
        {"from": "...", "to": "...", "type": "...", "confidence": 0.8}
    ]
}

Text:
{text}
```

### Step 6: Graph Building

```python
class KnowledgeGraphBuilderAgent:
    def build_graph(self, extraction: ExtractionOutput) -> GraphBuilderOutput:
        """Create/update nodes and relationships in Neo4j."""
        # For each entity: MERGE node (create or update)
        # For each relationship: MERGE edge (create or update)
        # Track: nodes_created, nodes_updated, edges_created, edges_updated
```

---

## Retrieval Pipeline (read path)

When someone asks a question, this is what happens:

```
┌──────────────┐
│  User Query  │  "Who worked on Project Alpha?"
└──────┬───────┘
       │
       ▼
┌──────────────┐     src/agents/security.py
│   Security   │     Check for injection, rate limits
│    Agent     │
└──────┬───────┘
       │ (if safe)
       ▼
┌──────────────┐     src/agents/query.py
│  Query       │     Classify query type
│  Classifier  │     (factual, relational, aggregative)
└──────┬───────┘
       │
       ├────────────────────┬────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│Vector Search │     │ Graph Search │     │ GNN Reasoner │
│  (ChromaDB)  │     │   (Neo4j)    │     │  (PyTorch)   │
│              │     │              │     │              │
│ Embed query  │     │ Convert to   │     │ Run link     │
│ → top-k      │     │ Cypher →     │     │ prediction   │
│   chunks     │     │ traverse     │     │ → hidden     │
│              │     │              │     │   relations  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Reranker   │     src/retrieval/reranker.py
                     │              │     Merge + rank results
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Context    │     Assemble top results into prompt
                     │  Assembler   │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Query Agent   │     src/agents/query.py
                     │(Llama 3.3    │     Generate answer with citations
                     │ 70B)         │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Answer     │     Formatted response with sources
                     └──────────────┘
```

### Step 1: Security Check

```python
class SecurityAgent:
    def check(self, query: str, session_id: str) -> SecurityOutput:
        """Validate query is safe to process."""
        # 1. Pattern matching (injection detection)
        # 2. Rate limiting (per session)
        # 3. Statistical analysis (length, characters)
        # Returns: is_safe, threat_type, confidence
```

### Step 2: Vector Search

```python
class VectorStore:
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: dict = None,
    ) -> list[SearchResult]:
        """Semantic search in ChromaDB."""
        # 1. Embed query with sentence-transformers
        # 2. Search ChromaDB for nearest neighbors
        # 3. Return chunks with similarity scores
```

### Step 3: Graph Search

```python
class Neo4jClient:
    def search(
        self,
        query: str,
        max_depth: int = 2,
        limit: int = 20,
    ) -> list[GraphNode]:
        """Search knowledge graph for relevant entities."""
        # 1. Convert query to entity names (LLM or NER)
        # 2. Find matching nodes in Neo4j
        # 3. Traverse relationships up to max_depth
        # 4. Return subgraph with context
```

### Step 4: GNN Reasoning

```python
class GNNReasonerAgent:
    def reason(
        self,
        nodes: list[str],
        task: str = "link_prediction",
    ) -> GNNOutput:
        """Run GNN inference on subgraph."""
        # 1. Extract subgraph around input nodes
        # 2. Convert to PyTorch Geometric Data
        # 3. Run GNN forward pass
        # 4. Return predictions + reasoning path
```

### Step 5: Reranking

```python
class Reranker:
    def rerank(
        self,
        vector_results: list[SearchResult],
        graph_results: list[GraphNode],
        gnn_results: list[GNNOutput],
        weights: dict = None,
    ) -> list[RankedResult]:
        """Merge and rank results from all sources."""
        # Default weights: vector=0.4, graph=0.4, gnn=0.2
        # Normalize scores to [0, 1]
        # Sort by combined score
        # Deduplicate by entity/chunk ID
```

### Step 6: Answer Generation

```python
class QueryAgent:
    async def answer(
        self,
        question: str,
        context: list[RankedResult],
    ) -> QueryOutput:
        """Generate answer with citations."""
        # 1. Assemble context (max 4096 tokens)
        # 2. Format prompt with context + question
        # 3. Send to Groq Llama 3.3 70B
        # 4. Parse response, extract citations
        # 5. Calculate confidence score
        # 6. Return formatted answer
```

---

## Incremental Updates

New documents don't require a full rebuild. The system merges new data into the existing graph:

```python
class IncrementalUpdater:
    def update(self, new_doc_path: str) -> UpdateResult:
        """Add new document to existing knowledge graph."""
        # 1. Ingest new document (load → chunk → embed)
        # 2. Extract entities from new chunks
        # 3. MERGE entities into existing graph
        # 4. MERGE relationships into existing graph
        # 5. Update ChromaDB with new embeddings
        # 6. Return update statistics
```

The trick is using Neo4j MERGE instead of CREATE. That way we don't end up with duplicate nodes.

---

## State Management

LangGraph handles the state machine:

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph

class PipelineState(TypedDict):
    # Input
    user_query: str | None
    document_path: str | None

    # Ingestion
    raw_text: str | None
    chunks: list[Chunk] | None

    # Extraction
    entities: list[Entity] | None
    relationships: list[Relationship] | None

    # Graph
    graph_nodes_created: int
    graph_edges_created: int

    # Retrieval
    vector_results: list[SearchResult] | None
    graph_results: list[GraphNode] | None
    gnn_results: list[GNNOutput] | None

    # Output
    answer: str | None
    sources: list[Source] | None
    confidence: float | None

    # Metadata
    processing_time: float
    agent_trace: list[str]

# Build the graph
graph = StateGraph(PipelineState)
graph.add_node("security_check", security_agent.run)
graph.add_node("ingest", ingestion_agent.run)
graph.add_node("extract", extraction_agent.run)
graph.add_node("build_graph", graph_builder_agent.run)
graph.add_node("query", query_agent.run)

# Define edges
graph.add_edge("security_check", "ingest")  # or "query" based on input
graph.add_edge("ingest", "extract")
graph.add_edge("extract", "build_graph")
graph.add_edge("build_graph", END)
```
