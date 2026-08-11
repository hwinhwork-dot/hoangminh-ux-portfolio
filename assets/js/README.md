# assets/js

The page still ships as a single `index.html` — that is deliberate and documented in
ARCHITECTURE.md §12 (D1). This folder holds the modules the studio is being extracted
into, one safe step at a time.

| File | Status | Step |
| --- | --- | --- |
| `studio-client.js` | written | 2 — transport + fallback switch |
| `studio-fallback.js` | to do | 1 — move the offline `DB[]` array out of index.html verbatim |
| `ai-studio.js` | to do | 1 — move the studio IIFE out of index.html verbatim |

Order matters. Step 1 is a pure move with no behaviour change and can be verified by
diffing rendered output. Only after that does step 2 become a one-line swap inside
`orchestrate()`, and step 3 replaces the hard-coded `sleep()` choreography with the
`trace` array the API returns.

Nothing here touches GSAP, the pinned lo-fi→hi-fi scrub, the day/night cycle or the
`prefers-reduced-motion` branches. Those stay in `index.html`.
