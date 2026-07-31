# Enterprise AI Knowledge Brain

A multi-agent system that reads your org's documents, builds a knowledge graph, and answers questions about them. Think of it as a company-wide assistant who's read everything and remembers it all.

Uses Groq's free LLMs, local embeddings, Neo4j for the graph, and PyTorch Geometric for finding hidden patterns.

---

## Quick Start

```bash
git clone <repo-url>
cd enterprise-ai-brain
pip install -r requirements.txt

# Start Neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:5-community

# Set your Groq API key (free at console.groq.com)
export GROQ_API_KEY="your-groq-api-key"

# Run the web interface
cd cortexa
npm install
npm run dev
```

## How It Works

```
User asks question
    │
    ▼
┌─────────────┐     ┌─────────────┐
│Query Agent  │     │Security     │
│(Llama 3.3)  │     │Agent        │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────────────────────┐
│     LangGraph Orchestrator  │
└──┬──────┬──────┬──────┬─────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│Vector││Graph ││GNN   ││Answer│
│Search││Search││Reason││Gen   │
└──────┘└──────┘└──────┘└──────┘
   │      │      │
   └──────┴──────┘
          │
┌─────────────────────────────┐
│     Knowledge Layer         │
│  ChromaDB | Neo4j | SQLite  │
└─────────────────────────────┘
```

Six agents, each doing one thing well:

| Agent | What it does | Model |
|-------|-------------|-------|
| Ingestion | Reads docs, splits into chunks | Llama 3.1 8B |
| Entity Extraction | Pulls out people, projects, concepts | Llama 3.1 8B |
| Knowledge Graph Builder | Connects entities in Neo4j | Direct Cypher |
| GNN Reasoner | Finds hidden patterns | PyTorch Geometric |
| Query Agent | Answers your questions | Llama 3.3 70B |
| Security Agent | Blocks prompt injection | Rules + classifier |

The knowledge graph stores entities (people, projects, tech) as nodes with typed relationships. When you ask a question, the system searches both the vector store (semantic similarity) and the graph (structural connections) to find the best answer.

Full details: [docs/agents.md](docs/agents.md), [docs/knowledge-graph.md](docs/knowledge-graph.md), [docs/pipeline.md](docs/pipeline.md)

## Documentation

| What | Where |
|------|-------|
| System architecture | [docs/architecture.md](docs/architecture.md) |
| Agent specs | [docs/agents.md](docs/agents.md) |
| Graph schema | [docs/knowledge-graph.md](docs/knowledge-graph.md) |
| Data flow | [docs/pipeline.md](docs/pipeline.md) |
| Model selection | [docs/models.md](docs/models.md) |
| Setup guide | [docs/setup.md](docs/setup.md) |
| Troubleshooting | [docs/troubleshooting.md](docs/troubleshooting.md) |

## Tech Stack

Everything here is free. No paid APIs, no subscriptions.

| What | Tool | Why |
|------|------|-----|
| LLM (answers) | Groq Llama 3.3 70B | Free, smart, fast |
| LLM (extraction) | Groq Llama 3.1 8B | Free, 30 RPM, good for bulk |
| Embeddings | sentence-transformers | Local, no API needed |
| Vector search | ChromaDB | Simple, local, free |
| Knowledge graph | Neo4j Community | Free, no node limits |
| GNN | PyTorch Geometric | Industry standard |
| Agent orchestration | LangGraph | By LangChain team |
| Frontend | Next.js & React | Modern, interactive web UI |

## Project Scope

Full project description, data sources, capabilities, and industry applicability: [docs/project-scope.md](docs/project-scope.md)

## License

B.Tech project. See LICENSE file.
