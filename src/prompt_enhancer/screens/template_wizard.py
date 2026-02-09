"""Template creation wizard — AI-guided, field-by-field template builder."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, TextArea
from textual.containers import Horizontal, Vertical, VerticalScroll

from prompt_enhancer.models import AppConfig, Template
from prompt_enhancer.wizard_api import (
    TEMPLATE_FIELDS,
    FIELD_DESCRIPTIONS,
    generate_suggestions,
)
from prompt_enhancer.templates import save_template


class TemplateWizardScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self._template_name = ""
        self._step = -1  # -1 = name entry, 0-3 = fields
        self._field_values: dict[str, str] = {}
        self._current_value: str | None = None
        self._suggestions: list[str] = []
        self._loading = False

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="wizard-container"):
            yield Static("New Template Wizard", id="wizard-title")
            yield Static("Step 1 of 5: Template Name", id="wizard-progress")
            yield Static("", id="wizard-field-description")

            with Vertical(id="wizard-name-section"):
                yield Input(
                    placeholder="Enter a name for your template...",
                    id="wizard-name-input",
                )
                yield Button(
                    "Continue", id="wizard-btn-name-continue", variant="primary"
                )

            with Vertical(id="wizard-field-section", classes="hidden"):
                yield Static("", id="wizard-field-title")
                yield Static("", id="wizard-status")

                yield Vertical(id="wizard-suggestions")

                with Horizontal(id="wizard-field-actions"):
                    yield Button(
                        "I have my own",
                        id="wizard-btn-custom",
                        variant="default",
                    )
                    yield Button(
                        "Done",
                        id="wizard-btn-done",
                        variant="primary",
                        disabled=True,
                    )

                with Vertical(id="wizard-custom-section", classes="hidden"):
                    yield TextArea("", id="wizard-custom-textarea")
                    yield Button(
                        "Use this text",
                        id="wizard-btn-use-custom",
                        variant="success",
                    )

                with Vertical(id="wizard-current-section", classes="hidden"):
                    yield Static("Current value:", id="wizard-current-label")
                    yield Static("", id="wizard-current-display")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#wizard-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "wizard-name-input":
            self._submit_name()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wizard-btn-name-continue":
            self._submit_name()
        elif event.button.id == "wizard-btn-custom":
            self._show_custom_input()
        elif event.button.id == "wizard-btn-use-custom":
            self._apply_custom_value()
        elif event.button.id == "wizard-btn-done":
            self._accept_and_advance()
        elif event.button.id and event.button.id.startswith("wizard-sug-"):
            idx = int(event.button.id.split("-")[-1])
            self._select_suggestion(idx)

    def _submit_name(self) -> None:
        name_input = self.query_one("#wizard-name-input", Input)
        name = name_input.value.strip()
        if not name:
            self.notify("Please enter a template name.", severity="warning")
            return
        self._template_name = name
        self._step = 0
        self._enter_field_step()

    def _enter_field_step(self) -> None:
        field_key, field_label = TEMPLATE_FIELDS[self._step]

        # Update progress
        self.query_one("#wizard-progress", Static).update(
            f"Step {self._step + 2} of 5: {field_label}"
        )
        self.query_one("#wizard-field-description", Static).update(
            FIELD_DESCRIPTIONS[field_key]
        )

        # Switch sections
        self.query_one("#wizard-name-section").add_class("hidden")
        self.query_one("#wizard-field-section").remove_class("hidden")

        # Reset field state
        self._current_value = None
        self._suggestions = []
        self.query_one("#wizard-field-title", Static).update(
            f"[bold]{field_label}[/bold]"
        )
        self.query_one("#wizard-btn-done", Button).disabled = True
        self.query_one("#wizard-custom-section").add_class("hidden")
        self.query_one("#wizard-current-section").add_class("hidden")

        self._fetch_suggestions()

    def _fetch_suggestions(self, refine: bool = False) -> None:
        if self._loading:
            return
        self._loading = True
        status = self.query_one("#wizard-status", Static)
        status.update("[bold yellow]Generating suggestions...[/bold yellow]")

        # Clear existing buttons
        container = self.query_one("#wizard-suggestions", Vertical)
        container.remove_children()

        self.run_worker(
            self._do_fetch_suggestions(refine), exclusive=True
        )

    async def _do_fetch_suggestions(self, refine: bool) -> None:
        field_key = TEMPLATE_FIELDS[self._step][0]
        status = self.query_one("#wizard-status", Static)

        try:
            suggestions = await generate_suggestions(
                config=self.config,
                template_name=self._template_name,
                field_key=field_key,
                completed_fields=self._field_values,
                current_value=self._current_value if refine else None,
            )
            self._suggestions = suggestions
            status.update("")
            self._render_suggestion_buttons()
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                status.update(
                    "[bold red]API Error:[/bold red] Invalid API key. "
                    "Please check Settings."
                )
            else:
                status.update(f"[bold red]Error:[/bold red] {error_msg}")
        finally:
            self._loading = False

    def _render_suggestion_buttons(self) -> None:
        container = self.query_one("#wizard-suggestions", Vertical)
        container.remove_children()

        for i, suggestion in enumerate(self._suggestions):
            # Show first ~100 chars as a preview
            label = suggestion.replace("\n", " ")
            if len(label) > 100:
                label = label[:97] + "..."
            btn = Button(
                f"  {i + 1}. {label}",
                id=f"wizard-sug-{i}",
                classes="wizard-suggestion-btn",
            )
            container.mount(btn)

    def _select_suggestion(self, idx: int) -> None:
        if idx < len(self._suggestions):
            self._current_value = self._suggestions[idx]
            self._show_current_value()
            self.query_one("#wizard-btn-done", Button).disabled = False
            self._fetch_suggestions(refine=True)

    def _show_custom_input(self) -> None:
        custom_section = self.query_one("#wizard-custom-section")
        custom_section.remove_class("hidden")
        textarea = self.query_one("#wizard-custom-textarea", TextArea)
        textarea.load_text("")
        textarea.focus()

    def _apply_custom_value(self) -> None:
        textarea = self.query_one("#wizard-custom-textarea", TextArea)
        text = textarea.text.strip()
        if not text:
            self.notify("Please enter some text.", severity="warning")
            return
        self._current_value = text
        self._show_current_value()
        self.query_one("#wizard-custom-section").add_class("hidden")
        self.query_one("#wizard-btn-done", Button).disabled = False
        self._fetch_suggestions(refine=True)

    def _show_current_value(self) -> None:
        section = self.query_one("#wizard-current-section")
        section.remove_class("hidden")
        display = self.query_one("#wizard-current-display", Static)
        display.update(self._current_value or "")

    def _accept_and_advance(self) -> None:
        if self._current_value is None:
            return
        field_key = TEMPLATE_FIELDS[self._step][0]
        self._field_values[field_key] = self._current_value

        if self._step < 3:
            self._step += 1
            self._enter_field_step()
        else:
            self._save_template()

    def _save_template(self) -> None:
        template = Template(
            name=self._template_name,
            system_prompt=self._field_values.get("system_prompt", ""),
            domain_knowledge=self._field_values.get("domain_knowledge", ""),
            thinking_steps=self._field_values.get("thinking_steps", ""),
            clarifying_instructions=self._field_values.get(
                "clarifying_instructions", ""
            ),
        )
        save_template(template)
        self.notify(f"Template '{template.name}' created!")
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
