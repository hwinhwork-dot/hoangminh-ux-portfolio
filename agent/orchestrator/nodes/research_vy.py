"""Vy — researcher. Deterministic: no model call, therefore fully unit-testable.

Returning zero hits is a legitimate outcome and the reason the answering node cannot
invent a fact: with no evidence, it is never invoked at all.
"""

from __future__ import annotations

from agent.orchestrator.state import StudioState
from agent.schemas import Intent

_NO_RETRIEVAL = {Intent.SMALLTALK, Intent.CONTACT, Intent.OUT_OF_SCOPE, Intent.ADVERSARIAL}


async def research(state: StudioState) -> StudioState:
    if state.intent in _NO_RETRIEVAL:
        return state

    # Đường truy xuất nằm trong agent/orchestrator/retrieval.py để script hiệu chỉnh
    # ngưỡng đo đúng thứ chạy ở đây, chứ không đo một phiên bản gần giống.
    from agent.orchestrator.retrieval import retrieve_for

    state.hits = retrieve_for(state.message)
    state.top_score = state.hits[0].score if state.hits else 0.0
    state.step(
        actor="vy",
        act="retrieve",
        label="On it. Checking the research wall...",
        hits=len(state.hits),
    )
    return state
