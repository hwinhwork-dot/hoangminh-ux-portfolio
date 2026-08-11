"""The studio graph: hana -> vy -> minh -> (kai) -> output guard.

A small hand-written async pipeline rather than a framework. Four nodes and one
conditional edge do not justify a graph library, and the trace format the browser
animation consumes is easier to keep honest this way.

The invariant that shapes the whole function: **no path raises to the caller.** Every
failure — no key, provider error, guard rejection, empty retrieval — resolves to an
answer plus `degraded`, because a recruiter seeing an error state is the one outcome
worth engineering against (ADR-0003).
"""

from __future__ import annotations

import time

from agent.guardrails.input_guard import check_input
from agent.guardrails.output_guard import check_output
from agent.guardrails.policies import get_policies
from agent.orchestrator.nodes import answer_minh, research_vy, triage_hana, viz_kai
from agent.orchestrator.state import StudioState
from agent.schemas import ChatRequest, ChatResponse, Intent
from agent.services import llm


def _respond(state: StudioState, started: float) -> ChatResponse:
    # Computed here rather than at the end of `run`, because most turns return early —
    # a refusal, a canned answer, an empty retrieval — and each of those was reporting
    # degraded=false even when no model was configured at all.
    degraded = state.degraded or not llm.enabled()
    return ChatResponse(
        answer_html=state.answer_html,
        agent=state.speaker,  # type: ignore[arg-type]
        intent=state.intent or Intent.PROFILE,
        citations=state.citations,
        trace=state.trace,
        degraded=degraded,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


async def run(request: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    policies = get_policies()
    state = StudioState(
        message=request.message,
        session_id=request.session_id,
        history=list(request.history),
    )

    # 1. Input guard — a block costs nothing and never reaches the model.
    guard = check_input(request.message)
    if guard.blocked:
        state.intent = guard.intent or Intent.OUT_OF_SCOPE
        state.blocked_reason = guard.reason
        state.answer_html = policies.reply(guard.reply_key or "out_of_scope")
        state.speaker = "hana"
        state.step(actor="hana", act="refuse", label="Let me point you the right way...")
        return _respond(state, started)

    try:
        # 2. Triage.
        await triage_hana.triage(state)

        # 3. Turns Hana owns outright — approved wording, no retrieval, no model.
        canned = triage_hana.canned_answer(state)
        if canned and state.intent in (Intent.SMALLTALK, Intent.CONTACT):
            state.answer_html = canned
            state.speaker = "hana"
            state.step(actor="hana", act="answer", label="Happy to help.")
            if state.intent == Intent.CONTACT:
                from agent.tools.capture_lead import capture_lead

                await capture_lead(state.session_id, state.message, state.intent.value)
            return _respond(state, started)

        # 4. Retrieval. Empty is a valid, meaningful outcome.
        await research_vy.research(state)
        if not state.hits:
            state.answer_html = policies.reply("not_indexed")
            state.speaker = "hana"
            state.step(actor="hana", act="fallback", label="I have not indexed that one...")
            from agent.observability.trace import log_unanswered

            log_unanswered(state.message, state.top_score)
            return _respond(state, started)

        # 5. Compose, then optionally chart.
        await answer_minh.answer(state)
        await viz_kai.visualise(state)

        # 6. Output guard. Charts skip it: their markup is generated here, not by a
        #    model, and their values come from the knowledge base by construction.
        if state.raw_answer:
            verdict = check_output(
                state.raw_answer, state.intent or Intent.PROFILE, evidence=state.evidence_map
            )
            state.answer_html = verdict.html
            state.citations = verdict.citations
            if not verdict.allowed:
                state.speaker = "hana"
                state.blocked_reason = verdict.violation
                state.trace.append(state.trace[-1].model_copy(update={"act": "fallback"}))

        if not state.answer_html:
            state.answer_html = policies.reply("not_indexed")
            state.speaker = "hana"

        # Logistics stays grounded in the HR FAQ but is voiced by the front desk:
        # "when can he start" should sound like the receptionist, not the product owner.
        if state.intent == Intent.LOGISTICS and state.answer_html:
            state.speaker = "hana"

    except Exception as exc:  # noqa: BLE001 - the boundary that keeps the page alive
        state.degraded = True
        state.blocked_reason = f"error:{type(exc).__name__}"
        if not state.answer_html:
            state.answer_html = policies.reply("not_indexed")
            state.speaker = "hana"

    return _respond(state, started)
