"""Retrieval quality — the layer that decides whether an answer is possible at all.

These run against the committed index. If it is missing the suite skips rather than
fails: a developer who has not run `scripts/ingest_kb.py` has a setup problem, not a
broken retriever.
"""

import pytest

from agent.config import get_settings
from agent.rag.rerank import apply_floor, rerank
from agent.rag.retrieve import hybrid_search, load_index

pytestmark = pytest.mark.usefixtures("index")

FLOOR = get_settings().min_score


def top(query, n=4):
    return rerank(query, hybrid_search(query, 12), n)


def sources(query, n=4):
    return [h.source_file for h in top(query, n)]


# --- the index itself ------------------------------------------------------
def test_index_loads():
    idx = load_index()
    assert idx is not None and idx.n > 30


def test_index_excludes_the_boundaries_playbook():
    idx = load_index()
    assert all(c.source_file != "06-boundaries.md" for c in idx.chunks)


# --- lexical exactness -----------------------------------------------------
@pytest.mark.parametrize("query,expected", [
    ("EchoMind", "02-projects.md"),
    ("VinFast test drive assistant", "02-projects.md"),
    ("GPA", "01-profile.md"),
    ("requirement traceability matrix", "03-practice-requirements.md"),
    ("UAT release gate", "03-practice-requirements.md"),
])
def test_exact_terms_retrieve_their_source(query, expected):
    assert expected in sources(query)


# --- paraphrase and inflection --------------------------------------------
def test_stemming_lets_singular_find_plural():
    # The knowledge base says "wireframes"; a recruiter types "wireframe".
    assert top("wireframe prototyping")


def test_vietnamese_question_still_retrieves():
    assert top("hiện tại Minh đang làm ở đâu")


# --- the floor -------------------------------------------------------------
@pytest.mark.parametrize("query", [
    "Which companies has he worked for in Singapore?",
    "What was his TOEIC score?",
])
def test_topically_absent_questions_fall_below_the_floor(query):
    assert apply_floor(top(query), FLOOR) == []


@pytest.mark.parametrize("query", [
    "Which level of PRD can Minh write?",
    "Tell me about EchoMind",
    "What is Minh doing right now?",
    "How does he think about AI safety and guardrails?",
    "What is different about designing UX for an AI product?",
])
def test_real_questions_clear_the_floor(query):
    assert apply_floor(top(query), FLOOR), f"{query!r} would be wrongly refused"


def test_floor_returning_empty_is_a_valid_outcome():
    assert apply_floor([], FLOOR) == []


# --- reranking -------------------------------------------------------------
def test_rerank_damps_repeats_from_one_source():
    hits = top("Minh", 4)
    counts = {}
    for hit in hits:
        counts[hit.source_file] = counts.get(hit.source_file, 0) + 1
    assert max(counts.values()) <= 3, "one file is crowding out the rest of the evidence"


def test_rerank_respects_top_n():
    assert len(top("product", 2)) <= 2


def test_every_hit_can_be_cited():
    from agent.guardrails.policies import get_policies

    allowed = set(get_policies().allowed_sources)
    for hit in top("Minh product experience"):
        assert hit.source_file in allowed
