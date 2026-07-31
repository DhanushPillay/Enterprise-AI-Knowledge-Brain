# AGENTS.md — Enterprise AI Knowledge Brain

Instructions for AI coding assistants working in this repo.

## What This Project Is

A multi-agent system that ingests org data, builds a knowledge graph with Neo4j, and answers questions via LLM agents. Uses Groq free-tier LLMs, local embeddings, and PyTorch Geometric for GNN reasoning.

## Tech Stack

- **Language:** Python 3.11+
- **LLM:** Groq API (Llama 3.3 70B for queries, Llama 3.1 8B for extraction)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2, 384 dims)
- **Vector Store:** ChromaDB (local, SQLite-backed)
- **Graph DB:** Neo4j Community 5.x (Docker)
- **GNN:** PyTorch Geometric
- **Multi-Agent:** LangGraph
- **Orchestration:** LangChain
- **Frontend:** Streamlit
- **Metadata:** SQLite

## Key Commands

```bash
pip install -r requirements.txt

docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community

streamlit run src/app.py

pytest tests/ -v

ruff check src/
ruff format src/

mypy src/
```

## Directory Structure

```
enterprise-ai-brain/
├── src/
│   ├── agents/           # Each agent = one file
│   │   ├── ingestion.py      # Reads and chunks documents
│   │   ├── extraction.py     # Pulls out entities
│   │   ├── graph_builder.py  # Builds the knowledge graph
│   │   ├── gnn_reasoner.py   # GNN reasoning
│   │   ├── query.py          # Answers questions
│   │   └── security.py       # Blocks bad prompts
│   ├── graph/            # Neo4j layer
│   │   ├── neo4j_client.py   # Connection + queries
│   │   ├── schema.py         # Node/relationship types
│   │   └── queries.py        # Cypher templates
│   ├── retrieval/        # Search layer
│   │   ├── vector_store.py   # ChromaDB ops
│   │   ├── hybrid.py         # Vector + graph combined
│   │   └── reranker.py       # Ranks results
│   ├── llm/              # LLM integration
│   │   ├── groq_client.py    # Rate-limit-aware Groq client
│   │   └── prompts.py        # Prompt templates
│   ├── ingestion/        # Document processing
│   │   ├── loaders.py        # PDF, TXT, MD loaders
│   │   ├── chunker.py        # Text chunking
│   │   └── preprocessor.py   # Text cleaning
│   ├── security/         # Security
│   │   ├── prompt_guard.py   # Injection detection
│   │   └── anomaly.py        # Query anomalies
│   ├── config.py         # All settings
│   └── app.py            # Streamlit frontend
├── tests/
├── docs/
├── data/                 # Sample docs for testing
└── notebooks/
```

## Coding Rules

- Type hints on every function
- PEP 8 (ruff enforces it)
- One class per file for agents, group utilities
- All LLM calls go through `src/llm/groq_client.py` (never call Groq directly)
- All Neo4j queries go through `src/graph/neo4j_client.py`
- Use `logging`, not `print()`
- Google-style docstrings for public functions

## Architecture Rules

1. One agent, one job. Don't combine ingestion + extraction.
2. All Groq calls must use the rate-limit-aware client. Check `docs/models.md`.
3. Local-first. No external services except Groq API.
4. No secrets in code. API keys come from env vars.
5. Graph schema is law. All node/relationship types must match `src/graph/schema.py`.

## Project Scope

Full project description, data sources, capabilities, and industry use cases are in `docs/project-scope.md`. Read it to understand what we're building and why.

## Don't

- Add new LLM providers (Groq is it)
- Add paid dependencies
- Hardcode API keys
- Skip rate limiting
- Create abstractions with one implementation
- Add comments explaining obvious code

## Testing

- pytest
- `pytest tests/ -v`
- 80% coverage for agents, 70% overall
- Integration tests need Docker (mark `@pytest.mark.integration`)
- Mock Groq calls in unit tests (never hit the real API)

## Git

- Format: `type(scope): description`
- Types: feat, fix, docs, refactor, test, chore
- Don't commit: `.env`, `__pycache__`, `.chroma/`, Neo4j data
