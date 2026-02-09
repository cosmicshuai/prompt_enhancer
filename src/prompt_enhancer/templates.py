"""Template CRUD operations using JSON files in ~/.prompt_enhancer/templates/."""

from __future__ import annotations

from pathlib import Path

from prompt_enhancer.models import Template
from prompt_enhancer.builtin_templates import BUILTIN_TEMPLATES

TEMPLATES_DIR = Path.home() / ".prompt_enhancer" / "templates"


def _ensure_builtins() -> None:
    """Write builtin templates to disk if they don't exist."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for template in BUILTIN_TEMPLATES:
        path = TEMPLATES_DIR / f"{template.id}.json"
        if not path.exists():
            template.save(path)


def list_templates() -> list[Template]:
    _ensure_builtins()
    templates = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            templates.append(Template.load(path))
        except (ValueError, KeyError):
            continue
    return templates


def get_template(template_id: str) -> Template | None:
    _ensure_builtins()
    path = TEMPLATES_DIR / f"{template_id}.json"
    if path.exists():
        return Template.load(path)
    return None


def save_template(template: Template) -> Template:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    path = TEMPLATES_DIR / f"{template.id}.json"
    template.save(path)
    return template


def delete_template(template_id: str) -> bool:
    path = TEMPLATES_DIR / f"{template_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
