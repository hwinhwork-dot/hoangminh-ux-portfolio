# Deploying

The site is live at **https://hoangminh-ux-portfolio.vercel.app** and `main` auto-deploys.
This page is the short version of what production needs that the repository cannot
provide by itself.

## What the repository already handles

| | |
| --- | --- |
| Static page | `index.html` at the root, served directly. No build step. |
| API | `vercel.json` routes every `/api/*` path to `api/index.py` and bundles `agent/**` and `knowledge/**` alongside it. |
| Knowledge base | `knowledge/index/index.json` is **committed**. Vercel has no build step that could regenerate it, so the artifact ships with the code — see the note in `.gitignore`. |
| Cold start | 2.6 ms to load and decode the index, 0.2 ms for a lexical search. No numeric stack to import. |

## Environment variables — set these in the Vercel dashboard

Project → Settings → Environment Variables, for **Production** (and Preview if you want
previews to answer too). Nothing here can be set from the repository, and the site
behaves differently depending on which are present.

| Variable | Value | Effect if missing |
| --- | --- | --- |
| `OPENAI_API_KEY` | your key | **The agent answers by quoting the knowledge base verbatim instead of composing.** Grounded and honest, just terse. Everything else keeps working. |
| `ENV` | `production` | Only affects the label in `/api/health`. |
| `ALLOWED_ORIGINS` | `https://hoangminh-ux-portfolio.vercel.app` | Defaults to `*`. The studio is same-origin so nothing breaks, but leaving it open lets any site call the endpoint on your budget. Add a custom domain here too if you add one. |
| `DAILY_TOKEN_BUDGET` | `200000` | Defaults to 200k. This is the real ceiling on spend — the rate limiter is per-instance and best-effort. |
| `LLM_MODEL` | `gpt-4.1-mini` | Defaults to the same. |
| `LLM_TRIAGE_MODEL` | `gpt-4.1-nano` | Defaults to the same. Only called when no routing rule matches. |
| `RAG_MIN_SCORE` | `0.20` | Defaults to the same. **Do not change without re-running `scripts/check_retrieval.py`** — it is calibrated, not chosen. |

Redeploy after adding them: environment variables are read at cold start, so an existing
deployment keeps the old values until it is replaced.

## Verifying a deploy

```bash
curl -s https://hoangminh-ux-portfolio.vercel.app/api/health | python3 -m json.tool
```

What good looks like:

```json
{ "ok": true, "env": "production", "llm_enabled": true,
  "model": "gpt-4.1-mini", "index": { "chunks": 57, "vectors": true } }
```

| Symptom | Cause |
| --- | --- |
| `"chunks": 0` | The index did not ship. Run `python scripts/ingest_kb.py` and commit `knowledge/index/index.json`. |
| `"vectors": false` | The index was built without a key. Rebuild with `OPENAI_API_KEY` set — lexical-only still works, but paraphrase matching is weaker. |
| `"llm_enabled": false` | `OPENAI_API_KEY` is not set in Vercel, or the daily budget is spent. |

Then ask it something real:

```bash
curl -s -X POST https://hoangminh-ux-portfolio.vercel.app/api/chat \
  -H 'content-type: application/json' \
  -d '{"message":"Which level of PRD can Minh write?","session_id":"check","history":[]}'
```

## Before each deploy

```bash
python scripts/ingest_kb.py --check    # index must agree with knowledge/raw
python scripts/check_policies.py       # guards block the bad, pass the real
python scripts/check_retrieval.py      # the floor still separates
pytest -q                              # 192 tests, no network
python eval/run_eval.py                # release gate, twice — flakes are defects
```

Run the eval **twice**. Three separate defects in this project passed a first run and
failed the second; a single green run would have shipped all three.

## Rolling back

Vercel → Deployments → the last good one → Promote. Then note which `eval/runs/*.json`
corresponded to the bad deploy, so the regression is provable rather than remembered.

## Kill switch

Remove `OPENAI_API_KEY` from the Vercel environment and redeploy. The studio drops to
quoting the knowledge base. Nothing breaks; the page keeps working.
