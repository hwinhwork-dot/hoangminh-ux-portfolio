"""One structured JSON line per request (Day-10 pipeline).

Vercel captures stdout, so stdout is the sink. There is no metrics database and no
tracing vendor: for a single public endpoint, one greppable line per turn carries every
signal the four health checks in ARCHITECTURE.md §8 need.

Privacy rule: the visitor's question is logged **only** when retrieval missed. Those
queries are the knowledge-gap backlog and are worth their weight; every other message is
someone reading a portfolio, and there is no reason to keep it.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

from agent.config import get_settings
from agent.observability import cost
from agent.orchestrator.state import StudioState


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), file=sys.stdout, flush=True)


def emit(state: StudioState, latency_ms: int) -> None:
    settings = get_settings()
    spend = cost.estimate_cost(settings.model, state.in_tokens, state.out_tokens)
    cost.record(state.in_tokens, state.out_tokens)
    _emit({
        "event": "turn",
        "ts": datetime.now(UTC).isoformat(),
        "session": state.session_id,
        "intent": state.intent.value if state.intent else None,
        "agent": state.speaker,
        "hits": len(state.hits),
        "top_score": round(state.top_score, 3),
        "model": settings.model if state.in_tokens else None,
        "in_tok": state.in_tokens,
        "out_tok": state.out_tokens,
        "cost_usd": spend,
        "budget_ratio": cost.budget_ratio(),
        "latency_ms": latency_ms,
        "guard": state.blocked_reason or "pass",
        "degraded": state.degraded,
    })


def log_unanswered(query: str, top_score: float) -> None:
    """A retrieval miss is a knowledge gap. This log is the backlog for the next revision."""
    _emit({
        "event": "unanswered",
        "ts": datetime.now(UTC).isoformat(),
        "query": query[:200],
        "top_score": round(top_score, 3),
    })
