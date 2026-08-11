"""Per-turn state passed between orchestrator nodes.

One mutable object per request. It is also what the tracer serialises, so anything you
add here shows up in the log line and in the on-stage handoff log.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.schemas import Citation, Hit, Intent, TraceStep, Turn


@dataclass
class StudioState:
    # input
    message: str
    session_id: str
    history: list[Turn] = field(default_factory=list)

    # hana
    intent: Intent | None = None
    query: str = ""
    needs_chart: bool = False
    rule_matched: bool = False
    language_in: str = "en"
    confidence: float = 0.0

    # vy
    hits: list[Hit] = field(default_factory=list)
    top_score: float = 0.0

    # minh / kai
    answer_html: str = ""
    raw_answer: str = ""                      # model output, before the output guard
    evidence_map: dict = field(default_factory=dict)   # "E1" -> Citation, for the guard
    citations: list[Citation] = field(default_factory=list)
    speaker: str = "hana"

    # bookkeeping
    trace: list[TraceStep] = field(default_factory=list)
    degraded: bool = False
    blocked_reason: str | None = None
    in_tokens: int = 0
    out_tokens: int = 0

    def step(self, **kwargs) -> None:
        """Append a trace step. The browser replays these as agent walks."""
        self.trace.append(TraceStep(**kwargs))
