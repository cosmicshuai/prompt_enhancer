# Prompt Enhancer

A terminal UI tool that transforms rough prompt ideas into detailed, high-quality prompts through a guided conversation with Claude.

## Goal

Writing good prompts is hard. You know what you want but struggle to articulate all the details, constraints, and context that produce great AI output. Prompt Enhancer bridges that gap — you provide a rough idea, the AI asks targeted clarifying questions, and then generates a polished, comprehensive prompt you can use anywhere.

## Use Cases

- **Code review prompts** — Describe what you want reviewed and the tool asks about language, framework, concerns, and standards before producing a thorough review prompt.
- **Technical writing** — Start with "write docs for my API" and end up with a prompt that specifies audience, format, depth, and style.
- **API design** — Sketch out an idea and get a prompt that covers resources, auth, pagination, versioning, and error handling.
- **Any domain** — Create custom templates for your own workflows (marketing copy, data analysis, system design, etc.).

## How It Works

1. Select a template (built-in or custom)
2. Enter your rough prompt idea
3. The AI asks 2-4 clarifying questions, one at a time
4. An enhanced prompt is generated
5. Request changes or copy to clipboard

The conversation is iterative — you can keep refining until the prompt is exactly right.

## Architecture

```
src/prompt_enhancer/
├── __init__.py
├── __main__.py              # Entry point (python -m prompt_enhancer)
├── app.py                   # Textual App, screen orchestration
├── config.py                # Config load/save, API key env file management
├── models.py                # Template + AppConfig dataclasses
├── templates.py             # Template CRUD (JSON files)
├── builtin_templates.py     # 3 starter templates
├── api.py                   # EnhancementSession — async streaming, prompt extraction
├── screens/
│   ├── api_key_prompt.py    # First-run API key setup with validation
│   ├── main_menu.py         # Main menu
│   ├── template_list.py     # Browse/select/manage templates
│   ├── template_editor.py   # Create or edit a template
│   ├── session.py           # Conversation UI with streaming + clipboard copy
│   └── settings.py          # API key, model, max tokens
└── styles/
    └── app.tcss             # Stylesheet
```

**Key design decisions:**

- **Textual** for the TUI — rich widgets (RichLog, TextArea, OptionList) without curses boilerplate.
- **Async streaming** — responses appear in real-time via the Anthropic SDK's streaming API.
- **Template system** — each template has four fields (system prompt, domain knowledge, thinking steps, clarifying instructions) that shape how the AI guides the conversation.
- **`<enhanced_prompt>` tags** — the AI wraps its final output in tags so the tool can extract and display it separately from the conversation.
- **Local storage** — templates are individual JSON files in `~/.prompt_enhancer/templates/`. Config lives in `~/.prompt_enhancer/config.json`. The API key is stored separately in `~/.prompt_enhancer/env` with `0600` permissions.

## Dependencies

| Package | Purpose |
|---------|---------|
| [textual](https://github.com/Textualize/textual) | Terminal UI framework |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | Claude API client with async streaming |
| [pyperclip](https://github.com/asweigart/pyperclip) | Cross-platform clipboard copy |

Requires **Python 3.10+**.

## Install

```bash
# Clone the repo
git clone <repo-url>
cd prompt_enhancer

# Create a virtual environment (using uv)
uv venv --python 3.12
source .venv/bin/activate

# Install in editable mode
uv pip install -e .
```

Or with plain pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Start

```bash
prompt-enhancer
```

Or:

```bash
python -m prompt_enhancer
```

On first launch you'll be prompted to enter your Anthropic API key. The key is validated against the API before being saved.

If you already have `ANTHROPIC_API_KEY` set in your shell environment, it will be picked up automatically.

## Configuration

All user data lives in `~/.prompt_enhancer/`:

| File | Contents |
|------|----------|
| `env` | `ANTHROPIC_API_KEY='sk-ant-...'` (mode 0600) |
| `config.json` | Model selection, max tokens |
| `templates/*.json` | Template definitions |

You can change the model (Opus 4.6 / Sonnet 4.5 / Haiku 4.5) and max tokens from **Settings** in the app.
