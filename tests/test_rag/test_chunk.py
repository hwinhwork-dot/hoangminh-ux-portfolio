"""Chunking decides what a citation can point at."""

from pathlib import Path

from agent.config import KNOWLEDGE_RAW
from agent.rag.chunk import (
    MIN_TOKENS,
    chunk_corpus,
    chunk_file,
    estimate_tokens,
    parse_front_matter,
    split_oversized,
)

CORPUS = chunk_corpus(KNOWLEDGE_RAW)


def test_corpus_produces_chunks():
    assert len(CORPUS) > 30


def test_every_chunk_has_complete_provenance():
    for chunk in CORPUS:
        assert chunk.source_file.endswith(".md")
        assert chunk.heading.strip()
        assert 1 <= chunk.tier <= 4
        assert chunk.updated_at


def test_chunk_ids_are_unique():
    ids = [c.id for c in CORPUS]
    assert len(ids) == len(set(ids))


def test_no_chunk_is_a_stub():
    assert all(estimate_tokens(c.text) >= MIN_TOKENS for c in CORPUS)


def test_chunks_carry_their_heading_in_the_text():
    # Both the retriever and the answering model need to see what a passage is about.
    for chunk in CORPUS:
        assert chunk.text.startswith(chunk.heading)


def test_tables_are_never_split_from_their_header():
    for chunk in CORPUS:
        rows = [line for line in chunk.text.splitlines() if line.strip().startswith("|")]
        if rows:
            assert any("---" in row for row in rows), f"{chunk.id} has orphan table rows"


def test_front_matter_is_parsed():
    meta, body = parse_front_matter("---\nsource_id: x\ntier: 1\n---\n# Title\n")
    assert meta["source_id"] == "x" and meta["tier"] == "1"
    assert body.strip() == "# Title"


def test_oversized_section_splits_with_overlap():
    text = "\n\n".join(f"Paragraph number {i} with some filler words here." * 6 for i in range(40))
    parts = split_oversized("Big", text)
    assert len(parts) > 1
    assert all(estimate_tokens(p) <= 700 for p in parts)


def test_boundaries_file_is_chunkable_but_excluded_from_the_index():
    # It is the refusal playbook. An agent able to retrieve it can be talked into
    # reciting its own guardrails.
    from agent.rag.ingest import _allowed_sources

    assert chunk_file(Path(KNOWLEDGE_RAW) / "06-boundaries.md")
    assert "06-boundaries.md" not in _allowed_sources()
