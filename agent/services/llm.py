"""The single place this codebase talks to a model provider.

One module, two calls, and a hard rule: **it never raises**. Every failure — no key, a
timeout, a rate limit, a malformed response — returns `None`, and the caller degrades.
An exception escaping this boundary would surface to a recruiter as a broken page, which
ADR-0003 forbids.

Token usage is recorded on the result so the trace can price the turn without the
orchestrator having to know anything about the provider.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from agent.config import get_settings


@dataclass
class Completion:
    text: str
    in_tokens: int = 0
    out_tokens: int = 0
    model: str = ""


def enabled() -> bool:
    return get_settings().llm_enabled


def _client():
    from openai import OpenAI

    return OpenAI(api_key=get_settings().openai_api_key, timeout=20.0, max_retries=1)


def complete(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    json_mode: bool = False,
) -> Completion | None:
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    try:
        kwargs = {
            "model": model or settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens or settings.max_tokens,
            "temperature": settings.temperature if temperature is None else temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = _client().chat.completions.create(**kwargs)
        usage = getattr(response, "usage", None)
        return Completion(
            text=(response.choices[0].message.content or "").strip(),
            in_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            out_tokens=getattr(usage, "completion_tokens", 0) or 0,
            model=kwargs["model"],
        )
    except Exception:
        # Deliberately broad: provider SDKs raise a wide and changing set of errors, and
        # every one of them means the same thing here — answer without the model.
        return None


def complete_json(system: str, user: str, *, model: str | None = None) -> dict | None:
    """Structured call for the triage node. Returns None on any parse or call failure."""
    result = complete(system, user, model=model, max_tokens=200, temperature=0.0, json_mode=True)
    if result is None:
        return None
    try:
        parsed = json.loads(result.text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
