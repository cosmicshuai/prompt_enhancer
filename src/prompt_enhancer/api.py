"""Anthropic API integration for prompt enhancement sessions."""

from __future__ import annotations

import re
from typing import AsyncIterator

import anthropic

from prompt_enhancer.models import Template, AppConfig

PROCESS_INSTRUCTIONS = """\
You are helping the user craft a high-quality, detailed prompt. Follow this process:

1. The user will provide a rough prompt idea.
2. Ask ONE clarifying question at a time to better understand their needs. Wait for their response before asking the next question. Keep questions focused and specific.
3. After gathering enough context (typically 2-4 questions), generate the enhanced prompt.
4. When you produce the final enhanced prompt, wrap it in <enhanced_prompt> tags like this:
   <enhanced_prompt>
   Your enhanced prompt here...
   </enhanced_prompt>
5. After presenting the enhanced prompt, ask if the user wants any changes. If they do, produce a revised version (again wrapped in <enhanced_prompt> tags).

Important: Only wrap the final enhanced prompt in the tags, not your conversational responses or questions."""


class EnhancementSession:
    """Manages a multi-turn conversation for prompt enhancement."""

    def __init__(self, template: Template, config: AppConfig):
        self.template = template
        self.config = config
        self.messages: list[dict] = []
        self._last_assistant_text = ""
        # Pass explicit key if set, otherwise let the SDK read ANTHROPIC_API_KEY
        self._client = anthropic.AsyncAnthropic(
            api_key=config.api_key or None
        )

    def _build_system_prompt(self) -> str:
        parts = []
        if self.template.system_prompt:
            parts.append(self.template.system_prompt)
        if self.template.domain_knowledge:
            parts.append(f"Domain Knowledge:\n{self.template.domain_knowledge}")
        if self.template.thinking_steps:
            parts.append(f"Thinking Steps:\n{self.template.thinking_steps}")
        if self.template.clarifying_instructions:
            parts.append(
                f"Clarifying Instructions:\n{self.template.clarifying_instructions}"
            )
        parts.append(PROCESS_INSTRUCTIONS)
        return "\n\n".join(parts)

    async def send_message(self, user_text: str) -> AsyncIterator[str]:
        """Send a user message and yield streaming response chunks."""
        self.messages.append({"role": "user", "content": user_text})
        self._last_assistant_text = ""

        async with self._client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self._build_system_prompt(),
            messages=self.messages,
        ) as stream:
            async for text in stream.text_stream:
                self._last_assistant_text += text
                yield text

        self.messages.append(
            {"role": "assistant", "content": self._last_assistant_text}
        )

    def extract_enhanced_prompt(self) -> str | None:
        """Extract the latest enhanced prompt from the last response."""
        if not self._last_assistant_text:
            return None
        matches = re.findall(
            r"<enhanced_prompt>\s*(.*?)\s*</enhanced_prompt>",
            self._last_assistant_text,
            re.DOTALL,
        )
        return matches[-1] if matches else None
