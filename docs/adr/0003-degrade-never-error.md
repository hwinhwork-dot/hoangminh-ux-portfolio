# ADR-0003 — The studio degrades, it never errors

Date: 2026-08-10 · Status: accepted

## Context

The endpoint is public, unauthenticated and funded personally. It will hit rate limits,
budget ceilings, cold-start timeouts and provider incidents. The visitor is a recruiter
forming a first impression of a candidate's engineering judgement.

## Decision

No failure path returns an error to the browser. Missing key, exhausted budget, upstream
failure, timeout, unhandled exception — all resolve to a `200` with `degraded: true` and
an answer from the offline knowledge tier that already ships inside the page. The client
never rejects; `StudioClient.ask()` always resolves.

## Consequences

**Good.** The worst observable outcome is a less specific answer. The offline DB, which
already exists and is already good, becomes the availability floor instead of dead code.
The kill switch is simply removing the API key.

**Bad.** Failures are invisible to the visitor and therefore easy to ignore — which is
why `degraded` is a first-class field in the trace and fallback rate is an alerting
signal with a 15% threshold. A silent degradation that nobody watches is an outage in
slow motion.
