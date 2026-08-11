---
source_id: practice-requirements
tier: 2
updated_at: 2026-08-10
summary: How Minh writes PRDs, BRDs, user stories, acceptance criteria, traceability and UAT; how he runs Agile.
---

# Practice — requirements, delivery and testing

## PRD — what level he writes

Minh writes **feature-level PRDs end to end**: problem statement, goals and non-goals,
user stories with acceptance criteria, flows, edge cases and success metrics. He also
builds the **BRD baseline** and maintains a **requirement traceability matrix** so nothing
is lost on the way to UAT.

For org-wide, multi-team PRDs he still asks for a senior review pass — which he considers
healthy at his stage rather than a gap to hide. Proof of level: the Requirements section
of the portfolio.

## BRD

Structure he uses:

- **Objective** — the business outcome, stated as a measurable change.
- **Scope** — explicitly in and explicitly out.
- **Stakeholders**.
- **Business requirements** — coded (`BR-1`, `BR-2`, …) so they can be traced.
- **Success metrics**.

Each `BR-n` is then linked to a user story, its acceptance criteria and a UAT case
through the traceability matrix.

Live example on the site — *BRD v1.2, Digital learning activation*:

| Field | Content |
| --- | --- |
| Objective | Raise week-one activation and 7-day retention for new students |
| Scope | **In:** onboarding, reading, progress. **Out:** payments, admin portal |
| Stakeholders | Students, teachers, content team, engineering |
| BR-1 | Reduce setup friction |
| BR-2 | Show progress |
| BR-3 | Surface struggling students |
| Metrics | Activation rate, D7 retention, setup completion time |

## Requirement traceability matrix (RTM)

Every requirement is traced from business need to a verified test result.

| Need | User story | Acceptance criteria | Test | Status |
| --- | --- | --- | --- | --- |
| BR-1 | Set up without help | Setup completes in 3 steps or fewer | UAT-1 | Passed |
| BR-2 | See my progress | Streak and next goal shown first | UAT-2 | Passed |
| BR-3 | See class engagement | Low-activity students are flagged | UAT-3 | In test |
| BR-2 | Get a gentle nudge | Reminder after 3 inactive days | UAT-4 | Backlog |

## User stories & acceptance criteria

Format: **As a … I want … so that …**, with **Gherkin** acceptance criteria
(Given / When / Then) written so they double as UAT scenarios. He follows **INVEST** and
prioritises with **MoSCoW** or value-vs-effort.

Examples:

- *P1 · Activation* — As a new student, I want to set up my device without help, so that
  I can start reading in minutes.
  `Given` a first-time student `When` they open the device `Then` setup completes in
  under 3 steps.
- *P1 · Retention* — As a returning student, I want to see my progress, so that I stay
  motivated to come back.
  `Given` a returning student `When` they open the app `Then` a streak and next goal are
  shown first.
- *P2 · Trust* — As a teacher, I want to see class engagement, so that I can support
  struggling students.
  `Given` a class is enrolled `When` the teacher opens the dashboard `Then` low-activity
  students are flagged.

## UAT

Planned directly from the acceptance criteria: test scenarios, expected results,
pass/fail runs with real users, defect logging and clarification with engineering, and a
clear **release acceptance gate** — approved only when all P1 scenarios pass and no
blocking defect is open.

The live board carries an honest failure: *UAT-3, teacher spots struggling students* —
the low-activity flag is delayed. Logged, clarified, gate held.

## Agile delivery

- **Scrum**: sprint planning, disciplined execution, milestone reviews.
- **RACI matrix** so ownership is never ambiguous.
- Product backlog maintained with MoSCoW / value-effort prioritisation.
- A change log for scope moves.
