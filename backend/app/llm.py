"""Thin LLM adapter. Providers: any OpenAI-compatible API (default) or Anthropic."""
import json
import re
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .config import settings

T = TypeVar("T", bound=BaseModel)

EXAMPLE = (
    '{"relations":[{"source":"ASML","source_type":"Company","relation":"SUPPLIES",'
    '"target":"Intel","target_type":"Company","evidence":"ASML ships EUV tools to Intel",'
    '"confidence":0.9}]}'
)

RETRY_CODES = {429, 500, 502, 503, 504}
WAITS = [5, 15, 30]  # seconds between retries when the provider is overloaded


def strip_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _chat_with_retry(client, models: list[str], sys_prompt: str, prompt: str) -> str:
    last = None
    for model in models:
        for attempt in range(len(WAITS) + 1):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": sys_prompt},
                              {"role": "user", "content": prompt}],
                )
                return resp.choices[0].message.content or ""
            except Exception as exc:
                code = getattr(exc, "status_code", None)
                transient = code in RETRY_CODES or type(exc).__name__ in (
                    "APITimeoutError", "APIConnectionError")
                if not transient:
                    raise
                last = exc
                print(f"[llm] {model} transient error ({code or type(exc).__name__}), attempt {attempt + 1}")
                if attempt < len(WAITS):
                    time.sleep(WAITS[attempt])
    raise last

def _openai_compat(model_cls: type[T], system: str, user: str) -> T:
    from openai import OpenAI

    client = OpenAI(api_key=settings.llm_api_key or "none",
                    base_url=settings.llm_base_url, max_retries=0, timeout=120)
    sys_prompt = (
        f"{system}\n\nReturn ONLY one JSON object (no prose, no markdown) matching this JSON Schema:\n"
        f"{json.dumps(model_cls.model_json_schema())}\n\nExample of valid output:\n{EXAMPLE}"
    )
    models = [settings.llm_model]
    if settings.llm_fallback_model:
        models.append(settings.llm_fallback_model)

    prompt, last_err = user, None
    for _ in range(2):  # one retry with the validation error fed back
        raw = _chat_with_retry(client, models, sys_prompt, prompt)
        try:
            return model_cls.model_validate_json(strip_fences(raw))
        except ValidationError as e:
            last_err = e
            prompt = f"{user}\n\nYour previous output was invalid ({e.error_count()} errors). Return valid JSON only."
    raise ValueError(f"LLM output failed validation: {last_err}")


def _anthropic(model_cls: type[T], system: str, user: str) -> T:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[{"name": "record", "description": "Record the structured extraction result.",
                "input_schema": model_cls.model_json_schema()}],
        tool_choice={"type": "tool", "name": "record"},
    )
    for block in resp.content:
        if block.type == "tool_use":
            return model_cls.model_validate(block.input)
    raise ValueError("LLM returned no structured output")


def extract_structured(model_cls: type[T], system: str, user: str) -> T:
    if settings.llm_provider == "anthropic":
        return _anthropic(model_cls, system, user)
    return _openai_compat(model_cls, system, user)