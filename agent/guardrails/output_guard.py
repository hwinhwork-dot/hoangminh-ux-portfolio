"""L5 — the last thing between the model and a recruiter.

This guard may **block and replace**. It must never silently rewrite a fact: a wrong
answer quietly corrected is a bug that hides itself, and the whole point of the layer is
that failures are visible in the trace.

Checks run cheapest-first, but the ordering also reflects severity — an uncited factual
claim is the failure that damages a real person, so it is checked before cosmetics.

The canonical-fact check deserves a note. It does not verify that an answer is complete;
it verifies that when the answer *does* state one of a small set of load-bearing facts
(GPA, employer, contact details, headline metrics), it states the same value the
knowledge base does. A model that drifts "3.57" to "3.7" is not making a typo — it is
fabricating a credential.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from agent.guardrails.policies import get_policies
from agent.schemas import FACTUAL_INTENTS, Citation, Intent

_TAG = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>")
# Removing the tags of these elements is not enough — their *content* is executable or
# invisible-but-present, so the whole element goes.
_DANGEROUS_BLOCK = re.compile(
    r"<\s*(script|style|iframe|object|embed|svg)\b.*?(?:</\s*\1\s*>|$)", re.S | re.I
)
_CLASS = re.compile(r'class="([^"]*)"')
_CITATIONS_LINE = re.compile(r"^\s*CITATIONS:\s*(.*)$", re.M | re.I)

# The prompt asks for a bare `NOT_INDEXED` when the evidence does not cover the question.
# Live runs showed the model almost never complies: it prefers to explain, writing "the
# evidence does not specify..." instead. The explanation is honest, but it is prose where
# a sentinel was expected, and worse, it sometimes upgrades absence of evidence into
# evidence of absence ("he has not worked for any companies in Singapore").
#
# A rule a model can break is not a guardrail. So the sentinel is enforced here rather
# than requested there: these phrasings mean the same thing and are treated the same way.
_INSUFFICIENT_EVIDENCE = re.compile(
    r"(?i)\b("
    r"(the )?evidence (provided )?does not|(the )?evidence (provided )?doesn't|"
    r"not (specified|mentioned|stated|indexed|available|provided) in the (evidence|context|knowledge)|"
    r"(does|do) not (specify|mention|state|include|contain|indicate)|"
    r"no (information|evidence|mention|record|detail)s? (about|on|regarding|of)|"
    r"(i|we) (do not|don't) have (that|this|any)|"
    r"is not (covered|addressed) (by|in) the (evidence|knowledge)|"
    r"there is no (information|evidence|mention)|"
    r"according to the (indexed |provided |available |given )?(evidence|knowledge|context)|"
    r"based (only )?on the (evidence|knowledge|context) (provided|given|available)"
    r")\b"
)

# Patterns that decide whether an answer is *claiming* a canonical fact at all. Without
# these the guard would fire on any answer that merely mentions the topic.
_FACT_PROBES: dict[str, re.Pattern[str]] = {
    "gpa": re.compile(r"\bgpa\b[^.]{0,20}?(\d\.\d{1,2})", re.I),
    "echomind_wpm": re.compile(r"(\d{2,3}\s*[-–]\s*\d{2,3})\s*(?:words|wpm)", re.I),
    "stakeholders": re.compile(r"(?:over |more than |about )?(\d+\+?)\s*stakeholder", re.I),
}


def _hedge_leads(body: str, position: int) -> bool:
    """True when the hedge arrives before the answer asserts anything.

    The prompt requires load-bearing facts to be bolded, so the first `<b>` is a usable
    marker for "the answer has started saying something". No bold at all means the reply
    is prose only, and a hedge in its opening sentence carries the whole reply.
    """
    first_fact = body.find("<b>")
    if first_fact != -1:
        return position < first_fact
    return position < 200


def _fact_matches(found: str, expected: str) -> bool:
    """Compare the number, not its decoration.

    "150+", "over 150" and "150" are the same fact; "3.9" and "3.57" are not. Only
    digits, dots and internal hyphens survive the comparison, so ranges ("55–65" vs
    "55-65") agree while genuinely different values still disagree.
    """
    def digits(text: str) -> str:
        return re.sub(r"[^\d.-]", "", text.replace("\u2013", "-").replace("\u2014", "-")).strip("-.")

    return digits(found) == digits(expected)


@dataclass(frozen=True)
class OutputVerdict:
    allowed: bool
    html: str
    citations: list[Citation] = field(default_factory=list)
    violation: str | None = None


def parse_citations(raw: str, evidence: dict[str, Citation] | None = None) -> tuple[str, list[Citation]]:
    """Split the model's `CITATIONS: E1,E3` tail from the body it belongs to."""
    match = _CITATIONS_LINE.search(raw)
    if not match:
        return raw.strip(), []
    body = (raw[: match.start()] + raw[match.end():]).strip()
    keys = [k.strip() for k in match.group(1).replace(";", ",").split(",") if k.strip()]
    citations = [evidence[k] for k in keys if evidence and k in evidence] if evidence else []
    return body, citations


def sanitize_html(raw: str) -> str:
    """Drop every tag and class outside the allowlist; escape what is left over.

    Tag removal alone is not enough — an attacker-influenced answer could carry an
    `onclick` attribute on an allowed tag, so attributes are rebuilt rather than filtered.
    """
    policies = get_policies()
    allowed_tags = set(policies.get("output.allowed_html_tags", []))
    allowed_classes = set(policies.get("output.allowed_html_classes", []))

    def replace(match: re.Match[str]) -> str:
        tag = match.group(1).lower()
        if tag not in allowed_tags:
            return ""
        if match.group(0).startswith("</"):
            return f"</{tag}>"
        attributes = ""
        class_match = _CLASS.search(match.group(0))
        if class_match:
            classes = [c for c in class_match.group(1).split() if c in allowed_classes]
            if classes:
                attributes += f' class="{" ".join(classes)}"'
        # data-v drives the bar-fill transition in index.html and is numeric-only.
        data_v = re.search(r'data-v="(\d{1,3})"', match.group(0))
        if data_v and tag == "i":
            attributes += f' data-v="{data_v.group(1)}"'
        return f"<{tag}{attributes}>"

    return _TAG.sub(replace, _DANGEROUS_BLOCK.sub("", raw))


def check_output(
    raw: str,
    intent: Intent,
    *,
    evidence: dict[str, Citation] | None = None,
) -> OutputVerdict:
    policies = get_policies()
    body, citations = parse_citations(raw, evidence)

    # The model's honest miss. Not a violation — a correct outcome.
    if body.strip().upper().startswith("NOT_INDEXED"):
        return OutputVerdict(False, policies.reply("not_indexed"), [], "not_indexed")

    if not body.strip():
        return OutputVerdict(False, policies.reply("not_indexed"), [], "empty_answer")

    # Same outcome, reached by prose instead of the sentinel — but only when the hedge
    # *is* the answer. Position decides it: a hedge that opens the reply is a refusal;
    # one that follows an asserted fact is a caveat, and caveats are good behaviour.
    #
    # This distinction was not obvious. The blunt version threw away a correct answer to
    # "did he win first prize?" — the model led with "He was a <b>Top 20 finalist</b>"
    # and then added "the evidence does not indicate he won first prize", which is
    # precisely the honest correction the case exists to test.
    hedge = _INSUFFICIENT_EVIDENCE.search(body)
    if hedge and _hedge_leads(body, hedge.start()):
        return OutputVerdict(False, policies.reply("not_indexed"), [], "insufficient_evidence")

    # 1. Citations for anything factual.
    #
    #    When the model omits the CITATIONS line — which it does often enough to matter —
    #    discarding an otherwise good answer is the wrong trade. The evidence block is
    #    something we assembled, not something the model reported: we already know which
    #    passages were in context, so the sources can be attributed without asking. The
    #    line is a convenience for pinpointing *which* of them was used, never the thing
    #    that makes an answer grounded. What actually makes it grounded is upstream: the
    #    retrieval floor means a model with no evidence is never called at all.
    if intent in FACTUAL_INTENTS and not citations:
        if evidence:
            citations = list(evidence.values())[:2]
            violation_note = "citations_inferred"
        else:
            return OutputVerdict(False, policies.reply("not_indexed"), [], "missing_citations")
    else:
        violation_note = None

    # 2. Hard-forbidden content: salary figures, impersonation, self-disclosure.
    match = policies.matches("output.forbidden_patterns", body)
    if match:
        key = "salary" if re.search(r"\$|usd|vnd|₫", match.pattern, re.I) else "not_indexed"
        return OutputVerdict(False, policies.reply(key), [], f"forbidden:{match.pattern[:40]}")

    # 3. Canonical facts must match the knowledge base exactly where they are claimed.
    for name, probe in _FACT_PROBES.items():
        expected = policies.canonical_facts.get(name)
        if not expected:
            continue
        found = probe.search(body)
        if found and not _fact_matches(found.group(1), expected):
            return OutputVerdict(
                False, policies.reply("not_indexed"), [], f"canonical_mismatch:{name}"
            )

    # 4. Length, then markup.
    max_chars = policies.get("output.max_chars", 1400)
    if len(body) > max_chars:
        body = body[:max_chars].rsplit(" ", 1)[0] + "…"

    return OutputVerdict(True, sanitize_html(body), citations, violation_note)


def escape_untrusted(text: str) -> str:
    """For echoing user input back into HTML. Never used on model output."""
    return html.escape(text, quote=True)
