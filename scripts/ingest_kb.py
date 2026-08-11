"""Build knowledge/index from knowledge/raw.

Run after every edit to the knowledge base. Commit only the source markdown — the index
is a build artifact (see .gitignore).

    python scripts/ingest_kb.py            # build (embeddings if a key is configured)
    python scripts/ingest_kb.py --check    # run the data-quality gates only
    python scripts/ingest_kb.py --no-vectors   # lexical-only, spends nothing
    python scripts/ingest_kb.py --force    # build despite gate failures (last resort)

Without OPENAI_API_KEY the index builds lexical-only and retrieval still works. That is
the same degradation path the live studio uses, so it is worth exercising.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.config import KNOWLEDGE_INDEX, KNOWLEDGE_RAW  # noqa: E402
from agent.rag.chunk import chunk_corpus  # noqa: E402
from agent.rag.ingest import IngestError, build_index, run_gates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="run gates only, write nothing")
    parser.add_argument("--no-vectors", action="store_true", help="skip embeddings")
    parser.add_argument("--force", action="store_true", help="write despite gate failures")
    args = parser.parse_args()

    print(f"raw:   {KNOWLEDGE_RAW}")
    print(f"index: {KNOWLEDGE_INDEX}\n")

    if args.check:
        from agent.rag.ingest import _allowed_sources

        chunks = [c for c in chunk_corpus(KNOWLEDGE_RAW) if c.source_file in _allowed_sources()]
        failures = run_gates(chunks, KNOWLEDGE_RAW, KNOWLEDGE_INDEX)
        if failures:
            print(f"GATES FAILED ({len(failures)}):")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(f"gates passed · {len(chunks)} chunks")
        return 0

    try:
        report = build_index(
            KNOWLEDGE_RAW,
            KNOWLEDGE_INDEX,
            force=args.force,
            with_vectors=not args.no_vectors,
        )
    except IngestError as exc:
        print("GATES FAILED — index not written:")
        print(exc)
        return 1

    print(f"{report['chunks']} chunks · {report['tokens_total']} tokens · "
          f"{report['vocabulary']} vocabulary · {report['bytes'] / 1024:.1f} KB")
    for source, count in report["sources"].items():
        print(f"  {source:32} {count:3}")
    if report["vectors"]:
        print(f"\nvectors: yes ({report['embedding_model']})")
    else:
        print("\nvectors: no — lexical-only index. Set OPENAI_API_KEY and re-run "
              "to enable paraphrase matching.")
    if report["gate_failures"]:
        print(f"\nWARNING: written with --force despite {len(report['gate_failures'])} gate failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
