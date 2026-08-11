# ADR-0002 — Ground every answer in a versioned knowledge base

Date: 2026-08-10 · Status: accepted

## Context

The agent speaks about a real person to people making a hiring decision. Three options:

1. Put the whole profile in the system prompt.
2. Fine-tune a model on it.
3. Retrieve from a versioned knowledge base at answer time.

## Decision

Option 3. `knowledge/raw/*.md` is the single source of truth, chunked and indexed at
commit time, retrieved per turn, cited in the answer, and enforced by the output guard.
A retrieval floor prevents the answering node from running at all on weak evidence.

## Consequences

**Good.** A fact can be corrected with a text edit and a rebuild, not a retraining run.
Citations make answers checkable — a recruiter can open the same section on the page.
"Not indexed" becomes a first-class, testable outcome rather than an embarrassment. The
KB is reviewable in a pull request like any other requirement.

**Bad.** Retrieval can miss, and a miss reads as ignorance. Two moving parts (index and
prompt) instead of one. Requires the ingest step to be re-run and its output kept in sync.

**Rejected: option 1** — a growing profile in every request is paid for on every turn and
still leaves the model free to embellish. **Rejected: option 2** — fine-tuning bakes facts
into weights, which is exactly the wrong property for a résumé that changes.
