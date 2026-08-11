"""Hana — facilitator. Classifies the question and owns every refusal.

Rules first, model second. The model is only asked when `router.route()` declines, which
in practice is the long tail of oddly-phrased questions. Everything Hana answers herself
— logistics, contact, greetings — comes from pre-approved wording, so those turns cost
nothing and cannot drift.
"""

from __future__ import annotations

from agent.config import PROMPTS_DIR, get_settings
from agent.guardrails.policies import get_policies
from agent.orchestrator.router import expand_query, route
from agent.orchestrator.state import StudioState
from agent.schemas import Intent
from agent.services import llm

_VALID = {i.value for i in Intent}


def _prompt() -> str:
    shared = (PROMPTS_DIR / "00-shared-context.md").read_text(encoding="utf-8")
    triage = (PROMPTS_DIR / "10-hana-triage.md").read_text(encoding="utf-8")
    return f"{shared}\n\n---\n\n{triage}"


async def triage(state: StudioState) -> StudioState:
    ruled = route(state.message)
    if ruled:
        state.intent, state.query, state.needs_chart = ruled
        state.confidence = 0.9
        state.step(actor="hana", act="triage", label="Got it. Classifying the question...")
        return state

    result = llm.complete_json(_prompt(), state.message, model=get_settings().triage_model)
    if result and result.get("intent") in _VALID:
        state.intent = Intent(result["intent"])
        state.query = str(result.get("query") or state.message)
        state.needs_chart = bool(result.get("needs_chart"))
        state.language_in = str(result.get("language_in") or "en")
        state.confidence = float(result.get("confidence") or 0.5)
    else:
        # No rule, no model. Search with the raw question and let the floor decide —
        # guessing an intent is worse than admitting the question was unusual.
        state.intent = Intent.PROFILE
        state.query = expand_query(state.message)
        state.confidence = 0.3
        state.degraded = state.degraded or not llm.enabled()

    state.step(actor="hana", act="triage", label="Got it. Classifying the question...")
    return state


def canned_answer(state: StudioState) -> str | None:
    """Turns Hana answers alone, from approved wording. No retrieval, no model."""
    policies = get_policies()
    if state.intent == Intent.SMALLTALK:
        return (
            "Hi — I answer questions about <b>Minh</b>'s work. Try his "
            "<b>AI product work</b>, the <b>VinFast assistant</b>, how he writes a "
            "<b>PRD</b>, or how to <b>reach him</b>."
        )
    if state.intent == Intent.CONTACT:
        return (
            "Reach Minh at <b>hwinh.work@gmail.com</b> or <b>+84 765 828 191</b> "
            "(Ho Chi Minh City). He is open to UX research, CX, product discovery and "
            "AI product roles."
        )
    if state.intent == Intent.LOGISTICS:
        return policies.reply("not_indexed") if not state.hits else None
    return None
