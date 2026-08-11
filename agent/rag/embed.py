"""Embeddings, stored so the serverless function never loads a numeric stack.

Vectors are built offline by `scripts/ingest_kb.py` and written as base64-encoded
float32 arrays. At request time the function decodes with `array` and `base64` — both
stdlib — and computes cosine as a plain dot product because the vectors are stored
L2-normalised.

Why not numpy: the corpus is ~60 chunks. A pure-Python dot product over that costs well
under a millisecond, while numpy costs tens of megabytes of bundle and import time on
every cold start. The moment the corpus outgrows this, the answer is a hosted vector
store, not numpy.

Everything here is optional. With no API key the index is built lexical-only and
retrieval still works — see ADR-0003.
"""

from __future__ import annotations

import base64
import math
from array import array
from functools import lru_cache

from agent.config import get_settings

Vector = list[float]


# --------------------------------------------------------------------------- #
# storage
# --------------------------------------------------------------------------- #
def encode(vector: Vector) -> str:
    return base64.b64encode(array("f", vector).tobytes()).decode("ascii")


def decode(blob: str) -> Vector:
    buf = array("f")
    buf.frombytes(base64.b64decode(blob))
    return list(buf)


def normalise(vector: Vector) -> Vector:
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


def cosine(a: Vector, b: Vector) -> float:
    """Dot product. Correct only because both sides are stored normalised."""
    return sum(x * y for x, y in zip(a, b, strict=False))


# --------------------------------------------------------------------------- #
# provider
# --------------------------------------------------------------------------- #
def available() -> bool:
    settings = get_settings()
    return settings.embedding_provider == "openai" and bool(settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[Vector]:
    """Batch-embed and return normalised vectors. Raises if no provider is configured."""
    if not available():
        raise RuntimeError("no embedding provider configured — set OPENAI_API_KEY")

    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    out: list[Vector] = []
    for start in range(0, len(texts), 96):
        batch = texts[start : start + 96]
        response = client.embeddings.create(model=settings.embedding_model, input=batch)
        out.extend(normalise(list(item.embedding)) for item in response.data)
    return out


@lru_cache(maxsize=256)
def _embed_query_cached(text: str) -> tuple[float, ...] | None:
    try:
        return tuple(embed_texts([text])[0])
    except Exception:
        # A provider hiccup must degrade retrieval, never fail the request.
        return None


def embed_query(text: str) -> Vector | None:
    """None when embeddings are unavailable — the caller falls back to lexical only.

    Cached: the studio's sticky-note chips send identical queries, visitors rephrase, and
    every eval rerun repeats all 42. A cache hit removes a network round trip from the
    critical path, which is the single biggest lever on p95 latency.
    """
    if not available():
        return None
    vector = _embed_query_cached(text)
    return list(vector) if vector else None
