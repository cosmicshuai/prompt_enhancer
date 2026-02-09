"""Settings screen for API key, model, and max tokens configuration."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Select
from textual.containers import Horizontal, Vertical

from prompt_enhancer.config import (
    load_config,
    save_general_config,
    _save_env_api_key,
)

MODELS = [
    ("Claude Sonnet 4.5", "claude-sonnet-4-5-20250929"),
    ("Claude Haiku 4.5", "claude-haiku-4-5-20251001"),
    ("Claude Opus 4.6", "claude-opus-4-6"),
]


class SettingsScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config = load_config()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings-outer"):
            with Vertical(id="settings-container"):
                yield Static("Settings", id="settings-title")

                with Vertical(id="settings-api-key-section"):
                    yield Static("API Key", classes="field-label")
                    yield Input(
                        value=self._config.api_key,
                        placeholder="sk-ant-...",
                        password=True,
                        id="input-api-key",
                    )
                    with Horizontal(id="settings-api-key-buttons"):
                        yield Button(
                            "Update API Key",
                            id="btn-save-api-key",
                            variant="primary",
                        )

                with Vertical(id="settings-general-section"):
                    yield Static("General", classes="field-label")
                    yield Static("Model", classes="field-label")
                    yield Select(
                        [(name, val) for name, val in MODELS],
                        value=self._config.model,
                        id="select-model",
                    )
                    yield Static("Max Tokens", classes="field-label")
                    yield Input(
                        value=str(self._config.max_tokens),
                        placeholder="4096",
                        id="input-max-tokens",
                        type="integer",
                    )
                    with Horizontal(id="settings-general-buttons"):
                        yield Button("Save", id="btn-save-general", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-api-key":
            self._save_api_key()
        elif event.button.id == "btn-save-general":
            self._save_general()

    def _save_api_key(self) -> None:
        api_key = self.query_one("#input-api-key", Input).value.strip()
        _save_env_api_key(api_key)
        self.notify("API key updated.")

    def _save_general(self) -> None:
        model_select = self.query_one("#select-model", Select)
        model = model_select.value if model_select.value != Select.BLANK else self._config.model
        max_tokens_str = self.query_one("#input-max-tokens", Input).value.strip()

        try:
            max_tokens = int(max_tokens_str) if max_tokens_str else 4096
        except ValueError:
            self.notify("Max tokens must be a number.", severity="error")
            return

        if max_tokens < 1:
            self.notify("Max tokens must be positive.", severity="error")
            return

        save_general_config(model, max_tokens)
        self.notify("Settings saved.")

    def action_go_back(self) -> None:
        self.app.pop_screen()
