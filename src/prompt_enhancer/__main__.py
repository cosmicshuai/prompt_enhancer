"""Entry point for python -m prompt_enhancer."""

from prompt_enhancer.app import PromptEnhancerApp


def main():
    app = PromptEnhancerApp()
    app.run()


if __name__ == "__main__":
    main()
