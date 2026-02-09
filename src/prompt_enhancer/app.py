"""Main Textual application."""

from pathlib import Path

from textual.app import App

from prompt_enhancer.screens.main_menu import MainMenuScreen

CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"


class PromptEnhancerApp(App):
    TITLE = "Prompt Enhancer"
    SUB_TITLE = "AI-powered prompt refinement"
    CSS_PATH = CSS_PATH

    def on_mount(self) -> None:
        self.theme = "tokyo-night"

        from prompt_enhancer.config import load_config, save_config

        config = load_config()
        self.push_screen(MainMenuScreen())

        if not config.api_key:
            from prompt_enhancer.screens.api_key_prompt import ApiKeyPromptScreen

            def on_key_entered(api_key: str) -> None:
                config.api_key = api_key
                save_config(config)
                self.notify("API key saved. You're all set!")

            self.push_screen(ApiKeyPromptScreen(), callback=on_key_entered)
