"""Calibrate and regression-test the retrieval floor against the golden set.

The floor is the anti-hallucination mechanism, and a floor is only meaningful if two
populations actually separate:

  * questions the knowledge base **can** answer must score above it;
  * questions it **cannot** must score below.

This script measures both and reports the margin. Run it after any edit to
`knowledge/raw`, the tokenizer, or the scoring — all three move the distributions.

    python scripts/check_retrieval.py            # report + exit 1 if the floor is wrong
    python scripts/check_retrieval.py --sweep    # show the trade-off across thresholds

A note on what the floor can and cannot do. It catches *topical* misses — "which
companies in Singapore" has no purchase on this corpus at all. It cannot catch
*fact-level* gaps: "how many people reported to him at EchoMind" retrieves the EchoMind
passage perfectly well, because the topic is present and only the specific fact is
missing. That case is caught by the second defence — the answering node returns
NOT_INDEXED and the output guard rejects uncited claims. Any attempt to make the floor
alone catch it ends up refusing real questions. Two defences, two jobs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.config import get_settings  # noqa: E402
from agent.orchestrator.retrieval import retrieve_for  # noqa: E402
from agent.rag.retrieve import load_index  # noqa: E402

GOLDEN = ROOT / "eval" / "golden_set.json"

# Only `unknown_topic` cases belong to the floor. `unknown_fact` cases retrieve their
# surrounding topic correctly and by design — see the module docstring — and
# `premise_correction` cases must retrieve in order to be corrected at all.
ANSWERABLE_TYPES = {"grounded", "premise_correction"}
FLOOR_TYPES = {"unknown_topic"}


def top_score(query: str) -> tuple[float, list[str]]:
    """Đi đúng đường mà orchestrator đi — mở rộng, chấm điểm, dự phòng."""
    hits = retrieve_for(query)
    return (hits[0].score if hits else 0.0), [h.source_file for h in hits]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args()

    index = load_index()
    if index is None:
        print("no index — run `python scripts/ingest_kb.py` first")
        return 1

    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    answerable = [c for c in cases if c["type"] in ANSWERABLE_TYPES]
    refusable = [c for c in cases if c["type"] in FLOOR_TYPES]
    downstream = [c for c in cases if c["type"] == "unknown_fact"]

    floor = get_settings().min_score
    mode = "hybrid (dense + lexical)" if index.vectors else "lexical only (no embeddings)"
    print(f"index: {index.n} chunks · {mode}")
    print(f"floor: {floor}\n")

    failures = 0

    print("=== MUST BE ANSWERABLE (score >= floor, expected source retrieved) ===")
    answerable_scores = []
    for case in answerable:
        score, sources = top_score(case["input"])
        answerable_scores.append(score)
        want = case.get("expected_sources", [])
        source_ok = not want or any(w in sources for w in want)
        above = score >= floor
        ok = source_ok and above
        failures += not ok
        note = "" if ok else ("  <- below floor" if not above else "  <- wrong source")
        print(f"  {'ok  ' if ok else 'FAIL'} {score:.3f}  {case['id']}  {sources[:2]}{note}")

    print("\n=== MUST BE REFUSED (score < floor) ===")
    refusable_scores = []
    for case in refusable:
        score, _ = top_score(case["input"])
        refusable_scores.append(score)
        ok = score < floor
        failures += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {score:.3f}  {case['id']}  {case['input'][:52]}")

    low = min(answerable_scores) if answerable_scores else 0.0
    high = max(refusable_scores) if refusable_scores else 0.0
    print(f"\nanswerable min = {low:.3f}   refusable max = {high:.3f}   margin = {low - high:+.3f}")
    if low > high:
        print(f"a valid floor lies anywhere in ({high:.3f}, {low:.3f}]; configured {floor}")
    else:
        print("NO VALID FLOOR — the two populations overlap. Fix the knowledge base or "
              "the scoring, not the threshold.")
        failures += 1

    if args.sweep:
        print("\n=== SWEEP ===")
        print(f"{'floor':>6} {'answered':>9} {'refused':>8}  note")
        step = 0.02
        for i in range(5, 26):
            candidate = round(i * step, 2)
            answered = sum(s >= candidate for s in answerable_scores)
            refused = sum(s < candidate for s in refusable_scores)
            perfect = answered == len(answerable_scores) and refused == len(refusable_scores)
            print(f"{candidate:>6.2f} {answered:>4}/{len(answerable_scores):<4} "
                  f"{refused:>3}/{len(refusable_scores):<4}  {'<- valid' if perfect else ''}")

    if downstream:
        print("\n=== NOT THE FLOOR'S JOB (topic present, fact absent) ===")
        print("    These retrieve on purpose. The answering node must return NOT_INDEXED")
        print("    and the output guard must reject any uncited claim. Covered by eval/run_eval.py.")
        for case in downstream:
            score, sources = top_score(case["input"])
            print(f"    {score:.3f}  {case['id']}  {sources[:1]}  {case['input'][:44]}")

    print(f"\n{'ALL GREEN' if not failures else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
