"""Reranking and the retrieval floor (Day-8 pipeline).

Cross-signal rather than a cross-encoder: for a 40 KB corpus a second neural pass buys
nothing and costs a model download at cold start. Three cheap signals carry the weight:

* **heading match** — a question that names the section it wants ("PRD", "UAT",
  "VinFast") should get that section, not a passing mention elsewhere;
* **source tier** — tier 1 is fact, tier 3 is pre-approved wording; when both answer, the
  fact wins;
* **source diversity** — four chunks from one file is not evidence, it is one source
  quoted four times, so the second chunk from a file is damped.

`apply_floor` is the single most important function in the retrieval layer: below
`min_score` the answering node is never invoked at all, which is what turns "I don't
know" from a prompt instruction into a structural guarantee.
"""

from __future__ import annotations

from agent.rag.tokenize import content_terms, tokens
from agent.schemas import Hit

TIER_BONUS = {1: 0.12, 2: 0.06, 3: 0.03, 4: 0.0}
HEADING_BONUS = 0.30
REPEAT_PENALTY = 0.06


def rerank(query: str, hits: list[Hit], top_n: int = 4) -> list[Hit]:
    if not hits:
        return []

    terms = set(content_terms(query))
    scored: list[tuple[float, Hit]] = []
    for hit in hits:
        heading_terms = set(tokens(hit.heading))
        # Share of the *heading* the visitor asked about, not share of the query. A long
        # expanded query would dilute the latter to nothing, which is how a section
        # titled "The portfolio itself, as evidence" came to outrank the one titled "UAT"
        # on the question "how does he run UAT?".
        overlap = len(terms & heading_terms) / len(heading_terms) if heading_terms else 0.0
        boost = overlap * HEADING_BONUS + TIER_BONUS.get(hit.tier, 0.0)
        scored.append((hit.score + boost, hit))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    out: list[Hit] = []
    seen: dict[str, int] = {}
    for boosted, hit in scored:
        repeats = seen.get(hit.source_file, 0)
        if boosted - repeats * REPEAT_PENALTY <= 0:
            continue
        seen[hit.source_file] = repeats + 1
        out.append(hit)
        if len(out) >= top_n:
            break
    return out


def apply_floor(hits: list[Hit], min_score: float) -> list[Hit]:
    """Drop everything below the floor.

    Returning `[]` is a correct, expected outcome. The orchestrator reads an empty list
    as "not indexed" and answers honestly instead of asking the model to improvise.
    """
    return [hit for hit in hits if hit.score >= min_score]
