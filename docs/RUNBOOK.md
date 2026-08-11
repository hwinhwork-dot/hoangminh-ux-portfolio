# Runbook

Operational notes for a one-person system. The design goal is that nothing here is ever
urgent: every failure path degrades to a working page.

## Deploy

`main` auto-deploys. To promote deliberately: `vercel --prod`.

Pre-deploy: `pytest -q` green, `python eval/run_eval.py` meeting the gate, and the page
regression checklist in `docs/TEST-PLAN.md`.

## Environment variables

Set in Vercel → Project → Settings → Environment Variables, shape documented in
`.env.example`. `OPENAI_API_KEY` is the only one whose absence changes behaviour —
without it the studio serves offline answers, which is a valid state, not an outage.

## Common situations

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Every answer arrives with `degraded: true` | Missing/expired key, or the daily budget is spent | Check `/api/health`; check the day's cost line in the logs |
| A specific question returns "not indexed" | Genuine knowledge gap | Add it to `knowledge/raw/`, `python scripts/ingest_kb.py`, add a golden-set case, deploy |
| A real HR question is being refused | Over-tight input guard pattern | Narrow the pattern in `policies.yaml`, add the question as a must-pass case |
| p95 latency above 6 s | Cold start, or too many retrieved chunks | Reduce `RAG_RERANK_TOP_N`; consider streaming (ADR-0003) |
| Answer contains something wrong about Minh | KB error or a guard hole | Fix the KB first, then add the exact input to the golden set as an anti-hallucination case |
| Rate-limit complaints | Threshold too low for a real reader | Raise `RATE_LIMIT_PER_MIN`; watch the cost line |

## Rollback

Vercel → Deployments → the last good one → Promote. Then note which `eval/runs/` file
corresponded to the bad deploy, so the regression is provable rather than remembered.

## Weekly review (15 minutes)

1. Read the unanswered-query log — every entry is a knowledge gap or a routing bug.
2. Check the four health signals against their thresholds (ARCHITECTURE.md §8).
3. Look at the guard block log for false positives, which cost more than false negatives.
4. Update the KB, rebuild the index, run the eval, commit.

## Kill switch

Remove `OPENAI_API_KEY` from the Vercel environment. Within one deployment cycle the
studio serves offline answers only. Nothing breaks; the page keeps working.
