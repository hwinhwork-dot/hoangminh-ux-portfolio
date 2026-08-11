"""Token accounting and the daily budget ceiling.

On exhaustion the API does not error — it flips to `degraded` and answers from the
extractive path for the rest of the day (`policies.yaml: transport.on_budget_exhausted`).

The counter is per-instance and therefore approximate in a serverless deployment: several
lambdas each hold their own tally, so the real ceiling is roughly the configured budget
times the number of warm instances. That is acceptable for a personal endpoint and
deliberately not hidden — the fix, when it is needed, is the same shared store the rate
limiter wants (see `api/index.py`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from agent.config import get_settings

# USD per 1M tokens. Update alongside LLM_MODEL; a stale table under-reports, it does
# not break anything.
PRICES: dict[str, tuple[float, float]] = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4.1": (2.00, 8.00),
    "text-embedding-3-small": (0.02, 0.0),
}

_spent: dict[str, int] = {}


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    prompt_price, completion_price = PRICES.get(model, (0.5, 1.5))
    return round((in_tokens * prompt_price + out_tokens * completion_price) / 1_000_000, 6)


def record(in_tokens: int, out_tokens: int) -> None:
    day = _today()
    _spent[day] = _spent.get(day, 0) + in_tokens + out_tokens
    for key in list(_spent):
        if key != day:
            del _spent[key]


def used_today() -> int:
    return _spent.get(_today(), 0)


def budget_exhausted() -> bool:
    return used_today() >= get_settings().daily_token_budget


def budget_ratio() -> float:
    budget = get_settings().daily_token_budget or 1
    return round(used_today() / budget, 4)
