"""Hybrid retrieval: BM25 + dense, fused by reciprocal rank (Day-8 pipeline).

Two scores are computed and they do different jobs. Confusing them is the classic RAG
bug, so they are kept apart deliberately:

* **Fusion rank** decides the *order* of results. Reciprocal rank fusion is used because
  BM25 scores and cosine similarities live on incomparable scales — averaging them is
  meaningless, but averaging their ranks is not.

* **Confidence** decides *whether to answer at all*, and must therefore be absolute.
  A relative score is useless as a floor: the best of ten bad chunks still normalises to
  1.0. So confidence is the idf-weighted share of the question's content terms that the
  chunk actually contains, blended with cosine when embeddings exist. "This passage
  covers 60% of what you asked about" is a statement a threshold can be set against.

BM25 is implemented here rather than imported: it is forty lines, it removes a dependency
from the serverless bundle, and it lets the index and the query path share one tokenizer
(`tokenize.py`) — which is the thing that actually breaks retrieval when it drifts.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from agent.config import KNOWLEDGE_INDEX
from agent.rag import embed
from agent.rag.tokenize import content_terms, fold, tokens
from agent.schemas import Chunk, Hit

K1 = 1.2
B = 0.75
RRF_K = 60

# A query term this corpus has never seen still lowers confidence — it is evidence we
# may not know the topic — but it must not outweigh a term we do know. Left at 1.0, a
# single colourful word ("just the buzzword") carries maximum idf and halves the score
# of a perfectly good question. Swept over the golden set: 0.6 gives the widest
# separation between questions that must be answered and questions that must not.
OOV_WEIGHT = 0.6

# Dense retrieval has no notion of a missing entity. "Which companies has he worked for
# in Singapore?" is topically identical to the work-history passages, so cosine rates it
# highly and — before this damping existed — dense confidence overrode a correct lexical
# verdict of 0.15 and pushed the question over the floor.
#
# Lexical search knows something dense cannot: whether the specific words asked about
# occur anywhere in the corpus at all. So the dense contribution is scaled down by the
# idf-weighted share of query terms the corpus has never seen. Swept over the golden set:
# 0.8 separates the populations by +0.160, and above ~1.2 it starts refusing real
# questions. This is the lexical half of "hybrid" gating the dense half, not merely
# ranking beside it.
DENSE_OOV_PENALTY = 0.8


class Index:
    """The prebuilt index, loaded once per cold start."""

    def __init__(self, payload: dict) -> None:
        self.chunks: list[Chunk] = [Chunk(**c) for c in payload["chunks"]]
        self.doc_tokens: list[list[str]] = payload["doc_tokens"]
        self.doc_len: list[int] = [len(t) for t in self.doc_tokens]
        self.avg_len: float = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0
        self.n: int = len(self.chunks)
        self.vectors: list[list[float]] | None = (
            [embed.decode(v) for v in payload["vectors"]] if payload.get("vectors") else None
        )
        self.embedding_model: str | None = payload.get("embedding_model")

        self.df: dict[str, int] = {}
        self.tf: list[dict[str, int]] = []
        for doc in self.doc_tokens:
            counts: dict[str, int] = {}
            for token in doc:
                counts[token] = counts.get(token, 0) + 1
            self.tf.append(counts)
            for token in counts:
                self.df[token] = self.df.get(token, 0) + 1

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))


@lru_cache(maxsize=1)
def load_index(path: Path | None = None) -> Index | None:
    """None when the index has not been built — callers degrade, they do not crash."""
    target = (path or KNOWLEDGE_INDEX) / "index.json"
    if not target.exists():
        return None
    return Index(json.loads(target.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def bm25_scores(index: Index, query: str) -> list[float]:
    terms = tokens(query)
    scores = [0.0] * index.n
    if not terms or not index.avg_len:
        return scores
    for term in terms:
        if term not in index.df:
            continue
        idf = index.idf(term)
        for i, counts in enumerate(index.tf):
            tf = counts.get(term, 0)
            if not tf:
                continue
            denominator = tf + K1 * (1 - B + B * index.doc_len[i] / index.avg_len)
            scores[i] += idf * (tf * (K1 + 1)) / denominator
    return scores


def coverage_scores(index: Index, query: str) -> list[float]:
    """Absolute lexical confidence: idf-weighted share of query terms present.

    Weighting by idf stops a chunk from scoring well just because it contains the common
    words in the question — "what", "he", "work" are already dropped as stopwords, and
    what survives is weighted by how rare it is in this corpus.
    """
    terms = content_terms(query)
    if not terms:
        return [0.0] * index.n
    weights = {
        term: index.idf(term) * (1.0 if term in index.df else OOV_WEIGHT)
        for term in terms
    }
    total = sum(weights.values()) or 1.0
    scores = []
    for counts in index.tf:
        hit = sum(weight for term, weight in weights.items() if counts.get(term))
        scores.append(hit / total)
    return scores


def is_foreign(query: str) -> bool:
    """True when the question is not written in the corpus's language.

    Detected by diacritics: Vietnamese survives `fold()` differently, English does not.
    Crude, and deliberately so — the only decision it drives is whether the lexical
    signal is entitled to veto the dense one.
    """
    return fold(query) != query


def oov_share(index: Index, query: str) -> float:
    """Idf-weighted share of query terms that occur nowhere in the corpus.

    High share = the visitor asked about something this knowledge base has never
    mentioned, whatever the topic looks like in embedding space.
    """
    terms = content_terms(query)
    if not terms:
        return 0.0
    total = sum(index.idf(t) for t in terms) or 1.0
    return sum(index.idf(t) for t in terms if t not in index.df) / total


def dense_scores(index: Index, query: str) -> list[float] | None:
    if not index.vectors:
        return None
    vector = embed.embed_query(query)
    if vector is None:
        return None
    return [embed.cosine(vector, candidate) for candidate in index.vectors]


def _rank_map(scores: list[float]) -> dict[int, int]:
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return {doc: rank for rank, doc in enumerate(order) if scores[doc] > 0}


def hybrid_search(query: str, top_k: int = 12, score_query: str | None = None) -> list[Hit]:
    """Fuse lexical and dense rankings; attach an absolute confidence to each hit.

    `query` finds passages and may carry expansion vocabulary. `score_query` decides how
    confident we are and defaults to `query` — pass the visitor's original wording. The
    distinction matters: an expanded query contains terms drawn from this very corpus, so
    grading confidence against it measures how well we expanded, not how well we know
    the answer.
    """
    index = load_index()
    if index is None or index.n == 0:
        return []

    scored_on = score_query or query
    lexical = bm25_scores(index, query)
    coverage = coverage_scores(index, scored_on)
    dense = dense_scores(index, query)
    # Every term of a Vietnamese question is "unknown" to an English corpus, which says
    # nothing about whether the answer exists. Cross-language matching is exactly what
    # the embeddings are for, so lexical does not get a veto here.
    dense_damping = (
        1.0 if is_foreign(scored_on)
        else max(0.0, 1.0 - DENSE_OOV_PENALTY * oov_share(index, scored_on))
    )

    fused: dict[int, float] = {}
    for doc, rank in _rank_map(lexical).items():
        fused[doc] = fused.get(doc, 0.0) + 1.0 / (RRF_K + rank)
    if dense is not None:
        for doc, rank in _rank_map(dense).items():
            fused[doc] = fused.get(doc, 0.0) + 1.0 / (RRF_K + rank)

    hits: list[Hit] = []
    for doc, fusion in fused.items():
        cosine_score = dense[doc] if dense is not None else 0.0
        # Rescale first (cosine sits around 0.2 even for unrelated text), then damp by
        # how much of the question this corpus has never heard of.
        dense_confidence = (
            max(0.0, (cosine_score - 0.20) / 0.55) * dense_damping if dense is not None else 0.0
        )
        confidence = max(coverage[doc], min(dense_confidence, 1.0))
        chunk = index.chunks[doc]
        hits.append(
            Hit(
                **chunk.model_dump(),
                score=round(confidence, 4),
                lexical_score=round(coverage[doc], 4),
                dense_score=round(cosine_score, 4),
            )
        )
        hits[-1].__dict__["_fusion"] = fusion

    hits.sort(key=lambda h: h.__dict__.get("_fusion", 0.0), reverse=True)
    return hits[:top_k]


def lexical_search(query: str, top_k: int = 12) -> list[Hit]:
    """Lexical-only path, used by tests and whenever embeddings are unavailable."""
    index = load_index()
    if index is None:
        return []
    coverage = coverage_scores(index, query)
    lexical = bm25_scores(index, query)
    order = sorted(range(index.n), key=lambda i: lexical[i], reverse=True)
    return [
        Hit(
            **index.chunks[i].model_dump(),
            score=round(coverage[i], 4),
            lexical_score=round(coverage[i], 4),
            dense_score=0.0,
        )
        for i in order[:top_k]
        if lexical[i] > 0
    ]
