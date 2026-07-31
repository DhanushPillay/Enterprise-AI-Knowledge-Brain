# CLAUDE.md

This file provides instructions for Claude Code when working in this repository.

## Read First

Read `AGENTS.md` for full project context, conventions, and architecture rules.

## Quick Reference

- **Project:** Enterprise AI Knowledge Brain — multi-agent system with knowledge graph
- **Stack:** Python 3.11+, Groq API, Neo4j, ChromaDB, PyTorch Geometric, LangGraph
- **Commands:** `pip install -r requirements.txt`, `streamlit run src/app.py`, `pytest tests/ -v`
- **Lint:** `ruff check src/ && ruff format src/`
- **Type check:** `mypy src/`

## Key Files

- `AGENTS.md` — full conventions and architecture rules
- `docs/architecture.md` — system design and data flow
- `docs/agents.md` — agent specifications
- `docs/models.md` — LLM model selection and rate limits
- `src/config.py` — all configuration and environment variables
