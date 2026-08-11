# knowledge/

**The highest-leverage folder in this repository.** It is the only place the agent may
learn a fact about Minh. If something is not written here, the correct answer is "I have
not indexed that yet".

```
raw/     source markdown, git-versioned, reviewed like code
index/   build artifacts — gitignored, rebuilt by scripts/ingest_kb.py
```

## Sources and authority

| File | Tier | Holds |
| --- | --- | --- |
| `01-profile.md` | 1 | Identity, education, certifications, availability, skill levels |
| `02-projects.md` | 1 | Work history and the three projects, with measured results |
| `03-practice-requirements.md` | 2 | PRD/BRD, stories, acceptance criteria, RTM, UAT, Agile |
| `04-practice-research.md` | 2 | Research methods, design thinking, HCI, metrics, tools, AI workflow |
| `05-hr-faq.md` | 3 | Pre-approved wording for recruiter questions |
| `07-ai-product.md` | 2 | AI product practice: framing, designing for uncertainty, agents, RAG, guardrails, evals, ROI |
| `06-boundaries.md` | 4 | Policy: what must never be answered, and the exact refusal text |

Tier 1 wins when two sources disagree. Tier 4 is policy, not knowledge, and is mirrored
in `agent/guardrails/policies.yaml` — keep the two in sync.

## Front matter

Every file starts with:

```yaml
---
source_id: projects
tier: 1
updated_at: 2026-08-10
summary: one line, used in retrieval debugging
---
```

## Editing rules

1. One fact per bullet. A bullet that needs a comma-spliced second claim is two bullets.
2. Always dated where a date exists. "Recently" is not a fact.
3. Never write a claim you could not defend in an interview — this text will be quoted
   back to Minh by a recruiter.
4. `##` headings are the chunk boundary, so each section must stand alone. A reader
   landing on that heading with no surrounding context should still get a complete answer.
5. Numbers are canonical. If a figure appears in `policies.yaml: canonical_facts`,
   changing it here means changing it there.

## After editing

```bash
python scripts/ingest_kb.py        # rebuild the index (gates run automatically)
python eval/run_eval.py --offline  # retrieval still finds every golden-set case
```
