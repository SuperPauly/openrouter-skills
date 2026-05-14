"""
TUI agent configuration.
Python equivalent of config.ts (TUI version with display settings).
"""

import os
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any

CONFIG_FILE = "agent.config.json"


@dataclass
class LoaderConfig:
    text: str = "Thinking"
    style: str = "gradient"  # "spinner" | "minimal" | "gradient"


@dataclass
class DisplayConfig:
    tool_display: str = "grouped"   # "emoji" | "grouped" | "minimal" | "hidden"
    reasoning: bool = False
    input_style: str = "block"      # "block" | "line" | "plain"
    loader: LoaderConfig = field(default_factory=LoaderConfig)


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
    show_banner: bool = True
    display: DisplayConfig = field(default_factory=DisplayConfig)


def load_config(overrides: dict[str, Any], *, skip_api_key: bool = False) -> AgentConfig:
    """
    Load config: agent.config.json → env vars → overrides.
    """
    config = AgentConfig()

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
            config.show_banner = bool(raw.get("showBanner", config.show_banner))
            d = raw.get("display", {})
            if d:
                config.display.tool_display = d.get("toolDisplay", config.display.tool_display)
                config.display.reasoning = bool(d.get("reasoning", config.display.reasoning))
                config.display.input_style = d.get("inputStyle", config.display.input_style)
                loader = d.get("loader", {})
                if loader:
                    config.display.loader.text = loader.get("text", config.display.loader.text)
                    config.display.loader.style = loader.get("style", config.display.loader.style)
        except (json.JSONDecodeError, ValueError):
            pass

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        config.api_key = api_key
    env_model = os.environ.get("AGENT_MODEL")
    if env_model:
        config.model = env_model

    for key, val in overrides.items():
        if key == "model":
            config.model = str(val)
        elif key == "api_key":
            config.api_key = str(val)

    if not config.api_key and not skip_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required. "
            "Get your key at https://openrouter.ai/keys"
        )

    return config
