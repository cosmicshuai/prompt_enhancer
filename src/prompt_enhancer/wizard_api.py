"""Non-streaming Claude API helper for the template creation wizard."""

from __future__ import annotations

import re

import anthropic

from prompt_enhancer.models import AppConfig

TEMPLATE_FIELDS = [
    ("system_prompt", "System Prompt"),
    ("domain_knowledge", "Domain Knowledge"),
    ("thinking_steps", "Thinking Steps"),
    ("clarifying_instructions", "Clarifying Instructions"),
]

FIELD_DESCRIPTIONS = {
    "system_prompt": (
        "The core instruction that defines the AI's role and behavior. "
        "This sets the overall persona, expertise, and approach the AI should take "
        "when enhancing prompts using this template."
    ),
    "domain_knowledge": (
        "Background knowledge and context specific to the domain. "
        "This includes terminology, best practices, common patterns, and reference "
        "information the AI should be aware of when working in this area."
    ),
    "thinking_steps": (
        "A structured sequence of steps the AI should follow when analyzing "
        "and enhancing a prompt. This guides the AI's reasoning process to ensure "
        "thorough and consistent results."
    ),
    "clarifying_instructions": (
        "Guidelines for what clarifying questions the AI should ask the user. "
        "This helps the AI gather the right information before producing the "
        "enhanced prompt, such as audience, constraints, and goals."
    ),
}


def _build_system_prompt() -> str:
    return (
        "You are helping a user create a template for a prompt enhancement tool. "
        "The user will tell you the template name and which field they are filling in. "
        "Generate exactly 2-3 high-quality suggestions for that field.\n\n"
        "Wrap each suggestion in <suggestion> XML tags like this:\n"
        "<suggestion>\nYour suggestion text here\n</suggestion>\n\n"
        "Each suggestion should be substantive (several sentences) and distinct "
        "from the others. Do not include any other text outside the tags."
    )


def _build_suggestion_prompt(
    template_name: str,
    field_key: str,
    completed_fields: dict[str, str],
    current_value: str | None = None,
) -> str:
    field_label = dict(TEMPLATE_FIELDS).get(field_key, field_key)
    description = FIELD_DESCRIPTIONS.get(field_key, "")

    parts = [f'Template name: "{template_name}"']
    parts.append(f"Field to fill: {field_label}")
    parts.append(f"Field description: {description}")

    if completed_fields:
        parts.append("\nAlready completed fields:")
        label_map = dict(TEMPLATE_FIELDS)
        for k, v in completed_fields.items():
            parts.append(f"  {label_map.get(k, k)}: {v}")

    if current_value:
        parts.append(f"\nThe user's current value for this field is:\n{current_value}")
        parts.append(
            "Generate 2-3 refined/improved variations based on this value. "
            "Keep the core intent but enhance clarity, detail, and effectiveness."
        )
    else:
        parts.append(
            "\nGenerate 2-3 suggestions for this field from scratch."
        )

    return "\n".join(parts)


def parse_suggestions(response_text: str) -> list[str]:
    """Extract suggestion text from <suggestion> XML tags."""
    matches = re.findall(
        r"<suggestion>\s*(.*?)\s*</suggestion>",
        response_text,
        re.DOTALL,
    )
    return matches


async def generate_suggestions(
    config: AppConfig,
    template_name: str,
    field_key: str,
    completed_fields: dict[str, str],
    current_value: str | None = None,
) -> list[str]:
    """Call Claude (non-streaming) to generate field suggestions."""
    client = anthropic.AsyncAnthropic(api_key=config.api_key or None)
    user_message = _build_suggestion_prompt(
        template_name, field_key, completed_fields, current_value
    )
    text = ""
    async with client.messages.stream(
        model=config.model,
        max_tokens=config.max_tokens,
        system=_build_system_prompt(),
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for chunk in stream.text_stream:
            text += chunk
    return parse_suggestions(text)
