"""Build `knowledge/index` from `knowledge/raw`, refusing to publish a broken index.

The Day-10 lesson applied to a knowledge base: a pipeline that silently writes bad data
is worse than one that fails loudly, because the agent will answer confidently from it
and nobody finds out until a recruiter does.

So the gates run *before* the write, and a failing gate aborts the build. The previous
index stays in place — a stale answer beats a broken one.

One rule worth calling out: `06-boundaries.md` is deliberately **not** indexed. It is the
refusal playbook, and an agent that can retrieve its own guardrail policy can be talked
into reciting it. Policy is loaded by the guard, never by the retriever.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent.rag import embed
from agent.rag.chunk import MIN_TOKENS, chunk_corpus, estimate_tokens
from agent.rag.tokenize import tokens
from agent.schemas import Chunk

REQUIRED_FRONT_MATTER = ("source_id", "tier", "updated_at")
SHRINK_TOLERANCE = 0.30


class IngestError(RuntimeError):
    """A data-quality gate failed. Nothing was written."""


def _allowed_sources() -> set[str]:
    from agent.guardrails.policies import get_policies

    return set(get_policies().raw["retrieval"]["allowed_sources"])


def run_gates(chunks: list[Chunk], raw_dir: Path, out_dir: Path) -> list[str]:
    """Return a list of human-readable failures. Empty list means the build may proceed."""
    failures: list[str] = []
    allowed = _allowed_sources()

    if not chunks:
        return ["corpus is empty — nothing to index"]

    # 1. front matter must be complete, or tier/updated_at silently default and the
    #    authority ladder in rerank.py starts ranking on fiction.
    for path in sorted(raw_dir.glob("*.md")):
        if path.name.startswith(("README", "_")) or path.name not in allowed:
            continue
        head = path.read_text(encoding="utf-8")[:400]
        for key in REQUIRED_FRONT_MATTER:
            if f"{key}:" not in head:
                failures.append(f"{path.name}: front matter missing '{key}'")

    # 2. every indexed source must be citable, or the output guard will reject answers
    #    that were grounded correctly.
    for source in {c.source_file for c in chunks}:
        if source not in allowed:
            failures.append(f"{source}: indexed but not in policies.yaml allowed_sources")

    # 3. no empty or stub chunks
    for chunk in chunks:
        if estimate_tokens(chunk.text) < MIN_TOKENS:
            failures.append(f"{chunk.id}: below {MIN_TOKENS} tokens")
        if not chunk.heading.strip():
            failures.append(f"{chunk.id}: empty heading")

    # 4. ids must be unique — a duplicate silently shadows a chunk at citation time
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.id in seen:
            failures.append(f"{chunk.id}: duplicate chunk id")
        seen.add(chunk.id)

    # 5-6. compare against the index already on disk, read once.
    previous = out_dir / "index.json"
    if previous.exists():
        try:
            built = json.loads(previous.read_text(encoding="utf-8"))["chunks"]
        except (json.JSONDecodeError, KeyError):
            built = None
        if built is not None:
            # The built index must agree with the source. Nothing warned when they
            # drifted — the mismatch was found by accident — and a stale index answers
            # confidently from text that is no longer true.
            built_ids = {c["id"] for c in built}
            fresh_ids = {c.id for c in chunks}
            if built_ids != fresh_ids:
                added, removed = sorted(fresh_ids - built_ids), sorted(built_ids - fresh_ids)
                failures.append(
                    f"index is stale: {len(added)} new, {len(removed)} removed "
                    f"(e.g. +{added[:2]} -{removed[:2]}). Run `python scripts/ingest_kb.py`"
                )
            # A corpus that suddenly shrank is usually a bad edit, not a real deletion.
            if built and len(chunks) < len(built) * (1 - SHRINK_TOLERANCE):
                failures.append(
                    f"corpus shrank {len(built)} -> {len(chunks)} chunks "
                    f"(>{int(SHRINK_TOLERANCE * 100)}%). Re-run with --force if intended"
                )

    return failures


def build_index(raw_dir: Path, out_dir: Path, *, force: bool = False, with_vectors: bool = True) -> dict:
    chunks = [c for c in chunk_corpus(raw_dir) if c.source_file in _allowed_sources()]

    # The staleness gate must not block the very build that resolves it.
    failures = [f for f in run_gates(chunks, raw_dir, out_dir) if not f.startswith("index is stale")]
    if failures and not force:
        raise IngestError("\n".join(f"  - {f}" for f in failures))

    doc_tokens = [tokens(c.text) for c in chunks]

    vectors: list[str] | None = None
    model: str | None = None
    if with_vectors and embed.available():
        from agent.config import get_settings

        vectors = [embed.encode(v) for v in embed.embed_texts([c.text for c in chunks])]
        model = get_settings().embedding_model

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [c.model_dump() for c in chunks],
        "doc_tokens": doc_tokens,
        "vectors": vectors,
        "embedding_model": model,
    }
    (out_dir / "index.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    from collections import Counter

    return {
        "chunks": len(chunks),
        "sources": dict(sorted(Counter(c.source_file for c in chunks).items())),
        "tokens_total": sum(len(t) for t in doc_tokens),
        "vocabulary": len({t for doc in doc_tokens for t in doc}),
        "vectors": bool(vectors),
        "embedding_model": model,
        "gate_failures": failures,
        "bytes": (out_dir / "index.json").stat().st_size,
    }
