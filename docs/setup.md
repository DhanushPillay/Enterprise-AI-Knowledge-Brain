# Setup Guide

## What you need

- Python 3.11+
- Docker Desktop (for Neo4j)
- Groq API key (free at console.groq.com)
- 8GB+ RAM (16GB is better)
- RTX 4060 or similar (optional, only for GNN training)

---

## Install

### 1. Clone and set up

```bash
git clone <repo-url>
cd enterprise-ai-brain
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Start Neo4j

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5-community
```

Check it at http://localhost:7474. Login: `neo4j` / `password`.

### 3. Set up environment variables

Create a `.env` file:

```bash
# Groq API (required)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# Neo4j (these are the defaults)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# App settings (optional)
APP_HOST=0.0.0.0
APP_PORT=8501
LOG_LEVEL=INFO
```

### 4. Initialize and run

```bash
# Set up the database schema
python -m src.graph.schema init

# Check that everything connects
python -m src.config verify

# Start the app
streamlit run src/app.py
```

Open http://localhost:8501.

---

## Verify everything works

```bash
python --version          # Should be 3.11+
docker ps                 # Should show neo4j running
curl http://localhost:7474  # Should return JSON

python -c "from groq import Groq; c = Groq(); print('Groq OK')"
python -c "import chromadb; c = chromadb.Client(); print('Chroma OK')"
python -c "from sentence_transformers import SentenceTransformer; print('ST OK')"
```

You should see:

```
Neo4j:     Connected (bolt://localhost:7687)
Groq:      Connected (API key found)
ChromaDB:  Connected (local storage)
Embeddings: Ready (all-MiniLM-L6-v2)
```

---

## Project layout

```
enterprise-ai-brain/
├── src/
│   ├── agents/           # Agent implementations
│   ├── graph/            # Neo4j integration
│   ├── retrieval/        # Vector + graph search
│   ├── llm/              # Groq API client
│   ├── ingestion/        # Document processing
│   ├── security/         # Prompt guard
│   ├── config.py         # Configuration
│   └── app.py            # Streamlit frontend
├── tests/
├── docs/
├── data/                 # Sample documents
├── notebooks/
├── .env                  # Environment variables (gitignored)
├── requirements.txt
└── README.md
```

---

## When things break

### Neo4j won't start

```bash
# Something's using the port
netstat -ano | findstr :7474

# Kill the old container and try again
docker rm -f neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community
```

### Groq API errors

```bash
# Check your key
echo $GROQ_API_KEY

# Quick test
python -c "
from groq import Groq
c = Groq()
r = c.chat.completions.create(
    model='llama-3.1-8b-instant',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(r.choices[0].message.content)
"
```

### ChromaDB errors

```bash
# Wipe the local database and start fresh
rm -rf .chroma/
python -c "import chromadb; chromadb.Client()"
```

### Memory issues

```bash
# Check how much Neo4j is using
docker stats neo4j

# Cap its memory
docker run -d --name neo4j \
  -e NEO4J_server_memory_heap_initial__size=512m \
  -e NEO4J_server_memory_heap_max__size=1g \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

---

## Dev setup

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
ruff check src/
ruff format src/
mypy src/
```
