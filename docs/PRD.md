# PRD — AI Studio (portfolio assistant)

Owner: Nguyen Hoang Minh · v1.0 · 2026-08-10 · Status: baseline

Written in the same shape as the BRD on the live page, on purpose: the assistant is a
work sample, and the document that specifies it is part of the sample.

---

## 1. Problem

A recruiter spends 2–5 minutes on a portfolio. This one is dense on purpose — a journey
map, a problem tree, a VPC, a BRD with a traceability matrix, user stories, a UAT board.
The evidence that would win the interview is exactly the evidence a skim misses.

Meanwhile the questions recruiters actually have ("what level of PRD can he write?",
"how much of this did he own?", "when can he start?") are answerable in one sentence
each — just not by scrolling.

## 2. Goals / non-goals

**Goals**

- G1 — Let a visitor get a specific, sourced answer about Minh's work in under 15 seconds.
- G2 — Make the assistant itself a demonstration of AI product work: grounding, guardrails,
  evaluation, observability.
- G3 — Never regress the page. The animation and reading experience are the first
  impression and outrank every agent feature.

**Non-goals**

- Not a general chatbot. Not a career-advice tool. Not a CV generator.
- No account, no login, no stored conversation.
- No Vietnamese answers in v1 (questions in Vietnamese are accepted; answers stay English).

## 3. Users

| Persona | Context | Needs | Failure that loses them |
| --- | --- | --- | --- |
| **Recruiter / HR partner** (primary) | Screening a stack of candidates, phone or laptop | Fast, checkable facts; a contact route | A vague or invented answer |
| **Hiring manager** (secondary) | Assessing depth before an interview | Depth on method: how he writes requirements, how he tests | Shallow marketing language |
| **Peer / mentor** | Curious about the build | To see the engineering behind it | No visible substance |

## 4. Business requirements

| ID | Requirement | Success metric |
| --- | --- | --- |
| **BR-1** | A visitor can ask a free-text question and get a grounded, cited answer | ≥90% of golden-set grounding cases pass |
| **BR-2** | The assistant never states an unsupported fact about Minh | 100% of anti-hallucination and adversarial cases pass |
| **BR-3** | The assistant is available even when the model is not | 0 visible error states; degraded path serves an answer |
| **BR-4** | The existing page experience is unchanged | No regression in animation, reduced-motion, or Lighthouse score |
| **BR-5** | Hiring intent produces a contact route | Contact/CTA surfaced in every logistics and contact turn |
| **BR-6** | Running the assistant stays inside a personal budget | Daily cost ≤ the configured ceiling; over-budget degrades, never errors |

## 5. User stories

**P1 · Fast answer** — *As a recruiter, I want to ask "what level of PRD can he write?"
and get a specific answer, so that I can decide whether to book a call.*
`Given` a visitor with the studio open `When` they ask about a documented practice
`Then` a cited answer appears within 15 s, attributed to the agent who wrote it.

**P1 · Honest miss** — *As a recruiter, I want to be told when something is not known, so
that I can trust everything else the assistant says.*
`Given` a question with no supporting evidence `When` retrieval scores below the floor
`Then` the assistant says it is not indexed and offers the email route, and states no
fact of its own.

**P1 · Availability** — *As a visitor, I want the studio to work regardless of backend
state, so that the page never feels broken.*
`Given` no API key, a rate limit, or an upstream failure `When` a question is asked
`Then` an offline answer is served with `degraded: true` and no error is shown.

**P2 · Comparison** — *As a hiring manager, I want projects side by side, so that I can
judge scope quickly.*
`Given` a comparison question `When` the answer is composed `Then` Kai renders an
`ai-table` whose values match the knowledge base exactly.

**P2 · Contact** — *As a recruiter who has decided, I want the contact path immediately.*
`Given` a contact or logistics intent `When` Hana answers `Then` the email and phone are
present and the lead is logged.

**P3 · Boundary** — *As the portfolio owner, I want the assistant to refuse out-of-scope
work, so that it stays a portfolio, not a free tool.*
`Given` an out-of-scope or adversarial input `When` the input guard runs `Then` the turn
is refused with approved wording and zero tokens spent.

## 6. Scope

**In:** free-text Q&A over a versioned knowledge base; four-agent orchestration wired to
the existing stage animation; tables and bar charts; logistics and contact answers;
guardrails; golden-set evaluation; structured tracing.

**Out (v1):** streaming responses; Vietnamese answers; voice; CV file generation;
scheduling or calendar integration; any persistence of visitor data.

## 7. Success metrics

| Metric | Target | Source |
| --- | --- | --- |
| Studio open rate | ≥25% of sessions that scroll past the promo strip | client event |
| Questions per opened session | ≥3 | trace |
| Fallback ("not indexed") rate | ≤15% of turns | trace |
| p95 latency | ≤6 s | trace |
| Guard block rate | ≤10% | trace |
| Contact surfaced | 100% of contact/logistics turns | eval |

## 8. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| A hallucinated credential reaches a recruiter | Fatal to trust and to the candidacy | Retrieval floor + mandatory citations + canonical-fact check + golden set gate |
| Prompt injection makes the assistant say something damaging | Reputational | Input guard pre-LLM, output guard post-LLM, both tested |
| Cost runaway on a public endpoint | Personal budget | Rate limit + daily token ceiling + degrade-not-error |
| Latency breaks the animation illusion | Feels broken | 12 s client timeout, walk choreography sized to real latency, p95 alert |
| KB drifts from reality (a new project, a changed date) | Stale answers | KB is markdown in git, reviewed like code; `updated_at` per source |

## 9. Release gate

Ship when: all ① grounding and ⑤ adversarial golden-set cases pass, overall ≥90%, no open
blocking defect in `docs/UAT.md`, and the page renders identically with JavaScript for the
studio disabled.

Same gate the portfolio shows on its own UAT board — held open by one blocking defect,
publicly.
