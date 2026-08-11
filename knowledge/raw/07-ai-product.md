---
source_id: ai-product
tier: 2
updated_at: 2026-08-10
summary: Minh's AI product practice — framing AI problems, designing for uncertainty, agent architecture, RAG, guardrails, evals, and the UX patterns specific to AI products.
---

# Practice — AI product

The through-line: Minh is a **UX and product person who builds AI systems**, not an ML
engineer. His edge is the seam most teams get wrong — the space between what a model can
do and what a user will trust.

## Framing: does this problem need AI at all?

Before any build, he answers four questions in order:

1. Does the problem genuinely need AI, or is a rule or a workflow enough?
2. If AI, at what level: **rule → workflow → agent**? Each step up buys capability and
   costs control.
3. Is the problem statement quantified enough to act on — baseline, target, and the cost
   of being wrong?
4. Decision: **Go / Not yet / No-go.**

He uses **Double Diamond** and human-centred discovery to get there, and treats
"Not yet" as a real, respectable outcome. Most AI features fail because nobody ran this
gate.

He also decides explicitly between **automate** (the system acts) and **augment** (the
system proposes, a human decides) — a product decision with a UX consequence, not a
technical one.

## Designing for uncertainty — the UX specialty

Classic UX assumes a deterministic system: the same input gives the same screen. AI
breaks that assumption, and most of the interesting design work lives in the break.

Patterns Minh designs with:

- **Confidence made visible.** The interface shows how sure the system is, so the user
  calibrates their trust instead of guessing.
- **Provenance and citations.** Every generated claim points back to a source the user
  can open. Trust comes from checkability, not from tone.
- **Graceful "I don't know".** An honest miss with a route forward beats a fluent wrong
  answer. This is designed for explicitly, not treated as an error state.
- **Reversibility.** Anything the system does on the user's behalf can be undone or
  reviewed before it commits.
- **Progressive disclosure of the machine.** Show the reasoning when the user needs it,
  hide it when they don't.
- **Latency as choreography.** When a system takes seconds, the wait is designed — the
  interface shows real work happening, not a spinner.

## AI safety, guardrails and responsible AI

Three HITL models he designs against: **human-in-the-loop** (approve before it acts),
**human-on-the-loop** (monitor and intervene), **human-in-command** (set the policy, the
system runs inside it). Choosing the right one is a product decision driven by the cost
of a wrong action.

He also designs the **escalation path** — what happens when the system reaches the edge
of its competence, who receives the handoff, and how the user is told. A system without a
designed escalation is a system that will fail silently in front of a customer.

Responsible AI in practice: **AI safety** treated as a design constraint rather than a
policy document — guardrails at the input and the output, red-teaming his own agents
before release, defence in depth against prompt injection and jailbreaks, and
transparency about what the system is and is not.

On **hallucination**: he treats a confident wrong answer as the most expensive failure a
system can have, and designs against it structurally — grounding every claim in
retrieved evidence, requiring citations, and setting a retrieval floor below which the
system declines rather than guesses.

## Agent architecture

- **Agentic Fit** — when a chatbot is enough and when the problem earns an agent.
- **ReAct loop** — Thought → Action → Observation, with traces read as a debugging
  artifact.
- **Tool design** — clear schemas, narrow responsibilities, predictable error handling.
  A tool that can fail ambiguously will.
- **System prompt engineering** — role, task, context, output contract, constraints; and
  the discipline that a rule a model *can* break is not a guardrail, it is a suggestion.
- **Multi-agent patterns** — supervisor and specialist roles, agent-to-agent handoff,
  MCP-style tool connectivity, and knowing when one good agent beats four mediocre ones.
- **Memory** — what an agent should carry between turns and what it should deliberately
  forget.

## Retrieval (RAG)

Chunking strategy, embedding models, **vector stores** (Chroma, FAISS) and their index
internals, metadata filtering, hybrid lexical + dense search, reranking, and a
**confidence floor** below which the system declines to answer.

His position: most RAG failures are not model failures. They are chunking, retrieval and
grounding failures — which makes them **product** problems with product fixes.

## Evaluation

He treats evals as acceptance criteria for AI:

- A **golden set** written before the build, covering grounding, routing, refusal,
  anti-hallucination, adversarial and format cases.
- Versioned runs, so a prompt change is a claim and the run file is its evidence.
- **Accuracy** measured against that set rather than asserted, and tracked as a
  benchmark across prompt revisions instead of judged by demo.
- **Release gates** — grounding and adversarial cases must be perfect before shipping,
  the same discipline as a UAT gate.

## Data and operations

Data pipelines feeding AI features, the six dimensions of data quality, and
**observability** — because an agent reading bad data answers confidently and wrongly,
and nobody notices until a user complains. Deployment to **cloud** infrastructure on
containers and serverless, **scaling** and reliability for agent workloads, CI/CD with
eval gates, and cost per request treated as a product constraint rather than an
infrastructure detail.

## Commercial framing

Token and inference cost modelled per feature, **ROI framing** for AI investment, and
translating a technical capability into a business case a non-technical stakeholder can
approve or reject. AI product strategy, market analysis, product-market fit for AI
features, and roadmap and milestone planning under model uncertainty.

## Specialisation

Minh's chosen depth is **AI Product Management** — strategy and market analysis, deep
PRDs and product-market fit, financial modelling and ROI, stakeholder management, and
roadmap planning for AI products.
