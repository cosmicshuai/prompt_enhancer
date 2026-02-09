"""Main menu screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Center, Vertical


class MainMenuScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="menu-container"):
                yield Static("Prompt Enhancer", id="menu-title")
                yield Static(
                    "Transform simple prompts into detailed, high-quality prompts",
                    id="menu-subtitle",
                )
                yield Button("Enhance a Prompt", id="btn-enhance", variant="primary")
                yield Button("Manage Templates", id="btn-templates", variant="default")
                yield Button("Settings", id="btn-settings", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-enhance":
            from prompt_enhancer.screens.template_list import TemplateListScreen

            self.app.push_screen(TemplateListScreen(mode="select"))
        elif event.button.id == "btn-templates":
            from prompt_enhancer.screens.template_list import TemplateListScreen

            self.app.push_screen(TemplateListScreen(mode="manage"))
        elif event.button.id == "btn-settings":
            from prompt_enhancer.screens.settings import SettingsScreen

            self.app.push_screen(SettingsScreen())

    def action_quit(self) -> None:
        self.app.exit()
