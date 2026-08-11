"""Wire contracts shared by the API, the orchestrator and the browser.

These models are the single definition of the `/api/chat` contract documented in
ARCHITECTURE.md §6. The frontend (`assets/js/studio-client.js`) mirrors them by hand —
if you change a field here, change it there in the same commit.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    PROFILE = "profile"
    ARTIFACT = "artifact"
    PROJECT = "project"
    AI_PRODUCT = "ai_product"
    COMPARISON = "comparison"
    METRIC = "metric"
    LOGISTICS = "logistics"
    CONTACT = "contact"
    SMALLTALK = "smalltalk"
    OUT_OF_SCOPE = "out_of_scope"
    ADVERSARIAL = "adversarial"


#: Intents whose answers must carry at least one citation (enforced by the output guard).
FACTUAL_INTENTS = {
    Intent.PROFILE,
    Intent.ARTIFACT,
    Intent.PROJECT,
    Intent.AI_PRODUCT,
    Intent.COMPARISON,
    Intent.METRIC,
}

Agent = Literal["hana", "vy", "minh", "kai"]


# --------------------------------------------------------------------------- #
# request
# --------------------------------------------------------------------------- #
class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=300)
    session_id: str = Field(max_length=64, description="Client-generated UUID. Never a cookie, never PII.")
    history: list[Turn] = Field(default_factory=list, max_length=6)


# --------------------------------------------------------------------------- #
# retrieval
# --------------------------------------------------------------------------- #
class Chunk(BaseModel):
    """One retrievable unit of the knowledge base."""

    id: str
    text: str
    source_file: str
    heading: str
    tier: int = Field(ge=1, le=4)
    updated_at: str


class Hit(Chunk):
    score: float
    lexical_score: float = 0.0
    dense_score: float = 0.0


class Citation(BaseModel):
    source: str
    heading: str


# --------------------------------------------------------------------------- #
# trace — drives the on-stage choreography in index.html
# --------------------------------------------------------------------------- #
class TraceStep(BaseModel):
    actor: Agent
    act: Literal["triage", "retrieve", "answer", "chart", "refuse", "fallback"]
    label: str = Field(description="Speech-bubble text shown above the walking agent.")
    hits: int | None = None
    ms: int | None = None


# --------------------------------------------------------------------------- #
# response
# --------------------------------------------------------------------------- #
class ChatResponse(BaseModel):
    answer_html: str
    agent: Agent
    intent: Intent
    citations: list[Citation] = Field(default_factory=list)
    trace: list[TraceStep] = Field(default_factory=list)
    degraded: bool = False
    latency_ms: int = 0


class ErrorBody(BaseModel):
    code: Literal["rate_limited", "blocked", "upstream", "bad_request"]
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
