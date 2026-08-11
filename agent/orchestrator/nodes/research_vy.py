"""Vy — researcher. Deterministic: no model call, therefore fully unit-testable.

Returning zero hits is a legitimate outcome and the reason the answering node cannot
invent a fact: with no evidence, it is never invoked at all.
"""

from __future__ import annotations

from agent.orchestrator.state import StudioState
from agent.schemas import Intent
from agent.tools.search_knowledge import search_knowledge

_NO_RETRIEVAL = {Intent.SMALLTALK, Intent.CONTACT, Intent.OUT_OF_SCOPE, Intent.ADVERSARIAL}


async def research(state: StudioState) -> StudioState:
    if state.intent in _NO_RETRIEVAL:
        return state

    # Expanded query finds the passage; the visitor's own words decide whether we are
    # confident enough to answer at all.
    state.hits = search_knowledge(state.query or state.message, score_query=state.message)
    state.top_score = state.hits[0].score if state.hits else 0.0
    state.step(
        actor="vy",
        act="retrieve",
        label="On it. Checking the research wall...",
        hits=len(state.hits),
    )
    return state
