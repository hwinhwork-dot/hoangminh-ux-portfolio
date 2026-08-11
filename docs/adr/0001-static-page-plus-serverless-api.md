# ADR-0001 — Keep the static page, add a serverless API

Date: 2026-08-10 · Status: accepted

## Context

The portfolio is a single 1 800-line `index.html` already deployed on Vercel: hand-tuned
GSAP choreography, a pinned scroll scrub, an SVG studio scene, a day/night cycle, and
complete `prefers-reduced-motion` branches. It needs a real agent backend.

The obvious alternative was migrating to Next.js and getting routing, API routes and a
component model in one move.

## Decision

Keep `index.html` exactly where it is. Add one Python serverless function at
`api/index.py`, routed by `vercel.json`, with the agent code in `agent/` bundled via
`includeFiles`.

## Consequences

**Good.** Zero risk to the animation work, which is the actual portfolio. No build step,
so the page stays inspectable — a recruiter opening dev tools sees hand-written code.
Same origin, so no CORS. Cold start is one function, not a framework.

**Bad.** No component reuse if a second page appears. The 146 KB single file is awkward
to edit — mitigated by the staged extraction into `assets/js/` (ARCHITECTURE.md §7).
Python on Vercel bundles less conveniently than Node.

**Revisit when** a second page, authentication, or a CMS is needed. Not before.
