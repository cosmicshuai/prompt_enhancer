"""First-run screen that prompts the user for their Anthropic API key."""

from __future__ import annotations

import anthropic
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input
from textual.containers import Vertical


class ApiKeyPromptScreen(ModalScreen[str]):
    """Blocks until the user provides a valid API key."""

    def compose(self) -> ComposeResult:
        with Vertical(id="api-key-prompt-container"):
            yield Static("Welcome to Prompt Enhancer", id="api-key-prompt-title")
            yield Static(
                "To get started, enter your Anthropic API key.\n"
                "You can find it at https://console.anthropic.com/settings/keys",
                id="api-key-prompt-desc",
            )
            yield Input(
                placeholder="sk-ant-...",
                password=True,
                id="api-key-prompt-input",
            )
            yield Static("", id="api-key-prompt-status")
            yield Button("Continue", id="btn-api-key-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#api-key-prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "api-key-prompt-input":
            self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-api-key-submit":
            self._submit()

    def _submit(self) -> None:
        api_key = self.query_one("#api-key-prompt-input", Input).value.strip()
        if not api_key:
            self._set_status("Please enter an API key.", error=True)
            return
        self.run_worker(self._validate_key(api_key), exclusive=True)

    async def _validate_key(self, api_key: str) -> None:
        status = self.query_one("#api-key-prompt-status", Static)
        btn = self.query_one("#btn-api-key-submit", Button)
        btn.disabled = True
        btn.label = "Validating..."
        status.update("[dim]Checking API key...[/dim]")

        try:
            client = anthropic.AsyncAnthropic(api_key=api_key)
            await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            self.dismiss(api_key)
        except anthropic.AuthenticationError:
            self._set_status("Invalid API key. Please check and try again.", error=True)
        except Exception as e:
            self._set_status(f"Connection error: {e}", error=True)
        finally:
            btn.disabled = False
            btn.label = "Continue"

    def _set_status(self, text: str, error: bool = False) -> None:
        status = self.query_one("#api-key-prompt-status", Static)
        if error:
            status.update(f"[bold red]{text}[/bold red]")
        else:
            status.update(text)
