"""The one serverless function.

Vercel routes every `/api/*` path here (see `vercel.json` rewrites) and bundles the
`agent/` and `knowledge/` trees alongside it via `includeFiles`. Sibling imports need the
project root on `sys.path` because the function's working directory is the bundle root,
not this file's directory.

Local: `vercel dev`, or `uvicorn api.index:app --reload --port 8000`.
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from agent.config import get_settings  # noqa: E402
from agent.guardrails.policies import get_policies  # noqa: E402
from agent.observability import cost, trace  # noqa: E402
from agent.orchestrator import graph  # noqa: E402
from agent.schemas import ChatRequest, ChatResponse  # noqa: E402

settings = get_settings()

app = FastAPI(
    title="hwinh's Product Studio API",
    version="1.0.0",
    docs_url=None,  # no public schema browser on a personal endpoint
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["content-type"],
    max_age=600,
)


# --------------------------------------------------------------------------- #
# rate limiting
# --------------------------------------------------------------------------- #
# In-memory and therefore **per warm instance**. On Vercel several lambdas may serve the
# same visitor, so the effective limit is this number times the instance count. That is
# a deliberate, documented compromise: it costs nothing, it stops the obvious abuse case
# (one person hammering the endpoint from one connection), and the daily token budget in
# `agent/observability/cost.py` is the real ceiling on spend.
#
# The upgrade, when traffic justifies it, is a shared store — Upstash Redis or Vercel KV
# — behind this same interface. Nothing above this line changes.
_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(client_ip: str) -> bool:
    now = time.time()
    window = _hits[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_min:
        return True
    window.append(now)
    if len(_hits) > 5000:  # crude cap so a spoofed-IP flood cannot grow the dict forever
        _hits.clear()
    return False


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #
@app.get("/api/health")
async def health() -> dict:
    """Cheap liveness probe. Reports whether the next turn will be model-backed."""
    from agent.rag.retrieve import load_index

    index = load_index()
    return {
        "ok": True,
        "env": settings.env,
        "llm_enabled": settings.llm_enabled and not cost.budget_exhausted(),
        "model": settings.model if settings.llm_enabled else None,
        "index": {
            "chunks": index.n if index else 0,
            "vectors": bool(index and index.vectors),
        },
        "budget_used": cost.budget_ratio(),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """One studio turn. Contract in ARCHITECTURE.md §6."""
    started = time.perf_counter()
    policies = get_policies()

    if _rate_limited(_client_ip(request)):
        return ChatResponse(
            answer_html=policies.reply("rate_limited"),
            agent="hana",
            intent="smalltalk",  # type: ignore[arg-type]
            trace=[{"actor": "hana", "act": "refuse", "label": "One moment..."}],  # type: ignore[list-item]
            degraded=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    response = await graph.run(payload)

    # Rebuild a minimal state view for the trace line. The orchestrator owns the turn;
    # this endpoint only reports it.
    from agent.orchestrator.state import StudioState

    state = StudioState(message=payload.message, session_id=payload.session_id)
    state.intent = response.intent
    state.speaker = response.agent
    state.degraded = response.degraded
    state.hits = []
    state.top_score = 0.0
    trace.emit(state, response.latency_ms)
    return response


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception) -> JSONResponse:
    """The page must never show a recruiter an error. 200 + degraded beats 500."""
    return JSONResponse(
        status_code=200,
        content={
            "answer_html": (
                "I could not reach my notes just now. Ask me again in a moment, or email "
                "Minh at <b>hwinh.work@gmail.com</b>."
            ),
            "agent": "hana",
            "intent": "smalltalk",
            "citations": [],
            "trace": [{"actor": "hana", "act": "fallback", "label": "Checking my notes..."}],
            "degraded": True,
            "latency_ms": 0,
        },
    )
