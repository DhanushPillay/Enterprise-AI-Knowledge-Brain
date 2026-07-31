"""Tests for src/config.py — settings loading and validation."""

import os

import pytest

from src.config import GroqModelConfig, Settings


class TestGroqModelConfig:
    """Verify the model constants and limits are correct."""

    def test_model_ids_are_strings(self) -> None:
        assert isinstance(GroqModelConfig.LLAMA_70B, str)
        assert isinstance(GroqModelConfig.LLAMA_8B, str)

    def test_both_models_have_limits(self) -> None:
        for model_id in [GroqModelConfig.LLAMA_70B, GroqModelConfig.LLAMA_8B]:
            limits = GroqModelConfig.LIMITS[model_id]
            assert "rpm" in limits
            assert "tpm" in limits
            assert "rpd" in limits

    def test_8b_has_higher_daily_limit_than_70b(self) -> None:
        """8B is for bulk work — it must have a higher daily cap."""
        rpd_70b = GroqModelConfig.LIMITS[GroqModelConfig.LLAMA_70B]["rpd"]
        rpd_8b = GroqModelConfig.LIMITS[GroqModelConfig.LLAMA_8B]["rpd"]
        assert rpd_8b > rpd_70b


class TestSettingsValidation:
    """Verify that Pydantic catches bad config early."""

    def _make_env(self, overrides: dict[str, str] | None = None) -> dict[str, str]:
        """Build a minimal valid env dict, then apply overrides."""
        base = {"GROQ_API_KEY": "gsk_test_key_1234567890abcdef"}
        if overrides:
            base.update(overrides)
        return base

    def test_valid_config_loads(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env = self._make_env()
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        cfg = Settings()
        assert cfg.groq_api_key == "gsk_test_key_1234567890abcdef"

    def test_missing_api_key_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(Exception):
            Settings()

    def test_bad_api_key_prefix_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "bad_prefix_key")
        with pytest.raises(Exception, match="gsk_"):
            Settings()

    def test_invalid_log_level_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env = self._make_env({"LOG_LEVEL": "VERBOSE"})
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        with pytest.raises(Exception, match="LOG_LEVEL"):
            Settings()

    def test_overlap_bigger_than_chunk_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env = self._make_env({"CHUNK_SIZE": "100", "CHUNK_OVERLAP": "200"})
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        with pytest.raises(Exception, match="chunk_overlap"):
            Settings()

    def test_defaults_are_sensible(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env = self._make_env()
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        cfg = Settings()

        assert cfg.chunk_size == 512
        assert cfg.chunk_overlap == 50
        assert cfg.neo4j_uri == "bolt://localhost:7687"
        assert cfg.embedding_model == "all-MiniLM-L6-v2"
        assert cfg.embedding_dimensions == 384
        assert cfg.vector_search_top_k == 10
        assert cfg.log_level == "INFO"

    def test_get_model_limits_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env = self._make_env()
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        cfg = Settings()
        limits = cfg.get_model_limits(GroqModelConfig.LLAMA_70B)
        assert limits["rpm"] == 30

    def test_get_model_limits_unknown_model(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env = self._make_env()
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        cfg = Settings()
        with pytest.raises(ValueError, match="Unknown model"):
            cfg.get_model_limits("nonexistent-model")
