# Test plan — AI Studio

v1.0 · 2026-08-10

## Layers

| Layer | What it proves | Where | Needs a key? |
| --- | --- | --- | --- |
| Policy smoke | Guard regexes: nothing damaging passes, nothing legitimate is refused | `scripts/check_policies.py` | no |
| Retrieval floor | The answerable and the unanswerable actually separate | `scripts/check_retrieval.py` | no |
| Index gates | Front matter, chunk sanity, corpus shrink | `scripts/ingest_kb.py --check` | no |
| Unit | Guards, routing, chart markup, chunking | `tests/` | no |
| Retrieval | The right chunk is findable, and unknowns stay unknown | `tests/test_rag/` | no |
| Contract | `/api/chat` shape, degradation, rate limit | `tests/test_api/` | no |
| Behavioural | The agent answers a recruiter correctly | `eval/golden_set.json` | yes (or `--offline`) |
| Manual UAT | The experience on a real page, on real devices | `docs/UAT.md` | yes |

Most of the surface is testable without a model. That is a design outcome: only one node
is generative, so everything else can be asserted deterministically.

## Golden set

42 cases across six layers — grounding, routing, refusal, anti-hallucination, adversarial,
format. Written before the implementation, in the same spirit as acceptance criteria
written before the build.

```bash
python scripts/check_policies.py      # guard regexes, sub-second, no deps but pyyaml
python scripts/check_retrieval.py     # floor calibration; --sweep shows the trade-off
python eval/run_eval.py --offline     # guards, routing, retrieval — free
python eval/run_eval.py               # full, real model
python eval/run_eval.py --layer ⑤     # adversarial only
```

Every run writes `eval/runs/vN_<date>.json`. Commit the run file with the change that
caused it — the run file is the evidence, the diff is the claim.

## Release gate

| Condition | Threshold |
| --- | --- |
| ① Source of truth | 100% |
| ⑤ Adversarial | 100% |
| Overall | ≥ 90% |
| Blocking defects open | 0 |
| Page regression | none (animation, reduced-motion, no-JS studio) |

A failed ① or ⑤ case is a blocking defect by definition — those are the two layers where a
failure damages a real person's reputation.

## Regression checklist for the page

Run before any deploy that touched `index.html` or `assets/js/`:

- [ ] Hero parallax, rotating role, concept-spec scan still animate
- [ ] Journey emotion path draws on scroll; column hover highlights the stage
- [ ] Problem-tree connectors redraw correctly on resize and at ≤760 px
- [ ] Lo-fi → hi-fi pinned scrub reaches 100% and releases the pin
- [ ] Studio opens from all four entry points: nav link, hero button, promo card, FAB
- [ ] FAB and hint appear only after the promo strip scrolls out
- [ ] Day/night cycle runs and returns to day
- [ ] `prefers-reduced-motion: reduce` disables walking, idle and cycle animations
- [ ] Mobile ≤940 px: stage hidden, chat full width, no horizontal scroll
- [ ] Escape and backdrop click close the overlay; body scroll restored

## Defect flow

Found → logged in `docs/UAT.md` with an id, severity and the reproducing input →
fixed → the reproducing input is added to `eval/golden_set.json` → run recorded. A defect
that does not become a test case will happen again.
