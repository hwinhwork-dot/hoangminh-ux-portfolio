"""Tool: search_knowledge — the only way any node reads the knowledge base."""

from __future__ import annotations

from agent.config import get_settings
from agent.guardrails.tool_guard import assert_allowed
from agent.rag.rerank import apply_floor, rerank
from agent.rag.retrieve import hybrid_search
from agent.schemas import Hit


def search_knowledge(
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
    score_query: str | None = None,
) -> list[Hit]:
    """Hybrid search, reranked, floored.

    Returns `[]` when nothing clears the floor. The caller must treat that as
    "not indexed" — never as permission to answer from model memory.

    `score_query` is the visitor's original wording; the floor is applied against it so
    query expansion cannot talk the retriever into confidence it has not earned.
    """
    assert_allowed("search_knowledge", {"query": query}, 0)
    settings = get_settings()
    candidates = hybrid_search(query, top_k or settings.top_k, score_query=score_query)
    best = rerank(query, candidates, settings.rerank_top_n)
    return apply_floor(best, settings.min_score if min_score is None else min_score)
