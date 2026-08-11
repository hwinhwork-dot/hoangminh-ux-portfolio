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

    query = state.query or state.message

    # Expanded query finds the passage; the visitor's own words decide whether we are
    # confident enough to answer at all.
    state.hits = search_knowledge(query, score_query=state.message)

    if not state.hits and state.rule_matched:
        # A question can be on-topic while sharing no vocabulary with the corpus — a
        # Vietnamese recruiter asking "hiện tại Minh đang làm ở đâu?" of an English
        # knowledge base scores zero lexically. Embeddings normally bridge that, but the
        # site is designed to work without them.
        #
        # A hand-written routing rule matching is itself strong evidence the question is
        # on topic: the rules are specific and reviewed, unlike a model's guess. So when
        # one fired and the strict pass still found nothing, fall back to scoring against
        # the rule's own translation. Gated on `rule_matched`, this cannot reopen the
        # hole it replaced — "which companies in Singapore" matches no rule at all.
        state.hits = search_knowledge(query, score_query=query)
    state.top_score = state.hits[0].score if state.hits else 0.0
    state.step(
        actor="vy",
        act="retrieve",
        label="On it. Checking the research wall...",
        hits=len(state.hits),
    )
    return state
