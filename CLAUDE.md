# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Prompt Enhancer is a terminal UI (TUI) app that transforms rough prompt ideas into detailed, high-quality prompts through a guided multi-turn conversation with Claude. Built with Textual and the Anthropic Python SDK.

## Development Commands

```bash
# Setup (uses uv)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .

# Run the app
prompt-enhancer
# or
python -m prompt_enhancer
```

There are no tests, linter, or formatter configured in this project.

## Architecture

**Screen-based navigation** — The app uses Textual's screen stack (`push_screen`/`pop_screen`) for navigation. Screens are imported lazily inside event handlers to avoid circular imports.

**Flow:** `App.on_mount` → `MainMenuScreen` → `TemplateListScreen(mode="select"|"manage")` → `SessionScreen` (for enhancement), `TemplateWizardScreen` (new template creation), or `TemplateEditorScreen` (modal, for editing existing). First-run pushes `ApiKeyPromptScreen` modal on top.

**`EnhancementSession` (api.py)** — Core logic class. Manages the multi-turn conversation with Claude via async streaming. Builds a system prompt by concatenating a template's four fields (system_prompt, domain_knowledge, thinking_steps, clarifying_instructions) with hardcoded `PROCESS_INSTRUCTIONS`. Uses `<enhanced_prompt>` XML tags as a structured extraction boundary — the AI wraps its final output in these tags, and `extract_enhanced_prompt()` regex-parses the last match.

**Template system** — Templates are dataclasses (`models.py`) persisted as individual JSON files in `~/.prompt_enhancer/templates/`. Three builtin templates (Code Review, Technical Writing, API Design) are auto-written to disk on first `list_templates()` call. Builtins have fixed UUIDs (`builtin-*`) and cannot be edited or deleted.

**Config split** — API key is stored separately in `~/.prompt_enhancer/env` (mode 0600) and loaded into `os.environ`. Model/max_tokens go to `~/.prompt_enhancer/config.json`. The `config.py` module handles this split transparently.

**Template Wizard** — `TemplateWizardScreen` (`screens/template_wizard.py`) is a full `Screen` (not modal) that guides users through creating a template field by field. Uses `wizard_api.py` for non-streaming Claude API calls that generate `<suggestion>` XML-tagged options. The wizard is a 5-step flow: name entry, then each of the 4 template fields. Each field step shows AI-generated suggestion buttons, a "I have my own" custom input option, and iterative refinement. The wizard API (`wizard_api.py`) is deliberately separate from `api.py` because it uses stateless request/response calls rather than streaming multi-turn conversations.

**Streaming UI** — `SessionScreen._stream_response` uses `run_worker` with `exclusive=True` for async streaming. During streaming, a truncated preview appears in a `Static` widget; on completion, the full response is written to a `RichLog`. If `<enhanced_prompt>` tags are detected, the extracted prompt populates a read-only `TextArea` with a clipboard copy button.

## Key Conventions

- **Python 3.10+**, uses `from __future__ import annotations` for modern type syntax
- **Hatchling** build backend, source layout under `src/prompt_enhancer/`
- Styles live in a single TCSS file (`styles/app.tcss`), using Textual's design system variables (`$primary`, `$panel`, etc.) with the `tokyo-night` theme
- Widget IDs follow the pattern `#screen-name-element` (e.g., `#session-input`, `#template-list-title`)
- `TemplateEditorScreen` is a `ModalScreen[bool]`; `ApiKeyPromptScreen` is a `ModalScreen[str]` — they use `dismiss()` to return typed results
- `TemplateWizardScreen` is a regular `Screen` (not modal) — it uses `push_screen`/`pop_screen` for navigation and `on_screen_resume` on the parent `TemplateListScreen` to refresh the list on return

## Testing the Template Wizard

The wizard requires a valid API key (it makes live Claude API calls). To test:

1. Run `prompt-enhancer` and ensure your API key is set in Settings
2. Go to "Manage Templates" → click "New Template"
3. Enter a template name (e.g., "Data Analysis") → click "Continue" or press Enter
4. For each of the 4 fields (System Prompt, Domain Knowledge, Thinking Steps, Clarifying Instructions):
   - Verify AI-generated suggestions appear as clickable buttons
   - Click a suggestion → verify the "Current value" section appears and new refined suggestions load
   - Click "I have my own" → type custom text → click "Use this text" → verify refinement triggers
   - Click "Done" → verify it advances to the next field
5. After all 4 fields → verify the template saves and appears in the template list
6. Verify "Edit" on existing (non-builtin) templates still opens the old `TemplateEditorScreen`
7. Press Escape at any wizard step → verify clean return to the template list
8. Try clicking "New Template" without an API key configured → verify it shows an error and redirects to Settings
