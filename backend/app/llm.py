"""Thin LLM adapter. Swap this one function to change provider."""
from typing import TypeVar

from pydantic import BaseModel

from .config import settings

T = TypeVar("T", bound=BaseModel)


def extract_structured(model_cls: type[T], system: str, user: str) -> T:
    import anthropic  # lazy import keeps unit tests light

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[{
            "name": "record",
            "description": "Record the structured extraction result.",
            "input_schema": model_cls.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "record"},
    )
    for block in resp.content:
        if block.type == "tool_use":
            return model_cls.model_validate(block.input)
    raise ValueError("LLM returned no structured output")
