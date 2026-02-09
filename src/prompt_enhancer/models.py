"""Data models for templates and app configuration."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Template:
    name: str
    system_prompt: str = ""
    domain_knowledge: str = ""
    thinking_steps: str = ""
    clarifying_instructions: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    builtin: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Template:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> Template:
        return cls.from_dict(json.loads(text))

    def save(self, path: Path) -> None:
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> Template:
        return cls.from_json(path.read_text())


@dataclass
class AppConfig:
    api_key: str = ""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> AppConfig:
        return cls.from_dict(json.loads(text))
