"""Template editor screen for creating/editing templates."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, Button, Input, TextArea
from textual.containers import Horizontal, Vertical, VerticalScroll

from prompt_enhancer.models import Template
from prompt_enhancer.templates import save_template


class TemplateEditorScreen(ModalScreen[bool]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, template: Template | None = None) -> None:
        super().__init__()
        self.template = template
        self.is_edit = template is not None

    def compose(self) -> ComposeResult:
        title = "Edit Template" if self.is_edit else "New Template"
        with Vertical(id="editor-container"):
            yield Static(title, id="editor-title")
            with VerticalScroll(id="editor-scroll"):
                yield Static("Name", classes="field-label")
                yield Input(
                    value=self.template.name if self.is_edit else "",
                    placeholder="Template name",
                    id="input-name",
                )
                yield Static("System Prompt", classes="field-label")
                yield TextArea(
                    self.template.system_prompt if self.is_edit else "",
                    id="ta-system-prompt",
                )
                yield Static("Domain Knowledge", classes="field-label")
                yield TextArea(
                    self.template.domain_knowledge if self.is_edit else "",
                    id="ta-domain-knowledge",
                )
                yield Static("Thinking Steps", classes="field-label")
                yield TextArea(
                    self.template.thinking_steps if self.is_edit else "",
                    id="ta-thinking-steps",
                )
                yield Static("Clarifying Instructions", classes="field-label")
                yield TextArea(
                    self.template.clarifying_instructions if self.is_edit else "",
                    id="ta-clarifying-instructions",
                )
            with Horizontal(id="editor-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save()
        elif event.button.id == "btn-cancel":
            self.dismiss(False)

    def _save(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        if not name:
            self.notify("Template name is required.", severity="error")
            return

        if self.is_edit:
            self.template.name = name
            self.template.system_prompt = self.query_one(
                "#ta-system-prompt", TextArea
            ).text
            self.template.domain_knowledge = self.query_one(
                "#ta-domain-knowledge", TextArea
            ).text
            self.template.thinking_steps = self.query_one(
                "#ta-thinking-steps", TextArea
            ).text
            self.template.clarifying_instructions = self.query_one(
                "#ta-clarifying-instructions", TextArea
            ).text
            save_template(self.template)
        else:
            template = Template(
                name=name,
                system_prompt=self.query_one("#ta-system-prompt", TextArea).text,
                domain_knowledge=self.query_one(
                    "#ta-domain-knowledge", TextArea
                ).text,
                thinking_steps=self.query_one("#ta-thinking-steps", TextArea).text,
                clarifying_instructions=self.query_one(
                    "#ta-clarifying-instructions", TextArea
                ).text,
            )
            save_template(template)

        self.notify(f"Template '{name}' saved.")
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
