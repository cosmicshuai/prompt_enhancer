"""Template list screen for selecting or managing templates."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical

from prompt_enhancer.templates import list_templates, delete_template


class TemplateListScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, mode: str = "select") -> None:
        super().__init__()
        self.mode = mode  # "select" or "manage"
        self._templates = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="template-list-container"):
            title = (
                "Select a Template" if self.mode == "select" else "Manage Templates"
            )
            yield Static(title, id="template-list-title")
            yield OptionList(id="template-option-list")
            with Horizontal(id="template-list-buttons"):
                if self.mode == "manage":
                    yield Button("New Template", id="btn-new-template", variant="primary")
                    yield Button("Edit", id="btn-edit-template", variant="default")
                    yield Button("Delete", id="btn-delete-template", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._templates = list_templates()
        option_list = self.query_one("#template-option-list", OptionList)
        option_list.clear_options()
        for t in self._templates:
            label = f"{'[builtin] ' if t.builtin else ''}{t.name}"
            option_list.add_option(Option(label, id=t.id))

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if self.mode == "select":
            self._start_session(event.option.id)

    def _start_session(self, template_id: str) -> None:
        from prompt_enhancer.config import load_config

        config = load_config()
        if not config.api_key:
            self.notify("Please set your API key in Settings first.", severity="error")
            from prompt_enhancer.screens.settings import SettingsScreen

            self.app.push_screen(SettingsScreen())
            return

        from prompt_enhancer.templates import get_template
        from prompt_enhancer.screens.session import SessionScreen

        template = get_template(template_id)
        if template:
            self.app.push_screen(SessionScreen(template=template, config=config))

    def on_screen_resume(self) -> None:
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-template":
            from prompt_enhancer.config import load_config

            config = load_config()
            if not config.api_key:
                self.notify(
                    "Please set your API key in Settings first.",
                    severity="error",
                )
                from prompt_enhancer.screens.settings import SettingsScreen

                self.app.push_screen(SettingsScreen())
                return

            from prompt_enhancer.screens.template_wizard import (
                TemplateWizardScreen,
            )

            self.app.push_screen(TemplateWizardScreen(config))
        elif event.button.id == "btn-edit-template":
            self._edit_selected()
        elif event.button.id == "btn-delete-template":
            self._delete_selected()

    def _edit_selected(self) -> None:
        option_list = self.query_one("#template-option-list", OptionList)
        if option_list.highlighted is not None:
            idx = option_list.highlighted
            if idx < len(self._templates):
                template = self._templates[idx]
                if template.builtin:
                    self.notify("Cannot edit built-in templates.", severity="warning")
                    return
                from prompt_enhancer.screens.template_editor import (
                    TemplateEditorScreen,
                )

                self.app.push_screen(
                    TemplateEditorScreen(template=template),
                    callback=lambda _: self._refresh_list(),
                )

    def _delete_selected(self) -> None:
        option_list = self.query_one("#template-option-list", OptionList)
        if option_list.highlighted is not None:
            idx = option_list.highlighted
            if idx < len(self._templates):
                template = self._templates[idx]
                if template.builtin:
                    self.notify(
                        "Cannot delete built-in templates.", severity="warning"
                    )
                    return
                delete_template(template.id)
                self.notify(f"Deleted '{template.name}'.")
                self._refresh_list()

    def action_go_back(self) -> None:
        self.app.pop_screen()
