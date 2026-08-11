---
source_id: practice-research
tier: 2
updated_at: 2026-08-10
summary: Research methods, design thinking loop, HCI lens, prototyping, metrics, tools and AI-first workflow.
---

# Practice — research, design and measurement

## Design Thinking, run as a full loop

1. **Empathize** — interviews, shadowing, journey research to understand the human, not
   the assumption.
2. **Define** — synthesize into a sharp problem, a value map, and a written requirements
   baseline.
3. **Ideate** — turn value into prioritised user stories with clear acceptance criteria.
4. **Prototype** — lo-fi to hi-fi, each fidelity built to answer a different question.
5. **Test** — usability sessions and UAT, feeding evidence and defects back into the loop.

He does not start with screens. He starts with people.

## Research toolkit

- **User interviews** — past behaviour rather than hypotheticals, no leading questions,
  5 Whys to reach the root.
- **Surveys** for scale.
- **Usability tests** with think-aloud, roughly **5 users per round**.
- **A/B and interleaving experiments** to decide with evidence.

Principle: qualitative finds the *why*, quantitative confirms *how common* it is.

## Journey mapping

Rows: doing · touchpoint · pain point · opportunity, over the stages of the experience,
with an emotion curve on top. The dip in the curve is where the design has to work
hardest. Example stages from the student case: Discover → Set up → First read → Daily use
→ Advocate, with the frustration trough at Set up.

## Problem framing

**Problem tree** — effects on top, core problem in the middle, root causes underneath, so
the team fixes the cause rather than the symptom. Example core problem: *students
disengage from the digital learning experience*, with root causes of high cognitive load
at activation, fragmented content with no sense of progress, and impersonal devices.

**Value Proposition Canvas** — customer profile on one side, value map on the other, with
explicit fit pairs: each pain mapped to a pain reliever, each gain to a gain creator.

## Prototyping

Prototypes in **Figma**, moving from **lo-fi wireframes** (to test structure, flow and
copy cheaply) to **hi-fi interactive prototypes** (to test hierarchy, trust and
micro-interactions). His rule: test the cheap thing first, because structure and copy are
the cheapest things to change and the most expensive to get wrong.

## HCI lens, applied to every flow

1. **Reduce cognitive load** — fewer choices per screen, progressive disclosure, defaults
   that do the thinking.
2. **Recognition over recall** — show options in context instead of asking people to
   remember them.
3. **Visible feedback** — every action confirms itself.
4. **Consistency** — patterns behave the same everywhere, so learning one screen teaches
   the rest.
5. **Error prevention** — design out the mistake, then make recovery painless.
6. **Match the real world** — language and flow follow how people actually think.

Comes from his university specialisation; applied concretely in the E-Reader activation
redesign.

## Metrics

Defined **before** building, and written into acceptance criteria as thresholds:

- **Activation rate** and setup time for onboarding.
- **D7 / D30 retention** for habit.
- **Task success rate** for usability.
- **NPS** for satisfaction — at SIHUB he turned scattered feedback into an NPS view
  reported to the Board.

## Design systems

Working-level understanding: tokens (colour, type, spacing) feeding components with
defined states, and patterns assembled from them. Applied in Figma and in this
portfolio's own consistent system. An org-scale system he would build alongside a senior
designer.

## Tools

**Figma** (wireframe → hi-fi prototype), **Notion** and **Jira** (docs, backlog and
tickets), **Python + Google Colab** (data analysis), **Git/GitHub** for versioned specs
and code, spreadsheets for trackers and RTMs, and **Claude / LLM agents** for AI-first
workflows. He picks the lightest tool that keeps the team aligned.

He also works on **accessibility** and **responsive/mobile** behaviour as part of
usability rather than as a late checklist — an interface that fails on a phone or with a
screen reader has failed the user, not a standard.

## AI-first workflow

Minh works AI-first and builds his own tooling:

- A custom **Claude skill** that writes concept-based specs through 7 guided sprints,
  asking what/why questions each sprint so the AI absorbs the real workflow, then packaged
  as a reusable command.
- **AI Studio** on this portfolio — a multi-agent system with triage, retrieval,
  knowledge and visualisation roles, grounded in a versioned knowledge base with layered
  guardrails and a golden-set evaluation. Designed and built by him.
- **ViVi**, the VinFast test-drive assistant, where he was Product Owner and UI/UX lead
  and built the LangGraph agent with its guarded tools.

His full AI product practice — problem framing, designing for uncertainty, agent
architecture, retrieval, guardrails, evaluation and commercial framing — is documented
separately in the AI product source.
