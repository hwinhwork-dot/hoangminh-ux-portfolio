"""Derived health signals and their alert thresholds (ARCHITECTURE.md §8).

Computed from the trace lines rather than stored: `vercel logs | python -m
agent.observability.metrics` is the whole monitoring stack, and for one endpoint that is
the right amount of infrastructure.

The thresholds encode which failures are worth waking up for. Fallback rate is first
because it is the one that is invisible to the visitor — they get a polite non-answer and
leave, and nothing about that looks like an incident.
"""

from __future__ import annotations

import json
import sys

# p95 is derived, not chosen: the stage choreography runs ~12s of walking and speech
# bubbles before the answer is needed, and StudioClient gives up at 12s. 9s leaves a
# margin to notice drift before a visitor ever sees a wait. Measured on the v6 live eval:
# p50 4.1s, p95 8.0s.
THRESHOLDS = {
    "fallback_rate": 0.15,
    "guard_block_rate": 0.10,
    "p95_latency_ms": 9000,
    "budget_used_ratio": 0.80,
}


def summarise(lines: list[dict]) -> dict:
    turns = [line for line in lines if line.get("event") == "turn"]
    if not turns:
        return {"turns": 0}

    latencies = sorted(t.get("latency_ms", 0) for t in turns)
    index = max(0, int(len(latencies) * 0.95) - 1)
    return {
        "turns": len(turns),
        "fallback_rate": round(sum(1 for t in turns if t.get("degraded") or not t.get("hits")) / len(turns), 3),
        "guard_block_rate": round(sum(1 for t in turns if t.get("guard") != "pass") / len(turns), 3),
        "p95_latency_ms": latencies[index],
        "budget_used_ratio": max((t.get("budget_ratio", 0) for t in turns), default=0),
        "cost_usd": round(sum(t.get("cost_usd", 0) for t in turns), 4),
        "unanswered": [line["query"] for line in lines if line.get("event") == "unanswered"],
    }


def breaches(summary: dict) -> list[str]:
    return [
        f"{name}={summary[name]} exceeds {limit}"
        for name, limit in THRESHOLDS.items()
        if name in summary and summary[name] > limit
    ]


def main() -> int:
    lines = []
    for raw in sys.stdin:
        raw = raw.strip()
        if raw.startswith("{"):
            try:
                lines.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    summary = summarise(lines)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    for breach in breaches(summary):
        print(f"ALERT: {breach}", file=sys.stderr)
    return 1 if breaches(summary) else 0


if __name__ == "__main__":
    raise SystemExit(main())
