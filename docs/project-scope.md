# Project Scope

Enterprise AI Brain: A Self-Learning Multi-Agent Organizational Intelligence Operating System.

---

## What this is

A next-generation self-learning organizational intelligence platform that functions as an AI Operating System for enterprises. Not a chatbot. Not a simple RAG system. It continuously learns from organizational knowledge and builds a dynamic knowledge graph representing the entire enterprise.

### What makes it different from traditional systems

Traditional chatbots answer questions from static data. Simple RAG systems retrieve relevant chunks and generate answers. This system goes further:

- It learns continuously, not just when you retrain
- It builds relationships between people, projects, tech, and decisions
- It reasons over the graph using GNNs, not just vector similarity
- It explains why it gave a certain answer
- It protects itself from manipulation
- It evolves as new data arrives without starting from scratch

---

## Data sources

The system ingests data from across the organization:

| Source | What it extracts | Status |
|--------|-----------------|--------|
| Documents (PDF, TXT, MD) | Text, entities, relationships | Built |
| Source code | Functions, classes, dependencies, authors | Built |
| Databases | Schema, records, relationships | Planned |
| APIs | Endpoints, data models, usage patterns | Planned |
| Emails | People, decisions, action items | Planned |
| Project repos | Commits, issues, contributors, timelines | Planned |
| Business workflows | Steps, owners, handoffs, bottlenecks | Planned |

Each source gets its own loader agent that converts raw data into a standard format the rest of the pipeline can process.

---

## Core capabilities

### Large Language Models (LLMs)

Used for entity extraction, query answering, and text classification. Runs on Groq's free tier with Llama 3.3 70B (smart tasks) and Llama 3.1 8B (bulk extraction).

### Knowledge Graphs

Entities and relationships live in Neo4j. People connect to projects, projects use technology, documents mention concepts. The graph grows as new data arrives.

### Graph Neural Networks (GNNs)

PyTorch Geometric runs GraphSAGE on the knowledge graph. Finds hidden patterns: who should talk to each other, which projects are related, what's likely to break next.

### Continual Learning

The system updates incrementally. New documents don't require a full rebuild. Entities get MERGED (created or updated), relationships get added, embeddings get indexed. The graph evolves over time instead of staying static.

How it works:
- New document arrives → ingestion pipeline processes it
- Entities extracted → MERGE into existing graph (no duplicates)
- New embeddings → added to ChromaDB index
- GNN retrains periodically on the updated graph
- Knowledge compounds over time

### Explainable AI (XAI)

Every answer comes with reasoning. The system shows which documents, graph paths, and GNN predictions led to its answer. SHAP values explain feature importance. Users can trace back from answer to source.

What gets explained:
- Which documents were retrieved and why
- Which graph relationships were traversed
- What the GNN predicted and with what confidence
- How the final answer was assembled from context

### Anomaly Detection

Two layers of protection:

**Prompt injection detection:** Rule-based patterns plus LLM classifier block attempts to override system instructions. Catches "ignore previous instructions," "you are now a," and similar attacks.

**Agent behavior monitoring:** Tracks agent activity for unusual patterns. Flags if an agent starts making too many API calls, accessing unexpected data, or producing outputs that don't match its role.

### Decision Recommendations

Beyond answering questions, the system suggests actions:
- "These three people should collaborate on X"
- "Project A depends on Project B, which is behind schedule"
- "This technology choice conflicts with your security policy"

---

## How the agents collaborate

Six specialized agents, each with a single job, working together:

```
Data Sources
    │
    ▼
┌──────────────────────────────────────────────┐
│              Ingestion Pipeline              │
│  Loader → Preprocessor → Chunker → Extractor│
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           Knowledge Graph Builder            │
│         Entities + Relationships → Neo4j     │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              Query Pipeline                  │
│  Vector Search + Graph Search + GNN Reasoning│
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           Answer + Explanation               │
│      Response with sources + reasoning       │
└──────────────────────────────────────────────┘
```

The Security Agent watches everything, blocking bad inputs and monitoring agent behavior.

---

## Industry applicability

This system works across industries because the core problem is the same everywhere: organizational knowledge is scattered, disconnected, and hard to find.

### Manufacturing
- Equipment manuals, maintenance logs, quality reports
- Link defects to root causes across shifts and facilities
- Recommend preventive maintenance based on patterns

### Finance
- Compliance documents, audit trails, policy updates
- Track regulatory changes across jurisdictions
- Flag transactions that don't match historical patterns

### Healthcare
- Medical records, research papers, treatment protocols
- Connect symptoms to diagnoses across patient populations
- Suggest evidence-based treatments based on similar cases

### IT Services
- Code repos, incident reports, architecture docs
- Map dependencies between services and teams
- Predict which changes are likely to cause incidents

### Smart Enterprises
- Cross-department knowledge, meeting notes, decisions
- Break down silos between teams
- Surface institutional knowledge before it walks out the door

---

## What's built vs what's left

### Done
- Full project documentation (this doc, README, architecture, agents, etc.)
- Data source mapping and extraction strategy
- Knowledge graph schema design
- Rate limiting and Groq integration plan
- Security module design (prompt injection)

### Next (Phase 2: core code)
- Ingestion agent (document loading, chunking, embedding)
- Entity extraction agent (Groq Llama 3.1 8B)
- Knowledge graph builder (Neo4j MERGE operations)
- Query agent (hybrid retrieval + answer generation)
- Streamlit frontend

### Later (Phase 3: advanced features)
- GNN reasoning agent (PyTorch Geometric)
- Continual learning (incremental graph updates)
- Explainable AI (SHAP integration)
- Anomaly detection (agent behavior monitoring)

### Far later (Phase 4:扩展)
- Database connector agent
- API connector agent
- Email parser agent
- Decision recommendation engine
- Industry-specific adaptations

---

## Tech stack

Everything free. No paid APIs.

| What | Tool | Why |
|------|------|-----|
| LLM (answers) | Groq Llama 3.3 70B | Free, smart, fast |
| LLM (extraction) | Groq Llama 3.1 8B | Free, 30 RPM, bulk work |
| Embeddings | sentence-transformers | Local, no API needed |
| Vector search | ChromaDB | Simple, local, free |
| Knowledge graph | Neo4j Community | Free, no node limits |
| GNN | PyTorch Geometric | Industry standard |
| Explainability | SHAP | Free, standard |
| Agent orchestration | LangGraph | By LangChain team |
| Frontend | Streamlit | Fast to build |
