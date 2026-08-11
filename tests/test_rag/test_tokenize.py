"""The index and the query path must tokenize identically, or retrieval rots silently."""

import pytest

from agent.rag.tokenize import content_terms, fold, stem, tokens


@pytest.mark.parametrize("group", [
    ("wireframe", "wireframes"),
    ("embedding", "embeddings"),
    ("guardrail", "guardrails"),
    ("evaluate", "evaluated", "evaluating", "evaluation"),
    ("communicate", "communication"),
    ("prioritize", "prioritisation", "prioritization"),
    ("story", "stories"),
    ("matrix", "matrices"),
    ("analysis", "analyses"),
    ("design", "designs", "designing", "designed"),
])
def test_inflections_collapse_to_one_token(group):
    assert len({stem(word) for word in group}) == 1


@pytest.mark.parametrize("word", ["business", "less", "ai", "ux", "rag", "prd", "uat", "gpa"])
def test_short_and_acronym_tokens_are_left_alone(word):
    assert stem(word) == word


def test_vietnamese_diacritics_fold():
    assert fold("kinh nghiệm") == "kinh nghiem"
    assert fold("Đà Nẵng") == "Da Nang"


def test_vietnamese_query_matches_unaccented_spelling():
    assert tokens("kinh nghiệm") == tokens("kinh nghiem")


def test_stopwords_are_dropped_but_acronyms_survive():
    assert content_terms("What is the AI and UX of it?") == ["ai", "ux"]


def test_content_terms_deduplicate_preserving_order():
    assert content_terms("agent agent guardrail agent") == ["agent", "guardrail"]
