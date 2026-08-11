# Prompts

Versioned as markdown so they can be **reviewed in a pull request** like any other
requirement. The HTML comment at the top of each file is the front matter: `prompt_id`,
`version`, the node that loads it, and the model tier it runs on.

| File | Node | Generative? |
| --- | --- | --- |
| `00-shared-context.md` | prepended to every generative node | — |
| `10-hana-triage.md` | `nodes/triage_hana.py` | yes, cheap tier, JSON out |
| `20-minh-answer.md` | `nodes/answer_minh.py` | yes, main model |
| — | `nodes/research_vy.py` | **no** — deterministic retrieval |
| — | `nodes/viz_kai.py` | **no** — deterministic templating |

## Changing a prompt

1. Bump `version` (semver: patch = wording, minor = new rule, major = contract change).
2. `python eval/run_eval.py` before and after.
3. Commit the prompt change and the new `eval/runs/*.json` **together** — the run file is
   the evidence that the change helped.
4. If the pass rate drops on any ① grounding or ⑤ adversarial case, the change does not
   ship. That is the release gate, same as UAT on the live page.

## Why rules live in code, not only here

Anything a model *can* violate under pressure is not a guardrail, it is a suggestion.
The prompts state the policy; `agent/guardrails/` enforces it. When the two disagree,
the code wins and the prompt is the bug.
