"""
Agent configuration loader.
Python equivalent of config.ts

Config priority: JSON file < environment variables < function overrides
"""

import os
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any

CONFIG_FILE = "agent.config.json"

@dataclass
class AgentConfig:
    api_key: str = ""
    model: str = "anthropic/claude-haiku-4.5"
    name: str = "My Agent"
    system_prompt: str = (
        "You are a helpful coding assistant. You can read, write, and edit files, "
        "run shell commands, search code, and fetch web pages. "
        "Working directory: {cwd}"
    )
    max_steps: int = 20
    max_cost: float = 1.0
    session_dir: str = ".sessions"
    session_enabled: bool = True
    output_mode: str = "text"  # "text" | "json" | "quiet"
    validate_output: bool = False
    output_schema: Optional[dict] = None


def load_config(overrides: dict[str, Any], *, skip_api_key: bool = False) -> AgentConfig:
    """
    Load config from agent.config.json, env vars, and overrides.
    Priority: overrides > env vars > config file > defaults
    """
    config = AgentConfig()

    # Load from JSON config file if it exists
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            raw = json.loads(config_path.read_text())
            config.model = raw.get("model", config.model)
            config.name = raw.get("name", config.name)
            config.system_prompt = raw.get("systemPrompt", config.system_prompt)
            config.max_steps = int(raw.get("maxSteps", config.max_steps))
            config.max_cost = float(raw.get("maxCost", config.max_cost))
            config.session_dir = raw.get("sessionDir", config.session_dir)
            config.session_enabled = bool(raw.get("sessionEnabled", config.session_enabled))
            config.output_mode = raw.get("outputMode", config.output_mode)
            config.validate_output = bool(raw.get("validateOutput", config.validate_output))
            if raw.get("outputSchema"):
                config.output_schema = raw["outputSchema"]
        except (json.JSONDecodeError, ValueError):
            pass

    # Override from environment variables
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        config.api_key = api_key
    env_model = os.environ.get("AGENT_MODEL")
    if env_model:
        config.model = env_model
    env_max_steps = os.environ.get("AGENT_MAX_STEPS")
    if env_max_steps:
        config.max_steps = int(env_max_steps)
    env_max_cost = os.environ.get("AGENT_MAX_COST")
    if env_max_cost:
        config.max_cost = float(env_max_cost)

    # Apply overrides
    if "api_key" in overrides:
        config.api_key = overrides["api_key"]
    if "model" in overrides:
        config.model = overrides["model"]
    if "max_steps" in overrides:
        config.max_steps = int(overrides["max_steps"])
    if "max_cost" in overrides:
        config.max_cost = float(overrides["max_cost"])
    if "output_mode" in overrides:
        config.output_mode = overrides["output_mode"]
    if "session_enabled" in overrides:
        config.session_enabled = bool(overrides["session_enabled"])
    if "validate_output" in overrides:
        config.validate_output = bool(overrides["validate_output"])
    if "output_schema" in overrides:
        config.output_schema = overrides["output_schema"]

    if not config.api_key and not skip_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required. "
            "Get your key at https://openrouter.ai/keys and set it as an environment variable."
        )

    return config
