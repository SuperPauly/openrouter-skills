"""
Tests for config loading.
Python equivalent of test/agent.test.ts
"""

import os
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import load_config, AgentConfig


class TestLoadConfig:
    def _clear_env(self, monkeypatch):
        for key in ["OPENROUTER_API_KEY", "AGENT_MODEL", "AGENT_MAX_STEPS", "AGENT_MAX_COST"]:
            monkeypatch.delenv(key, raising=False)

    def test_defaults_are_correct(self, monkeypatch, tmp_path):
        self._clear_env(monkeypatch)
        monkeypatch.chdir(tmp_path)  # ensure no agent.config.json found
        config = load_config({}, skip_api_key=True)
        assert config.model == "anthropic/claude-haiku-4.5"
        assert config.max_steps == 20
        assert config.max_cost == 1.0
        assert config.session_enabled is True
        assert config.output_mode == "text"
        assert config.name == "My Agent"
        assert config.session_dir == ".sessions"
        assert "coding assistant" in config.system_prompt

    def test_env_vars_override_defaults(self, monkeypatch, tmp_path):
        self._clear_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        monkeypatch.setenv("AGENT_MODEL", "openai/gpt-4o")
        monkeypatch.setenv("AGENT_MAX_STEPS", "50")
        monkeypatch.setenv("AGENT_MAX_COST", "5.0")
        config = load_config({})
        assert config.api_key == "test-key-123"
        assert config.model == "openai/gpt-4o"
        assert config.max_steps == 50
        assert config.max_cost == 5.0

    def test_overrides_take_precedence_over_env_vars(self, monkeypatch, tmp_path):
        self._clear_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
        monkeypatch.setenv("AGENT_MODEL", "openai/gpt-4o")
        config = load_config({"model": "google/gemini-2.0-flash-001", "output_mode": "json"})
        assert config.model == "google/gemini-2.0-flash-001"
        assert config.output_mode == "json"
        assert config.api_key == "env-key"

    def test_skip_api_key_prevents_error(self, monkeypatch, tmp_path):
        self._clear_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        config = load_config({}, skip_api_key=True)  # must not raise
        assert config is not None

    def test_raises_when_api_key_missing(self, monkeypatch, tmp_path):
        self._clear_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
            load_config({})
