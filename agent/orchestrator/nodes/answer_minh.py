"""Minh — the source of truth. The only generative node in the graph.

Two paths out of here:

* with a model, the prompt composes a grounded answer and appends a CITATIONS line that
  the output guard verifies;
* without one, `extractive_answer` quotes the top-ranked passage directly. That is not a
  lesser fallback so much as a different guarantee — text lifted verbatim from the
  knowledge base cannot be wrong about Minh, only terse.
"""

from __future__ import annotations

import re

from agent.config import PROMPTS_DIR
from agent.orchestrator.state import StudioState
from agent.schemas import Citation
from agent.services import llm


def _prompt() -> str:
    shared = (PROMPTS_DIR / "00-shared-context.md").read_text(encoding="utf-8")
    answer = (PROMPTS_DIR / "20-minh-answer.md").read_text(encoding="utf-8")
    return f"{shared}\n\n---\n\n{answer}"


def build_evidence(state: StudioState) -> tuple[str, dict[str, Citation]]:
    """Render the evidence block and the E-key -> citation map the guard will need."""
    lines: list[str] = []
    mapping: dict[str, Citation] = {}
    for i, hit in enumerate(state.hits, start=1):
        key = f"E{i}"
        mapping[key] = Citation(source=hit.source_file, heading=hit.heading)
        lines.append(f'[{key} · {hit.source_file} · "{hit.heading}"]\n{hit.text}')
    return "\n\n".join(lines), mapping


def markdown_to_html(text: str) -> str:
    """The knowledge base is markdown; the studio renders a narrow HTML subset.

    Without this the extractive path shows literal asterisks to a recruiter — which is
    exactly the kind of small ugliness that reads as an unfinished product.
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^[-*]\s+", "", text, flags=re.M)
    return re.sub(r"\s*\n\s*", " ", text).strip()


def _focused_excerpt(body: str, query: str, limit: int = 3) -> str:
    """Pick the sentences that answer the question, not the ones that came first.

    A section opens with context and answers later. Leading with sentence one gives a
    recruiter a name and a location when they asked about a current role.
    """
    from agent.rag.tokenize import content_terms, tokens

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if len(sentences) <= limit:
        return " ".join(sentences)

    wanted = set(content_terms(query))
    scores = [len(wanted & set(tokens(s))) for s in sentences]
    best = max(range(len(sentences)), key=lambda i: scores[i]) if any(scores) else 0
    start = max(0, min(best, len(sentences) - limit))
    return " ".join(sentences[start : start + limit])


def extractive_answer(state: StudioState) -> tuple[str, list[Citation]]:
    """Quote the best passage verbatim. Used whenever no model is available.

    Verbatim is the whole point: text lifted from the knowledge base cannot be wrong
    about Minh, only terse.
    """
    hit = state.hits[0]
    body = markdown_to_html(hit.text.split("\n\n", 1)[-1].strip())
    excerpt = _focused_excerpt(body, state.message)
    if len(excerpt) > 480:
        excerpt = excerpt[:480].rsplit(" ", 1)[0] + "…"
    return (
        f"<b>{hit.heading}</b><br>{excerpt}"
        '<span class="cap">Quoted from Minh\'s notes. Ask a narrower question for more.</span>',
        [Citation(source=hit.source_file, heading=hit.heading)],
    )


async def answer(state: StudioState) -> StudioState:
    if not state.hits:
        return state

    if not llm.enabled():
        state.answer_html, state.citations = extractive_answer(state)
        state.speaker = "minh"
        state.degraded = True
        state.step(actor="minh", act="answer", label="Here is the full context.")
        return state

    evidence, mapping = build_evidence(state)
    user = (
        f"<question>{state.message}</question>\n"
        f"<intent>{state.intent.value if state.intent else 'profile'}</intent>\n"
        f"<evidence>\n{evidence}\n</evidence>"
    )
    result = llm.complete(_prompt(), user)
    if result is None:
        state.answer_html, state.citations = extractive_answer(state)
        state.degraded = True
    else:
        state.raw_answer = result.text
        state.evidence_map = mapping
        state.in_tokens += result.in_tokens
        state.out_tokens += result.out_tokens

    state.speaker = "minh"
    state.step(actor="minh", act="answer", label="Here is the full context.")
    return state
