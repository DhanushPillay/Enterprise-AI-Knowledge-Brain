"""Application configuration — single source of truth.

Reads settings from environment variables and .env file.
Uses Pydantic for validation so we catch bad config early,
not in the middle of a pipeline run.

Usage:
    from src.config import settings
    print(settings.groq_api_key)

Verify everything connects:
    python -m src.config
"""

import logging
import os
import sys
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Project root: two levels up from this file (src/config.py -> project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class GroqModelConfig:
    """Rate limit constants for each Groq model.

    These come from Groq's free-tier docs (updated July 2026).
    Kept as a plain class, not a Pydantic model, because these
    are constants — not user-configurable.
    """

    LLAMA_70B = "llama-3.3-70b-versatile"
    LLAMA_8B = "llama-3.1-8b-instant"

    # Requests per minute / tokens per minute / requests per day
    LIMITS = {
        LLAMA_70B: {"rpm": 30, "tpm": 12_000, "rpd": 1_000},
        LLAMA_8B: {"rpm": 30, "tpm": 12_000, "rpd": 14_400},
    }


class Settings(BaseSettings):
    """All application settings in one place.

    Reads from .env file at project root, then falls back
    to environment variables. Every downstream module imports
    `settings` from this file instead of reading env vars directly.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Groq API -----------------------------------------------------------
    groq_api_key: str = Field(
        ...,
        description="Groq API key (starts with gsk_). Free at console.groq.com",
    )
    groq_model_query: str = Field(
        default=GroqModelConfig.LLAMA_70B,
        description="Model for answering questions (needs reasoning).",
    )
    groq_model_extraction: str = Field(
        default=GroqModelConfig.LLAMA_8B,
        description="Model for bulk entity extraction (fast, high daily limit).",
    )
    groq_max_retries: int = Field(
        default=3,
        description="Max retries on rate-limit (429) errors before giving up.",
    )
    groq_base_backoff_seconds: float = Field(
        default=2.0,
        description="Base wait time for exponential backoff (doubles each retry).",
    )

    # --- Neo4j ---------------------------------------------------------------
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j Bolt connection URI.",
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username.",
    )
    neo4j_password: str = Field(
        default="password",
        description="Neo4j password.",
    )

    # --- ChromaDB ------------------------------------------------------------
    chroma_persist_dir: str = Field(
        default=".chroma",
        description="Directory for ChromaDB persistent storage.",
    )
    chroma_collection_name: str = Field(
        default="knowledge_chunks",
        description="Name of the ChromaDB collection for document chunks.",
    )

    # --- Embeddings ----------------------------------------------------------
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformer model for embeddings (384 dims).",
    )
    embedding_dimensions: int = Field(
        default=384,
        description="Dimensionality of embedding vectors.",
    )

    # --- Chunking ------------------------------------------------------------
    chunk_size: int = Field(
        default=512,
        description="Number of tokens per text chunk.",
    )
    chunk_overlap: int = Field(
        default=50,
        description="Number of overlapping tokens between consecutive chunks.",
    )

    # --- Retrieval -----------------------------------------------------------
    vector_search_top_k: int = Field(
        default=10,
        description="Number of results to return from vector search.",
    )
    graph_search_max_depth: int = Field(
        default=2,
        description="Max traversal depth for Neo4j graph search.",
    )
    reranker_weights: dict[str, float] = Field(
        default={"vector": 0.5, "graph": 0.5, "gnn": 0.0},
        description="Score fusion weights for each retrieval source.",
    )

    # --- Security ------------------------------------------------------------
    max_query_length: int = Field(
        default=1000,
        description="Max characters allowed in a user query.",
    )
    min_query_length: int = Field(
        default=2,
        description="Min characters for a valid query.",
    )
    max_queries_per_minute: int = Field(
        default=20,
        description="Session-level rate limit for user queries.",
    )
    injection_confidence_threshold: float = Field(
        default=0.7,
        description="Below this, rule engine defers to LLM for injection check.",
    )

    # --- App / Logging -------------------------------------------------------
    app_host: str = Field(default="0.0.0.0", description="Streamlit host.")
    app_port: int = Field(default=8501, description="Streamlit port.")
    log_level: str = Field(default="INFO", description="Logging level.")

    # --- Validators ----------------------------------------------------------

    @field_validator("groq_api_key")
    @classmethod
    def validate_groq_key(cls, value: str) -> str:
        """Groq keys start with 'gsk_'. Catch typos early."""
        if not value.startswith("gsk_"):
            raise ValueError(
                "GROQ_API_KEY must start with 'gsk_'. "
                "Get a free key at https://console.groq.com"
            )
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Make sure it's a real Python log level."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}, got '{value}'")
        return upper

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap_smaller_than_chunk(cls, value: int, info) -> int:
        """Overlap must be smaller than chunk size, otherwise chunks repeat."""
        chunk_size = info.data.get("chunk_size", 512)
        if value >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({value}) must be less than chunk_size ({chunk_size})"
            )
        return value

    def get_model_limits(self, model_id: str) -> dict[str, int]:
        """Get rate limits for a specific Groq model.

        Args:
            model_id: The Groq model identifier.

        Returns:
            Dict with keys 'rpm', 'tpm', 'rpd'.

        Raises:
            ValueError: If model_id is not recognized.
        """
        limits = GroqModelConfig.LIMITS.get(model_id)
        if limits is None:
            raise ValueError(
                f"Unknown model '{model_id}'. "
                f"Known models: {list(GroqModelConfig.LIMITS.keys())}"
            )
        return limits

    def setup_logging(self) -> None:
        """Configure the root logger based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
            datefmt="%H:%M:%S",
        )


def _load_settings() -> Settings:
    """Load settings, with a clear error if .env is missing the API key."""
    try:
        return Settings()
    except Exception as e:
        # If the .env file doesn't exist or GROQ_API_KEY is missing,
        # give a helpful message instead of a Pydantic stack trace.
        env_path = PROJECT_ROOT / ".env"
        if not env_path.exists():
            print(
                "\n[ERROR] No .env file found.\n"
                f"  Copy the template:  cp .env.example .env\n"
                f"  Then set your GROQ_API_KEY in {env_path}\n"
            )
        raise


# ---------------------------------------------------------------------------
# The one settings instance everything imports.
# Lazy-loaded so tests can patch env vars before import.
# ---------------------------------------------------------------------------
settings: Settings = None  # type: ignore[assignment]


def get_settings() -> Settings:
    """Get (or create) the global settings instance.

    Lazy-loads on first call so tests can set env vars before
    the settings object is created.
    """
    global settings
    if settings is None:
        settings = _load_settings()
    return settings


# ---------------------------------------------------------------------------
# CLI: python -m src.config  →  verify all connections
# ---------------------------------------------------------------------------
def _verify() -> None:
    """Quick diagnostic — checks that every external service is reachable."""
    print("\n🔍 Verifying Enterprise AI Knowledge Brain configuration...\n")

    results: dict[str, str] = {}

    # 1. Config loads at all
    try:
        cfg = get_settings()
        cfg.setup_logging()
        results["Config"] = "✅ Loaded"
    except Exception as e:
        results["Config"] = f"❌ {e}"
        # Can't continue without config
        for name, status in results.items():
            print(f"  {name}: {status}")
        sys.exit(1)

    # 2. Groq API key format
    results["Groq API Key"] = (
        f"✅ Set (starts with gsk_...{cfg.groq_api_key[-4:]})"
    )

    # 3. Neo4j connection
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password)
        )
        driver.verify_connectivity()
        driver.close()
        results["Neo4j"] = f"✅ Connected ({cfg.neo4j_uri})"
    except ImportError:
        results["Neo4j"] = "⚠️  neo4j package not installed"
    except Exception as e:
        results["Neo4j"] = f"❌ {e}"

    # 4. ChromaDB
    try:
        import chromadb

        chroma_path = str(PROJECT_ROOT / cfg.chroma_persist_dir)
        client = chromadb.PersistentClient(path=chroma_path)
        # Just verify we can create/access a collection
        client.get_or_create_collection(cfg.chroma_collection_name)
        results["ChromaDB"] = f"✅ Ready ({chroma_path})"
    except ImportError:
        results["ChromaDB"] = "⚠️  chromadb package not installed"
    except Exception as e:
        results["ChromaDB"] = f"❌ {e}"

    # 5. Sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(cfg.embedding_model)
        test_embedding = model.encode(["test"])
        dims = test_embedding.shape[1]
        results["Embeddings"] = (
            f"✅ {cfg.embedding_model} loaded ({dims} dims)"
        )
    except ImportError:
        results["Embeddings"] = "⚠️  sentence-transformers not installed"
    except Exception as e:
        results["Embeddings"] = f"❌ {e}"

    # 6. Groq API connectivity
    try:
        from groq import Groq

        client = Groq(api_key=cfg.groq_api_key)
        response = client.chat.completions.create(
            model=cfg.groq_model_extraction,
            messages=[{"role": "user", "content": "Reply with OK"}],
            max_tokens=5,
        )
        results["Groq API"] = "✅ Connected (test call succeeded)"
    except ImportError:
        results["Groq API"] = "⚠️  groq package not installed"
    except Exception as e:
        results["Groq API"] = f"❌ {e}"

    # Print results
    print("─" * 50)
    for name, status in results.items():
        print(f"  {name:20s} {status}")
    print("─" * 50)

    failures = [k for k, v in results.items() if v.startswith("❌")]
    if failures:
        print(f"\n⚠️  {len(failures)} check(s) failed. Fix them before running.\n")
        sys.exit(1)
    else:
        print("\n✅ All checks passed. Ready to go!\n")


if __name__ == "__main__":
    _verify()
