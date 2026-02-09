"""Session screen — the core enhancement conversation experience."""

from __future__ import annotations

import pyperclip
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, TextArea
from textual.containers import Vertical

from prompt_enhancer.models import Template, AppConfig
from prompt_enhancer.api import EnhancementSession


class SessionScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back"),
        Binding("ctrl+y", "copy_to_clipboard", "Copy Prompt", show=True),
    ]

    def __init__(self, template: Template, config: AppConfig) -> None:
        super().__init__()
        self.template = template
        self.config = config
        self.session = EnhancementSession(template, config)
        self._streaming = False
        self._enhanced_prompt: str | None = None
        self._first_response_received = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="session-container"):
            yield Static(
                f"Enhancing with: {self.template.name}", id="session-title"
            )
            yield Static(
                "Describe the prompt you want to create",
                id="session-welcome",
            )
            yield RichLog(id="conversation-log", wrap=True, markup=True, classes="hidden")
            yield Static("", id="streaming-indicator")
            with Vertical(id="enhanced-section", classes="hidden"):
                yield Static("Enhanced Prompt:", id="enhanced-label")
                yield TextArea(
                    "", id="enhanced-prompt-display", read_only=True
                )
                yield Button(
                    "Copy to Clipboard",
                    id="btn-copy",
                    variant="success",
                    disabled=True,
                )
            yield Input(
                placeholder="What kind of prompt do you need? Describe your idea...",
                id="session-input",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#session-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "session-input":
            self._handle_send()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-copy":
            self._copy_to_clipboard()

    def _handle_send(self) -> None:
        if self._streaming:
            return
        input_widget = self.query_one("#session-input", Input)
        text = input_widget.value.strip()
        if not text:
            return
        input_widget.value = ""

        # Hide welcome, show conversation log
        self.query_one("#session-welcome").add_class("hidden")
        self.query_one("#conversation-log").remove_class("hidden")

        self.run_worker(self._stream_response(text), exclusive=True)

    async def _stream_response(self, user_text: str) -> None:
        self._streaming = True
        input_widget = self.query_one("#session-input", Input)
        input_widget.disabled = True

        log = self.query_one("#conversation-log", RichLog)
        indicator = self.query_one("#streaming-indicator", Static)

        log.write(f"\n[bold cyan]You:[/bold cyan] {user_text}")
        indicator.update("[bold yellow]Assistant is typing...[/bold yellow]")

        response_text = ""
        try:
            async for chunk in self.session.send_message(user_text):
                response_text += chunk
                preview = response_text[-200:] if len(response_text) > 200 else response_text
                indicator.update(f"[dim]{preview}[/dim]")

            indicator.update("")
            log.write(f"[bold green]Assistant:[/bold green] {response_text}")

            # Check for enhanced prompt
            enhanced = self.session.extract_enhanced_prompt()
            if enhanced:
                self._enhanced_prompt = enhanced
                self.query_one("#enhanced-section").remove_class("hidden")
                display = self.query_one("#enhanced-prompt-display", TextArea)
                display.load_text(enhanced)
                copy_btn = self.query_one("#btn-copy", Button)
                copy_btn.disabled = False
                input_widget.placeholder = "Request changes, or press Escape to go back"
                self.notify(
                    "Enhanced prompt ready! You can copy it or request changes."
                )
            else:
                self._first_response_received = True
                input_widget.placeholder = "Answer the question above..."
        except Exception as e:
            indicator.update("")
            error_msg = str(e)
            if (
                "authentication" in error_msg.lower()
                or "api key" in error_msg.lower()
            ):
                log.write(
                    "[bold red]API Error:[/bold red] Invalid API key. "
                    "Please check Settings."
                )
            else:
                log.write(f"[bold red]Error:[/bold red] {error_msg}")
        finally:
            self._streaming = False
            input_widget.disabled = False
            input_widget.focus()

    def _copy_to_clipboard(self) -> None:
        if self._enhanced_prompt:
            try:
                pyperclip.copy(self._enhanced_prompt)
                self.notify("Copied to clipboard!")
            except pyperclip.PyperclipException:
                self.notify(
                    "Could not copy to clipboard. Is a clipboard tool available?",
                    severity="error",
                )

    def action_copy_to_clipboard(self) -> None:
        self._copy_to_clipboard()

    def action_go_back(self) -> None:
        self.app.pop_screen()
