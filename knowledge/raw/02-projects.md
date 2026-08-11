---
source_id: projects
tier: 1
updated_at: 2026-08-10
summary: Work history and the three projects Minh led, with roles, scope and measured results.
---

# Projects & experience

## Timeline

| When | Where | What |
| --- | --- | --- |
| 2022 – 2026 | UEH University | B. of Technology & Innovation, GPA 3.57 |
| Jul – Dec 2024 | SIHUB — R&D Intern | City-level study, 150+ stakeholders |
| Jan – Oct 2025 | SIHUB — PM Executive | Startup journeys, A/B tests, Board reports |
| Mar – Jun 2025 | E-Reader ecosystem — Product Lead | HCI activation journey, Top 20 finalist |
| Sep – Dec 2025 | EchoMind — Product Owner | Brain-to-text system, 100% milestones |
| **Jul 2026 – Present** | **VinGroup — AI Talent** | **AI products end to end; PO & UI/UX on the VinFast test-drive assistant** |

## Comparison at a glance

| Project | Role | Focus | Result |
| --- | --- | --- | --- |
| **VinFast test-drive assistant** | Product Owner · UI/UX | Multi-agent booking assistant, guardrails, evals | Working product: agent + web UI + admin, containerised |
| **EchoMind** | Product Owner | AI brain-to-text, Agile + RACI | 55–65 WPM, <1 s latency, 100% milestones |
| **E-Reader Ecosystem** | Product Lead | HCI activation journey | Top 20 finalist (HCMC People's Committee) |
| **SIHUB** | PM Executive | Startup onboarding, insights, NPS | 150+ stakeholders, Board reporting |

---

## VinGroup — AI Talent (Jul 2026 – Present)

Selected into VinGroup's AI talent programme. He works across the full arc of an AI
product: deciding whether a problem needs AI at all, designing the agent and the interface
around it, building the retrieval and guardrail layers, and proving the result against an
evaluation set before release.

Specialising in **AI Product Management** — product strategy and market analysis, deep
PRDs and product-market fit, financial modelling and ROI for AI features, stakeholder
management, and roadmap planning under model uncertainty.

---

## VinFast test-drive assistant — "ViVi" (2026)

**Role: Product Owner and UI/UX lead.** He also built the agent.

A test-drive booking product for VinFast: a customer browses the vehicle catalogue, and a
conversational agent named **ViVi** helps them find a slot, hold it, verify their identity
and confirm the booking — with the deterministic UI and the agent sharing the same backend
services.

What he owned:

- **Product ownership** — problem framing, scope, the booking flow as a set of user
  stories with acceptance criteria, and the release decision.
- **UI/UX** — the catalogue and booking journey, from lo-fi wireframes to the built React
  interface, including how the assistant appears inside a transactional flow without
  taking control away from the customer.
- **Agent design and build** — a **LangGraph** agent with around ten guarded tools:
  search options, hold a slot, manage a booking draft, request and verify booking access,
  confirm the booking, and search a knowledge base.
- **Guardrails** — input guard, output guard and a guarded tool node, so the agent can
  only mutate booking data through allow-listed, validated tool calls. It never writes to
  the database directly.
- **Trust architecture** — an identity verification step before any booking is exposed,
  and an LLM-optional design so the catalogue and deterministic booking paths keep working
  when the model is unavailable.

Stack: FastAPI, LangGraph, React (Vite), Streamlit admin dashboard, PostgreSQL with a
SQLite adapter for tests, ChromaDB for knowledge search, Docker Compose, pytest suites for
guardrails, tools, services and API.

The design decision he is most attached to: **the agent never mutates data directly.**
Every state change goes through the same booking service the deterministic UI uses, so
the agent cannot invent a booking the rest of the system does not recognise.

---

## AI Studio — the assistant on this portfolio (2026)

**Role: designer and builder, end to end.**

A four-agent assistant embedded in this portfolio so a recruiter can interrogate the work
instead of scrolling it: Hana triages, Vy retrieves, Minh's agent answers, Kai renders
charts — with the on-screen choreography driven by the real orchestration trace.

Built with a versioned knowledge base as the only source of truth, hybrid retrieval with a
confidence floor, five layers of guardrails, a golden set of evaluation cases across
grounding, routing, refusal, anti-hallucination, adversarial and format, and a
degrade-never-error design so the page keeps working when the model does not.

---

## EchoMind — AI brain-to-text (Sep – Dec 2025)

**Role: Product Owner.**

- Ran the full product lifecycle on **Agile sprints** with a **RACI matrix** so ownership
  was never ambiguous.
- Drove the architectural move from a baseline model to a **Transformer** architecture.
- Delivered **100% milestone completion**.
- Measured outcomes: decoding at **55–65 words per minute** with **under 1 second**
  latency.

---

## E-Reader & Digital Education Ecosystem (Mar – Jun 2025)

**Role: Product Lead.**

- Applied **HCI principles** to redesign the student activation journey, from device
  provisioning through to content updates.
- Cut cognitive load at onboarding; decomposed pain points into a buildable feature set.
- Result: **Top 20 finalist** in a competition directed by the **HCMC People's Committee**.
- This is the case study the portfolio's journey map, problem tree and VPC are drawn from.

---

## SIHUB — Startup & Innovation Hub of HCMC (Jul 2024 – Oct 2025)

**Role: R&D Intern → PM Executive.**

- Owned **startup onboarding journeys** and collected founder insights.
- Ran **A/B and interleaving experiments** to decide with evidence.
- Led a **city-level study across 150+ stakeholders**.
- Turned scattered feedback into an **NPS** view reported directly to the **Board of
  Directors**.

---

## The portfolio itself, as evidence

The live site is a deliberate artifact of his own process, and is fair game to cite in an
interview:

- A **journey map** with an emotion curve and per-stage pains and opportunities.
- A **problem tree** separating effects, core problem and root causes.
- **VPC fit pairs** linking each pain and gain to a specific part of the solution.
- A **BRD** with a **requirement traceability matrix** running from business need to test
  result.
- **User stories** with Gherkin acceptance criteria.
- A scroll-scrubbed **lo-fi → hi-fi** prototype transition.
- A **UAT board** including a failing case and a release gate held open by a blocking
  defect.
- **AI Studio** — the multi-agent assistant, designed and built by him, including its
  guardrails and evaluation set.
