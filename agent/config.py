"""Typed settings, read once at cold start.

Everything is optional on purpose: with no keys configured the API still serves answers
from the offline fallback, which is what keeps the live page working when the budget runs
out or a provider has a bad day (ARCHITECTURE.md §10).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_RAW = ROOT / "knowledge" / "raw"
KNOWLEDGE_INDEX = ROOT / "knowledge" / "index"
PROMPTS_DIR = ROOT / "agent" / "prompts"
POLICIES_PATH = ROOT / "agent" / "guardrails" / "policies.yaml"

# Local development reads `.env`; Vercel injects the same names into the process
# environment directly. `override=False` keeps the platform authoritative — a stale local
# file must never win against what production actually configured.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
except ImportError:  # pragma: no cover - python-dotenv is a declared dependency
    pass


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _csv(name: str, default: str = "") -> list[str]:
    return [p.strip() for p in (os.getenv(name) or default).split(",") if p.strip()]


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("ENV", "development")

    # llm — OpenAI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    triage_model: str = os.getenv("LLM_TRIAGE_MODEL", "gpt-4.1-nano")
    max_tokens: int = _int("LLM_MAX_TOKENS", 500)
    temperature: float = _float("LLM_TEMPERATURE", 0.1)

    # embeddings
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "openai")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # retrieval
    top_k: int = _int("RAG_TOP_K", 12)
    rerank_top_n: int = _int("RAG_RERANK_TOP_N", 4)
    min_score: float = _float("RAG_MIN_SCORE", 0.20)

    # guardrails
    max_input_chars: int = _int("MAX_INPUT_CHARS", 300)
    rate_limit_per_min: int = _int("RATE_LIMIT_PER_MIN", 8)
    rate_limit_per_day: int = _int("RATE_LIMIT_PER_DAY", 60)
    daily_token_budget: int = _int("DAILY_TOKEN_BUDGET", 200_000)

    # observability
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    trace_sink: str = os.getenv("TRACE_SINK", "stdout")
    trace_http_endpoint: str | None = os.getenv("TRACE_HTTP_ENDPOINT") or None

    # misc
    lead_webhook_url: str | None = os.getenv("LEAD_WEBHOOK_URL") or None
    owner_email: str = os.getenv("OWNER_EMAIL", "hwinh.work@gmail.com")
    allowed_origins: list[str] = field(default_factory=lambda: _csv("ALLOWED_ORIGINS", "*"))

    @property
    def llm_enabled(self) -> bool:
        """False -> the orchestrator answers from the offline fallback only."""
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
