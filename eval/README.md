# eval/

Behavioural tests for the agent. Unit tests prove the code works; these prove the
*product* works — that a recruiter asking a real question gets a correct, sourced,
in-bounds answer.

```
golden_set.json   42 cases across six layers
run_eval.py       runner + grader
runs/             one JSON per run, versioned, committed
```

## Layers

| Layer | Cases | Asks |
| --- | --- | --- |
| ① Source of truth | G01–G14 | Is the answer right, and does it cite the right source? |
| ② Routing | R01–R07 | Did the right agent handle it? |
| ③ Refusal | S01–S05 | Did it decline what it must decline, with a route forward? |
| ④ Anti-hallucination | H01–H06 | Does it stay silent about what it does not know? |
| ⑤ Adversarial | A01–A06 | Does it hold under injection and impersonation? |
| ⑥ Format | V01–V04 | Does the markup render in the existing CSS? |

## Why runs are committed

Prompts live in git, so their history is already kept. What git does not keep is *what a
change did to behaviour*. `runs/vN_<date>.json` is that record: a prompt or policy diff
plus its run file is a claim plus its evidence.

## Adding a case

Add a case whenever:

- a defect is found (the reproducing input becomes the case),
- a knowledge gap is filled (prove it is now answerable),
- a guard is loosened (prove it still blocks what matters).

A defect that does not become a case will recur.
