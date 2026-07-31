# Troubleshooting

When something breaks, check here first. Each section has the symptom, what's probably wrong, how to fix it, and how to verify it worked.

---

## Connection problems

### Neo4j

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| `ServiceUnavailable: Bolt port 7687` | Docker container isn't running | `docker start neo4j` | `docker ps` shows neo4j |
| `Authentication failed` | Wrong password | Check `NEO4J_PASSWORD` env var | `curl http://localhost:7474` |
| `Connection refused` | Port not mapped | Restart with `-p 7687:7687` | `netstat -ano \| findstr :7687` |

### Groq API

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| `AuthenticationError` | Bad API key | Get a new one at console.groq.com | `echo $GROQ_API_KEY` |
| `RateLimitError (429)` | Too many requests | Wait 60s, make batches smaller | Check usage tracker |
| `DailyLimitError` | Hit the daily cap | Wait until tomorrow, or switch to 8B model | Check `daily_count` |
| `APITimeoutError` | Network hiccup | Retry, check your internet | `ping api.groq.com` |

### ChromaDB

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| `InvalidCollection` | Corrupted database | Delete `.chroma/` directory | Reinitialize client |
| `Embedding dimension mismatch` | Wrong model loaded | Make sure you're using `all-MiniLM-L6-v2` everywhere | Check embedding dims |

---

## Processing problems

### Entity extraction comes back empty

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| Empty entities list | Prompt is too complicated | Simplify the extraction prompt | Test with a single sentence |
| LLM returns bad JSON | Model got confused | Add a JSON schema constraint | Check `generate_structured` |
| Low confidence scores | Text is ambiguous | Lower the threshold or add more context | Look at sample outputs |

### Knowledge graph won't update

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| Nodes not created | Bad MERGE syntax | Check the Cypher query | Run it in the Neo4j browser |
| Relationships missing | One endpoint doesn't exist | Make sure both nodes exist first | `MATCH (n) RETURN count(n)` |
| Duplicates showing up | Using CREATE instead of MERGE | Switch to MERGE | Check `graph_builder.py` |

### Query returns nothing useful

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| "Not enough information" | Nothing relevant in the graph | Ingest more documents | Check ChromaDB count |
| Irrelevant results | Retrieval isn't tuned | Adjust similarity threshold | Look at search results |
| LLM refuses to answer | Prompt is too strict | Loosen the context requirements | Try a simpler question |

---

## Performance problems

### Queries are slow (over 5 seconds)

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| LLM takes forever | Model is too big for this task | Use Llama 3.1 8B for simple stuff | Check response times |
| Graph traversal is slow | Too many relationships | Limit traversal depth | Add `LIMIT` to Cypher |
| ChromaDB is slow | Index got big | Reduce top-k, add filters | Profile with `timeit` |

### Running out of memory

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| OOM during ingestion | Too many chunks in memory at once | Process in smaller batches | `htop` |
| Neo4j memory spike | Big graph import | Limit batch size in MERGE | `docker stats neo4j` |

### Hitting rate limits constantly

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| 429 errors during extraction | Batch is too big | Drop batch size to 5 | Check `rate_limiter.py` |
| Daily limit gone by noon | Too many API calls | Cache results, use local models for simple stuff | Review usage tracker |

---

## Streamlit app problems

| What you see | Probably this | Fix | Check |
|-------------|---------------|-----|-------|
| `ModuleNotFoundError` | Missing dependency | `pip install -r requirements.txt` | `pip list` |
| `Port 8501 in use` | Another Streamlit is running | Kill the other one, or use `--server.port 8502` | `netstat -ano \| findstr :8501` |
| `SyntaxError` in app.py | Code bug | Check `src/app.py` | `python -m py_compile src/app.py` |

---

## Quick diagnostic script

Run this to check everything at once:

```python
import os
from neo4j import GraphDatabase
from groq import Groq
import chromadb

def diagnose():
    results = {}

    # Neo4j
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
        )
        driver.verify_connectivity()
        results["neo4j"] = "OK"
    except Exception as e:
        results["neo4j"] = f"FAIL: {e}"

    # Groq
    try:
        client = Groq()
        client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        results["groq"] = "OK"
    except Exception as e:
        results["groq"] = f"FAIL: {e}"

    # ChromaDB
    try:
        client = chromadb.Client()
        client.list_collections()
        results["chromadb"] = "OK"
    except Exception as e:
        results["chromadb"] = f"FAIL: {e}"

    # Embeddings
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        model.encode(["test"])
        results["embeddings"] = "OK"
    except Exception as e:
        results["embeddings"] = f"FAIL: {e}"

    # Environment
    results["groq_key"] = "SET" if os.getenv("GROQ_API_KEY") else "MISSING"

    for component, status in results.items():
        print(f"  {component}: {status}")

if __name__ == "__main__":
    diagnose()
```
