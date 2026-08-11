<h1 align="center">Nguyen Hoang Minh — UX Research & Product Discovery</h1>

<p align="center">
  A portfolio that doesn't describe the process — it <em>runs</em> it.<br/>
  Plus <strong>AI Studio</strong>: a four-agent assistant so a recruiter can interrogate the work instead of scrolling it.
</p>

<p align="center">
  <a href="https://hoangminh-ux-portfolio.vercel.app"><strong>Live site</strong></a> ·
  <a href="./ARCHITECTURE.md">Architecture</a> ·
  <a href="./docs/PRD.md">PRD</a> ·
  <a href="./docs/TEST-PLAN.md">Test plan</a>
</p>

---

## What this is

A single-page portfolio for a UX research / product discovery role. Every section is a
real artifact rather than a screenshot of one: an animated journey map with an emotion
curve, a problem tree whose connectors are drawn from live DOM positions, a value
proposition canvas of fit pairs, a BRD with a requirement traceability matrix, user
stories in Given/When/Then, a scroll-scrubbed lo-fi → hi-fi prototype transition, and a
UAT board with an honest failing test case.

Inside it lives **AI Studio** — a hand-drawn room where four agents (Hana the
facilitator, Vy the researcher, Minh the source of truth, Kai the analyst) hand a
question to each other and answer it from a versioned knowledge base. The walking
animation is not decoration: it replays the real orchestration trace.

## Stack

| Layer | Choice |
| --- | --- |
| Page | Hand-written HTML + CSS, GSAP 3 + ScrollTrigger. **No build step.** |
| Type | Satoshi, JetBrains Mono, Patrick Hand, Caveat |
| Agent API | Python serverless function on Vercel, FastAPI ASGI |
| Model | OpenAI GPT, optional — the site works without a key |
| Retrieval | Hybrid BM25 + embeddings over `knowledge/`, reranked, with a calibrated confidence floor. BM25 and the vector maths are stdlib-only — no numpy, no vector DB, ~64 KB index |
| Eval | Golden set + versioned runs in `eval/runs/` |
| Hosting | Vercel |

## Quick start

```bash
git clone <this-repo> && cd hoangminh-ux-portfolio

# 1. The page alone — no dependencies, no build
python3 -m http.server 3000        # open http://localhost:3000

# 2. With the agent
cp .env.example .env               # add OPENAI_API_KEY (optional)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/ingest_kb.py        # build knowledge/index from knowledge/raw
vercel dev                         # serves index.html + /api on one origin
```

Without an API key the studio still answers — it falls back to the offline knowledge
answers. That degradation path is deliberate and is covered by tests.

## Everyday commands

```bash
python scripts/ingest_kb.py        # rebuild the retrieval index after editing knowledge/
python scripts/check_policies.py   # guard regexes: blocks the bad, passes the real
python scripts/check_retrieval.py  # is the retrieval floor still calibrated?
pytest -q                          # 192 tests: guards, tools, retrieval, API (no network)
python eval/run_eval.py --offline  # golden set, no model calls, no tokens spent
python eval/run_eval.py            # golden set against the real model
ruff check .                       # lint
```

## Repository layout

```
index.html          the portfolio — one file, on purpose
assets/js/          studio client + offline fallback
api/index.py        the only serverless function
agent/              orchestrator · prompts · tools · guardrails · rag · observability
knowledge/raw/      the single source of truth about Minh (markdown, reviewed like code)
eval/               golden set, runner, one JSON per run
tests/              pytest, mirrors agent/
docs/               PRD, agent spec, test plan, UAT log, runbook, ADRs
scripts/            ingest_kb.py, dev.sh
```

Full reasoning, diagrams and trade-offs: **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

## How the agent stays honest

The interesting engineering problem here is not "make a chatbot" — it is **make a
chatbot that cannot lie about a person's résumé.** Five things enforce that:

1. **One source of truth.** Facts live in `knowledge/raw/*.md`, versioned in git and
   reviewed like code. The model is never asked to recall anything about Minh.
2. **A retrieval floor.** If the best-matching evidence scores below the threshold, the
   answering agent is never invoked. The user gets "I don't have that indexed" plus a
   direct contact route.
3. **Citations are mandatory.** The output guard rejects any factual answer with zero
   cited sources, before it reaches the browser.
4. **Hard-coded refusals.** Salary figures, opinions about third parties, and anything
   outside the portfolio are blocked at the input guard — no tokens spent, no room for
   the model to improvise.
5. **A golden set with a release gate.** Grounding and adversarial cases must be 100%
   green before deploy, mirroring the UAT gate shown on the page itself.

## Editing the knowledge base

`knowledge/raw/` is the highest-leverage folder in the repo — it is what the agent knows.

```bash
$EDITOR knowledge/raw/02-projects.md
python scripts/ingest_kb.py
python eval/run_eval.py --offline
git commit -m "kb: add <project> outcome metrics"
```

Rules: one fact per bullet, always dated, never a claim you can't defend in an interview.
Anything the agent must *not* answer goes in `06-boundaries.md` together with the exact
refusal wording.

## Deploy

`main` auto-deploys to Vercel. The knowledge index ships committed because Vercel has no
build step that could regenerate it. Environment variables, verification commands and the
kill switch: **[docs/DEPLOY.md](./docs/DEPLOY.md)**.

## Contact

**Nguyen Hoang Minh** — Ho Chi Minh City, Vietnam
[hwinh.work@gmail.com](mailto:hwinh.work@gmail.com) · +84 765 828 191

---

<sub>© 2026 Nguyen Hoang Minh. Code is MIT; the written content, artwork and personal
information in <code>knowledge/</code> and <code>index.html</code> are not.</sub>
