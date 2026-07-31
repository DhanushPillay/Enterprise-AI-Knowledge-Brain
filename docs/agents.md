# Agent Specifications

Six agents. Each does one thing. All follow the `BaseAgent` interface from `docs/architecture.md`.

---

## 1. Ingestion Agent

**File:** `src/agents/ingestion.py`
**Class:** `IngestionAgent`
**Model:** Groq Llama 3.1 8B

### What it does

Reads raw documents, extracts text, cleans it up, and splits it into chunks that work well for embedding and entity extraction.

### Input

```python
@dataclass
class IngestionInput:
    file_path: str              # Path to document
    file_type: str              # "pdf", "txt", "md", "code"
    chunk_size: int = 512       # Tokens per chunk
    chunk_overlap: int = 50     # Overlap between chunks
```

### Output

```python
@dataclass
class IngestionOutput:
    chunks: list[Chunk]         # Processed text chunks
    metadata: DocumentMetadata  # File info, chunk count, processing time
    errors: list[str]           # Non-fatal errors (e.g., skipped pages)
```

### How it works

1. Detects file type from the extension
2. Loads the file using the right loader (`src/ingestion/loaders.py`)
3. Cleans up the text (`src/ingestion/preprocessor.py`)
4. Splits into chunks (`src/ingestion/chunker.py`)
5. Generates embeddings for each chunk (sentence-transformers)
6. Stores everything in ChromaDB

### What can go wrong

- Unsupported file type: return error, skip the file
- Empty document: return warning, zero chunks
- Corrupted PDF: try to extract what we can, report partial results

---

## 2. Entity Extraction Agent

**File:** `src/agents/extraction.py`
**Class:** `EntityExtractionAgent`
**Model:** Groq Llama 3.1 8B (fast, 30 RPM)

### What it does

Pulls out named entities (people, orgs, projects, concepts, dates) and relationships from text chunks.

### Input

```python
@dataclass
class ExtractionInput:
    chunks: list[Chunk]                    # Text chunks to process
    entity_types: list[str]                # Types to extract
    extraction_prompt: str                 # Prompt template
```

### Output

```python
@dataclass
class ExtractionOutput:
    entities: list[Entity]                 # Extracted entities
    relationships: list[Relationship]      # Extracted relationships
    extraction_stats: ExtractionStats      # Counts, confidence scores
```

### Entity types

```python
ENTITY_TYPES = [
    "Person",        # People's names
    "Organization",  # Companies, departments, teams
    "Project",       # Named projects, initiatives
    "Technology",    # Tools, frameworks, languages
    "Concept",       # Abstract ideas, methodologies
    "Date",          # Dates, time periods
    "Location",      # Places, offices, regions
    "Document",      # References to other documents
]
```

### Relationship types

```python
RELATIONSHIP_TYPES = [
    "WORKS_ON",       # Person → Project
    "WORKS_FOR",      # Person → Organization
    "USES",           # Project/Person → Technology
    "DEPENDS_ON",     # Project → Project/Technology
    "MENTIONS",       # Document → Entity
    "AUTHORED_BY",    # Document → Person
    "MANAGES",        # Person → Person/Project
    "PART_OF",        # Organization → Organization
]
```

### How it works

1. Builds an extraction prompt for each chunk
2. Sends it to Groq Llama 3.1 8B with a JSON schema constraint
3. Parses the response into Entity and Relationship objects
4. Deduplicates entities using fuzzy matching on name + type
5. Assigns confidence scores
6. Returns the extracted data

### Rate limiting

Batches of 5 chunks, 2-second delay between batches. Keeps us within 30 RPM. Overflow goes into a queue for the next run.

---

## 3. Knowledge Graph Builder Agent

**File:** `src/agents/graph_builder.py`
**Class:** `KnowledgeGraphBuilderAgent`
**Model:** None (direct Cypher queries)

### What it does

Takes extracted entities and relationships, then creates or updates nodes and edges in Neo4j.

### Input

```python
@dataclass
class GraphBuilderInput:
    entities: list[Entity]
    relationships: list[Relationship]
    source_document: str           # Document ID for provenance
```

### Output

```python
@dataclass
class GraphBuilderOutput:
    nodes_created: int
    nodes_updated: int
    edges_created: int
    edges_updated: int
    conflicts: list[GraphConflict]  # Duplicate/merge decisions
```

### How it works

For each entity, it checks if the node already exists (MATCH on name + type). If it does, it merges new properties in. If not, it creates a new node. Same deal for relationships. Every node and relationship gets tagged with the source document, a timestamp, and a confidence score.

### The Cypher queries

```cypher
// Create or merge entity node
MERGE (e:Entity {name: $name, type: $type})
ON CREATE SET e += $properties, e.created_at = datetime()
ON MATCH SET e += $properties, e.updated_at = datetime()

// Create relationship
MATCH (a:Entity {name: $from_name, type: $from_type})
MATCH (b:Entity {name: $to_name, type: $to_type})
MERGE (a)-[r:RELATES_TO {type: $rel_type}]->(b)
SET r += $properties
```

---

## 4. GNN Reasoner Agent

**File:** `src/agents/gnn_reasoner.py`
**Class:** `GNNReasonerAgent`
**Model:** PyTorch Geometric (runs locally, no API calls)

### What it does

Runs graph neural network inference on the knowledge graph. Finds missing links (link prediction), clusters related nodes (community detection), and scores node importance.

### Input

```python
@dataclass
class GNNInput:
    subgraph_nodes: list[str]     # Nodes relevant to query
    query: str                    # User's question (for context)
    task: str                     # "link_prediction", "community", "classification"
```

### Output

```python
@dataclass
class GNNOutput:
    predicted_links: list[PredictedLink]      # (node_a, node_b, confidence)
    communities: list[Community]              # Groups of related nodes
    node_scores: dict[str, float]            # Importance scores
    reasoning_path: list[str]                 # Explainable reasoning chain
```

### The GNN

Uses GraphSAGE because it scales well and works with partial graphs. Features are node type one-hot plus text embeddings (384 dims). Pre-trained on the full graph, fine-tuned per query. Runs on CPU since the graph is small (under 100K nodes).

### How it works

1. Extracts the subgraph around the relevant nodes
2. Converts it to a PyTorch Geometric `Data` object
3. Runs the GNN forward pass
4. Extracts predictions with confidence scores
5. Maps everything back to entity names so we can explain the reasoning

---

## 5. Query Agent

**File:** `src/agents/query.py`
**Class:** `QueryAgent`
**Model:** Groq Llama 3.3 70B

### What it does

Answers natural-language questions. Runs the retrieval pipeline, assembles context, generates an answer with citations, and calculates a confidence score.

### Input

```python
@dataclass
class QueryInput:
    question: str                          # User's natural language question
    context_limit: int = 4096              # Max tokens for context
    require_citations: bool = True         # Include source references
```

### Output

```python
@dataclass
class QueryOutput:
    answer: str                            # Generated answer
    sources: list[Source]                  # Cited documents/nodes
    confidence: float                      # Answer confidence (0-1)
    reasoning: str                         # How the answer was derived
    alternative_answers: list[str]         # Other possible answers
```

### How it works

1. Figures out what kind of question it is (factual, relational, aggregative, exploratory)
2. Runs hybrid retrieval (vector + graph + GNN)
3. Assembles context from the top results
4. Generates the answer with Llama 3.3 70B
5. Pulls out citations
6. Calculates confidence
7. Formats the response

### Query types

```python
QUERY_TYPES = {
    "factual":      "Who/What/When/Where questions",
    "relational":   "How are X and Y connected?",
    "aggregative":  "How many/Which/Summarize",
    "exploratory":  "Tell me about...", "What do you know about...",
}
```

### The prompt

```
You are an enterprise knowledge assistant. Answer the question using ONLY
the provided context. If the context doesn't contain enough information,
say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer with citations [Source: document_name]:
```

---

## 6. Security Agent

**File:** `src/agents/security.py`
**Class:** `SecurityAgent`
**Model:** Rule-based + local classifier (no LLM calls)

### What it does

Blocks prompt injection attacks, catches malicious queries, and flags anomalous behavior.

### Input

```python
@dataclass
class SecurityInput:
    user_query: str
    session_id: str
    query_history: list[str]     # Recent queries from this session
```

### Output

```python
@dataclass
class SecurityOutput:
    is_safe: bool
    threat_type: Optional[str]   # "injection", "anomaly", "excessive_rate"
    confidence: float
    blocked_reason: Optional[str]
```

### How it detects threats

**Pattern matching (rule engine):**

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all)\s+(instructions|prompts)",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"system\s*:\s*",
    r"forget\s+(everything|all|previous)",
    r"(?:bypass|override)\s+(?:safety|security|rules)",
    r"act\s+as\s+(?:if|though)\s+",
    r"(?:pretend|imagine)\s+(?:you\s+are|that)\s+",
]
```

**Statistical checks:**
- Query too long (over 1000 chars) or too short (under 2 chars)
- Rate limiting (more than 20 queries per minute per session)
- Weird vocabulary (non-English, lots of special characters)

**LLM-based detection (only when rules aren't sure):**
Sends suspicious queries to Llama 3.1 8B with a classifier prompt. Only kicks in when the rule-based confidence is below 0.7.

### What it does with bad queries

```python
"I'm sorry, but I can't process that request. It appears to contain
content that may be attempting to override my instructions. Please
rephrase your question in a straightforward manner."
```

---

## How agents talk to each other

Agents don't call each other directly. They communicate through LangGraph's `PipelineState` dictionary, and the orchestrator controls what runs when:

```
User Input
    │
    ▼
Security Agent → (if safe) → Ingestion/Query Router
    │                           │
    │              ┌────────────┴────────────┐
    │              ▼                         ▼
    │         Ingestion Path           Query Path
    │         ├─ Ingestion Agent       ├─ Query Agent
    │         ├─ Entity Extraction     │   ├─ Vector Search
    │         └─ Graph Builder         │   ├─ Graph Search
    │                                  │   ├─ GNN Reasoner
    │                                  │   └─ Context Assembly
    │                                  └─ Answer Generation
    ▼
User Output
```
