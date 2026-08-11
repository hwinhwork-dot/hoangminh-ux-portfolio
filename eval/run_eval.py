"""Run the golden set against the real agent and save a versioned result file.

Same discipline as the hackathon build: every run is written to `eval/runs/vN_<date>.json`
so a prompt or policy change can be compared against the run before it. Git already keeps
the prompt history; what is worth keeping is the *result* of each change.

    python eval/run_eval.py              # full set, real model if a key is configured
    python eval/run_eval.py --offline    # force the no-model path
    python eval/run_eval.py --layer ⑤    # one layer
    python eval/run_eval.py --case A01   # one case
    python eval/run_eval.py --no-save    # do not write a run file

Pass criteria, applied only for the fields a case actually declares:

    expected_keywords        all present in the answer, case-insensitive
    expected_keywords_any    at least one present — for facts with several valid namings
    expected_forbidden       none present  (a single hit fails the case outright)
    expected_sources         at least one listed source appears in the citations
    expected_intent/agent    exact match
    expected_html_contains   all substrings present in answer_html
    expected_tokens_spent 0  the turn must not have reached the model at all

Release gate (docs/TEST-PLAN.md): layers ① and ⑤ must be 100%, overall >= 90%, and no
open blocking defect in docs/UAT.md. Anything less does not deploy.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.schemas import ChatRequest  # noqa: E402
from agent.services import llm  # noqa: E402

GOLDEN_SET = ROOT / "eval" / "golden_set.json"
RUNS_DIR = ROOT / "eval" / "runs"

BLOCKING_LAYERS = ("①", "⑤")
OVERALL_GATE = 0.90

_TAG = re.compile(r"<[^>]+>")


def strip_tags(html: str) -> str:
    text = _TAG.sub(" ", html)
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def normalise(text: str) -> str:
    """Fold the differences a grader must not care about.

    Typographic dashes and quotes, and — the one that kept biting — hyphenation. A model
    writing "human in the loop" where the knowledge base writes "human-in-the-loop" has
    not said anything different. Ranges survive this: "55-65" and "55 65" both reduce to
    the same token sequence as the text they are matched against.

    What this deliberately does NOT do is resolve synonyms. "low-fidelity" is not a
    respelling of "lo-fi", and pretending otherwise would make the grader agreeable
    rather than useful. Those cases belong in `expected_keywords_any`.
    """
    for a, b in (("\u2013", "-"), ("\u2014", "-"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"')):
        text = text.replace(a, b)
    text = text.replace("-", " ")
    return " ".join(text.split()).lower()


class ModelCounter:
    """Counts real model calls so `expected_tokens_spent: 0` can be verified.

    Wrapping the service rather than adding a field to ChatResponse keeps the production
    contract free of test scaffolding — the browser has no business knowing token counts.
    """

    def __init__(self) -> None:
        self.calls = 0
        self._complete = llm.complete
        self._complete_json = llm.complete_json

    def __enter__(self) -> ModelCounter:
        def complete(*args, **kwargs):
            self.calls += 1
            return self._complete(*args, **kwargs)

        def complete_json(*args, **kwargs):
            self.calls += 1
            return self._complete_json(*args, **kwargs)

        llm.complete = complete          # type: ignore[assignment]
        llm.complete_json = complete_json  # type: ignore[assignment]
        return self

    def __exit__(self, *exc) -> None:
        llm.complete = self._complete          # type: ignore[assignment]
        llm.complete_json = self._complete_json  # type: ignore[assignment]


def grade(case: dict, result: dict, model_calls: int, live: bool = True) -> tuple[bool, list[str]]:
    """Return `(passed, reasons)`. A case with no assertions is a failure, not a pass.

    Offline runs assert less, and say so. Without a model the answering node is replaced
    by a verbatim quote from the top-ranked passage: the source is still guaranteed, the
    phrasing is not. Grading offline output against keywords written for a composed
    answer would either fail honest behaviour or force the keywords to be so loose that
    they stop testing anything.
    """
    reasons: list[str] = []
    text = normalise(strip_tags(result["answer_html"]))
    checked = False
    assert_keywords = live or case.get("type") not in {"grounded", "premise_correction"}

    for keyword in case.get("expected_keywords", []):
        if not assert_keywords:
            continue
        checked = True
        if normalise(keyword) not in text:
            reasons.append(f"missing keyword {keyword!r}")

    # Some facts have more than one honest name: "reranking", "a confidence floor" and
    # "confidence thresholds" all demonstrate the same depth. Requiring one exact word
    # tests the phrasing, not the product.
    any_of = case.get("expected_keywords_any", [])
    if any_of and assert_keywords:
        checked = True
        if not any(normalise(k) in text for k in any_of):
            reasons.append(f"none of {any_of} present")

    for forbidden in case.get("expected_forbidden", []):
        checked = True
        if normalise(forbidden) in text:
            reasons.append(f"forbidden content present: {forbidden!r}")

    if "expected_sources" in case:
        checked = True
        cited = {c["source"] for c in result["citations"]}
        if not (set(case["expected_sources"]) & cited):
            reasons.append(f"cited {sorted(cited) or 'nothing'}, wanted one of {case['expected_sources']}")

    if "expected_intent" in case:
        checked = True
        if result["intent"] != case["expected_intent"]:
            reasons.append(f"intent {result['intent']} != {case['expected_intent']}")

    if "expected_agent" in case:
        checked = True
        if result["agent"] != case["expected_agent"]:
            reasons.append(f"agent {result['agent']} != {case['expected_agent']}")

    for fragment in case.get("expected_html_contains", []):
        checked = True
        if fragment not in result["answer_html"]:
            reasons.append(f"html missing {fragment!r}")

    if case.get("expected_tokens_spent") == 0:
        checked = True
        if model_calls:
            reasons.append(f"spent {model_calls} model call(s) on a case that must cost nothing")

    if not checked:
        reasons.append("case declares no assertions")

    return not reasons, reasons


REJECTED_BY_TRANSPORT = {
    "answer_html": "rejected by request validation", "agent": "hana",
    "intent": "out_of_scope", "citations": [], "trace": [], "degraded": True, "latency_ms": 0,
}


async def run_case(case: dict) -> tuple[dict, int]:
    from pydantic import ValidationError

    from agent.orchestrator.graph import run

    with ModelCounter() as counter:
        try:
            request = ChatRequest(message=case["input"], session_id=f"eval-{case['id']}")
        except ValidationError:
            # Production returns 422 here and the browser drops to its offline tier.
            return dict(REJECTED_BY_TRANSPORT), counter.calls
        response = await run(request)
    return response.model_dump(mode="json"), counter.calls


def next_version() -> str:
    existing = sorted(RUNS_DIR.glob("v*_*.json"))
    return f"v{len(existing) + 1}_{datetime.now():%Y-%m-%d_%H%M}"


async def main_async(args) -> int:
    cases = json.loads(GOLDEN_SET.read_text(encoding="utf-8"))
    if args.layer:
        cases = [c for c in cases if c["layer"].startswith(args.layer)]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    if not cases:
        print("no cases matched")
        return 1

    if args.offline:
        import agent.config as config

        config.get_settings.cache_clear()
        import os

        os.environ["OPENAI_API_KEY"] = ""

    live = llm.enabled() and not args.offline
    print(f"{len(cases)} cases · {'live model' if live else 'offline (no model calls)'}\n")

    results = []
    skipped: list[str] = []
    for case in cases:
        if case.get("live_only") and not live:
            skipped.append(case["id"])
            print(f"  skip {case['id']:<4} {case['layer'][:1]} {case['input'][:44]:<46} "
                  f"needs a model in the loop")
            continue
        response, calls = await run_case(case)
        passed, reasons = grade(case, response, calls, live=live)
        results.append({
            "id": case["id"], "layer": case["layer"], "type": case["type"],
            "input": case["input"], "passed": passed, "reasons": reasons,
            "agent": response["agent"], "intent": response["intent"],
            "citations": [c["source"] for c in response["citations"]],
            "degraded": response["degraded"], "latency_ms": response["latency_ms"],
            "model_calls": calls,
            "answer": strip_tags(response["answer_html"])[:300].strip(),
        })
        mark = "ok  " if passed else "FAIL"
        print(f"  {mark} {case['id']:<4} {case['layer'][:1]} {case['input'][:44]:<46} "
              f"{'' if passed else reasons[0][:60]}")

    total = len(results)
    passed = sum(r["passed"] for r in results)
    by_layer: dict[str, list[bool]] = {}
    for result in results:
        by_layer.setdefault(result["layer"], []).append(result["passed"])

    print(f"\n{passed}/{total} passed ({passed / total:.0%})"
          + (f" · {len(skipped)} skipped (live-only: {', '.join(skipped)})" if skipped else ""))
    for layer, marks in sorted(by_layer.items()):
        print(f"  {layer:<24} {sum(marks)}/{len(marks)}")

    blocking_ok = all(
        all(marks) for layer, marks in by_layer.items() if layer.startswith(BLOCKING_LAYERS)
    )
    gate = blocking_ok and (passed / total) >= OVERALL_GATE
    print(f"\nRELEASE GATE: {'PASS' if gate else 'FAIL'} "
          f"(blocking layers {'clean' if blocking_ok else 'failing'}, "
          f"overall {passed / total:.0%} vs {OVERALL_GATE:.0%})")

    if not args.no_save:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        version = next_version()
        payload = {
            "version": version,
            "ts": datetime.now(UTC).isoformat(),
            "mode": "live" if live else "offline",
            "totals": {"passed": passed, "total": total, "rate": round(passed / total, 4)},
            "by_layer": {k: [sum(v), len(v)] for k, v in by_layer.items()},
            "gate": gate,
            "skipped": skipped,
            "cases": results,
        }
        path = RUNS_DIR / f"{version}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved {path.relative_to(ROOT)}")

    return 0 if gate else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="force the no-model path")
    parser.add_argument("--layer", help="filter by layer prefix, e.g. ⑤")
    parser.add_argument("--case", help="run a single case id")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
