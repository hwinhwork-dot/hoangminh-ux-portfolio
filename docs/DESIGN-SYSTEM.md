# Design system

Not a component library — a documented set of decisions already living in `:root` and the
`.ai-*` scope of `index.html`. Written down so the agent's rendered output and any future
extraction stay consistent with the page.

## Two worlds, on purpose

The page has two visual registers and they must not blend:

| | Portfolio | AI Studio |
| --- | --- | --- |
| Register | Editorial, precise, calm | Hand-drawn, warm, playful |
| Ink | `--ink #18191d` | `--dk #24365e` |
| Accent | `--accent #ff5630` | `--yel #f6c34d` |
| Surface | `--paper #f3f2ee` / `--surface #fff` | `--paperw #fdfcf7` |
| Type | Satoshi, JetBrains Mono | Patrick Hand, Caveat |
| Borders | 1 px hairline, `rgba(24,25,29,.10)` | 2.5 px ink, wobbly radii, hard offset shadow |
| Shadow | Soft, large, low opacity | `4px 5px 0` solid — a paper-on-desk shadow |

The contrast is the point: the studio should feel like a sketchbook someone left inside a
precise document.

## Tokens

```
--paper #f3f2ee   --surface #ffffff  --ink #18191d   --ink-2 #595d68   --ink-3 #9b9ea8
--accent #ff5630  --accent-2 #ff8a5c --accent-soft rgba(255,86,48,.10)
--pass #1d8f5b    --fail #c0341a     --warn #c98a1e
--max 1200px      --ease cubic-bezier(.22,1,.36,1)

studio: --dk #24365e  --dk2 #3a4f80  --yel #f6c34d  --blu #2f6fb8
        --redd #e0492f --grn #2f9469 --paperw #fdfcf7
        --wob1 / --wob2  (the irregular border-radius pairs that make edges look drawn)
```

## Motion

| Pattern | Where | Rule |
| --- | --- | --- |
| Batched reveal | `.reveal` via `ScrollTrigger.batch` | Items entering together cascade at 0.09 s |
| Scrubbed rise | `[data-rise]` | Tied to scroll, `ease: none` |
| Path draw | Journey curve, tree connectors | `strokeDashoffset` to 0 on enter |
| Pinned scrub | Lo-fi → hi-fi | 120% of viewport, progress drives opacity and the fill bar |
| Idle life | Steam, bars, leaves, lantern, stars | Long loops (2.6–26 s), never synchronised |
| Agent walk | Studio stage | 1.38 s per hop, transform-only |

**Reduced motion is not an afterthought.** Every animation above has an explicit
`prefers-reduced-motion: reduce` branch, and agents jump instead of walking. Any new
motion must ship with its own branch.

## Rules for agent-rendered HTML

The output guard allows only what this page already styles:

- `<b>` for load-bearing facts; `<i>` sparingly; `<br>` for line breaks.
- `<table class="ai-table">` — left-aligned, dashed header rule, no zebra striping.
- `<div class="ai-bars">` with `data-v` on each `track i` so the fill transition runs.
- `<span class="cap">` for a caption line.
- Nothing else. No headings, no links, no inline styles, no scripts.
