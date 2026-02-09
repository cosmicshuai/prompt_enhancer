"""Configuration management for ~/.prompt_enhancer/config.json.

API key is stored in ~/.prompt_enhancer/env as ANTHROPIC_API_KEY and loaded
into the process environment. On load we also check the existing env var
so users who export it in their shell profile don't need to configure it again.
"""

from __future__ import annotations

import os
from pathlib import Path

from prompt_enhancer.models import AppConfig

CONFIG_DIR = Path.home() / ".prompt_enhancer"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / "env"


def _load_env_api_key() -> str:
    """Read API key from the env file, falling back to the environment."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                val = line.split("=", 1)[1].strip().strip("'\"")
                if val:
                    os.environ.setdefault("ANTHROPIC_API_KEY", val)
                    return val
    return os.environ.get("ANTHROPIC_API_KEY", "")


def _save_env_api_key(api_key: str) -> None:
    """Persist API key to ~/.prompt_enhancer/env and the current process."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(f"ANTHROPIC_API_KEY='{api_key}'\n")
    ENV_FILE.chmod(0o600)
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key


def load_config() -> AppConfig:
    api_key = _load_env_api_key()
    config = AppConfig(api_key=api_key)
    if CONFIG_FILE.exists():
        try:
            saved = AppConfig.from_json(CONFIG_FILE.read_text())
            config.model = saved.model
            config.max_tokens = saved.max_tokens
        except (ValueError, KeyError):
            pass
    return config


def save_general_config(model: str, max_tokens: int) -> None:
    """Write only model and max_tokens to config.json (does not touch the env file)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    non_secret = AppConfig(api_key="", model=model, max_tokens=max_tokens)
    CONFIG_FILE.write_text(non_secret.to_json())


def save_config(config: AppConfig) -> None:
    _save_env_api_key(config.api_key)
    save_general_config(config.model, config.max_tokens)
