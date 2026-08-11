"""Rule-first intent routing.

Deterministic patterns run before any model call: they are free, instant, and testable.
The Hana prompt is consulted only when no rule fires, which keeps cost proportional to
genuine ambiguity — and keeps the studio working with no key at all.

Order matters and mirrors the discipline of the offline table in `index.html`: specific
before generic, first match wins. A rule for "the VinFast assistant" must precede the
generic "AI" rule, or every project question becomes a capability question.
"""

from __future__ import annotations

import re

from agent.schemas import Intent

# (pattern, intent, extra retrieval vocabulary, needs_chart)
RULES: list[tuple[str, Intent, str, bool]] = [
    (r"vinfast|vivi|test.?drive|booking assistant|p-?053",
     Intent.PROJECT, "VinFast ViVi test drive assistant Product Owner UI UX LangGraph guarded tools", False),
    (r"vingroup|vin group|ai talent|current(ly)? (work|role|job)|right now|doing now|hi[eệ]n t[aạ]i",
     Intent.PROFILE, "VinGroup AI Talent current role AI product management", False),
    (r"echomind|brain.?to.?text",
     Intent.PROJECT, "EchoMind brain to text Product Owner Transformer milestones WPM latency", False),
    (r"competition|first prize|award|finalist|top 20|won\b|win\b",
     Intent.PROJECT, "E-Reader competition Top 20 finalist HCMC People's Committee result", False),
    (r"e-?reader|digital education",
     Intent.PROJECT, "E-Reader digital education ecosystem Product Lead HCI activation Top 20", False),
    (r"sihub|innovation hub",
     Intent.PROJECT, "SIHUB PM Executive stakeholders NPS Board reporting experiments", False),
    (r"\brag\b|retrieval|vector|embedding|chunk|hallucinat|grounding",
     Intent.AI_PRODUCT, "RAG retrieval chunking embeddings hybrid search reranking confidence floor", False),
    (r"guardrail|jailbreak|injection|red.?team|responsible ai|ai safety|hitl|human.in.the.loop",
     Intent.AI_PRODUCT, "guardrails AI safety red teaming human in the loop escalation input output guard", False),
    (r"\beval|golden set|benchmark|test.*(ai|agent)",
     Intent.AI_PRODUCT, "evaluation golden set release gate accuracy versioned runs", False),
    (r"multi.?agent|orchestrat|langgraph|\bmcp\b|\ba2a\b|react pattern|supervisor",
     Intent.AI_PRODUCT, "multi-agent orchestration supervisor ReAct tool design agent architecture", False),
    (r"uncertain|trust|confidence|explainab|transparen|ux for ai|design(ing)?\s+(\w+\s+){0,2}for\s+(an?\s+)?ai",
     Intent.AI_PRODUCT, "designing for uncertainty confidence provenance citations graceful unknown reversibility", False),
    (r"ai product|product.market fit|\bpmf\b|\broi\b|token cost|ai strateg",
     Intent.AI_PRODUCT, "AI product management strategy PMF ROI cost per feature roadmap", False),
    (r"skill|chart|strength|how (strong|good)|rate (him|his)|k[yỹ] n[aă]ng",
     Intent.METRIC, "skills self-assessed levels research journey stories prototyping", True),
    (r"is (he|minh) technical|can (he|minh) (code|program|build)|coding|programming|developer|software engineer",
     Intent.PROFILE, "technical Python builds agents specs engineering HCI not an engineer", False),
    (r"\bprd\b|product requirement|\bbrd\b|business requirement",
     Intent.ARTIFACT, "PRD BRD feature level scope goals acceptance criteria traceability", False),
    (r"user stor|acceptance criteria|gherkin|given.?when.?then",
     Intent.ARTIFACT, "user stories acceptance criteria Gherkin INVEST MoSCoW", False),
    (r"\buat\b|acceptance test|release gate|traceab",
     Intent.ARTIFACT, "UAT acceptance testing defects release gate traceability matrix", False),
    (r"figma|wireframe|prototyp|lo-?fi|hi-?fi|mockup",
     Intent.ARTIFACT, "Figma wireframe lo-fi hi-fi prototype fidelity", False),
    (r"journey|persona|problem tree|value proposition|\bvpc\b",
     Intent.ARTIFACT, "journey map problem tree value proposition canvas fit pairs", False),
    (r"research|interview|survey|usability|a/?b test|discovery",
     Intent.ARTIFACT, "user research interviews surveys usability think aloud A/B interleaving", False),
    (r"\bhci\b|heuristic|cognitive load|usability principle",
     Intent.ARTIFACT, "HCI cognitive load recognition feedback consistency error prevention", False),
    (r"agile|scrum|sprint|kanban|raci|backlog",
     Intent.ARTIFACT, "Agile Scrum sprints RACI backlog MoSCoW change log", False),
    (r"compar|side by side|versus|\bvs\b|table",
     Intent.COMPARISON, "projects roles focus results comparison", True),
    (r"experience|timeline|career|work history|kinh nghi[eệ]m",
     Intent.COMPARISON, "timeline experience roles UEH SIHUB EchoMind E-Reader VinGroup", True),
    (r"education|gpa|university|ueh|degree|certificat",
     Intent.PROFILE, "UEH bachelor technology innovation GPA coursework certifications", False),
    (r"weakness|biggest flaw|improve",
     Intent.PROFILE, "weakness research deeply timebox lo-fi tests", False),
    (r"why (should|hire)|stand ?out|what makes.*(different|unique)",
     Intent.PROFILE, "strengths reasons to hire evidence end to end research delivery AI", False),
    (r"team|collaborat|stakeholder|communicat|conflict|leader|ownership",
     Intent.PROFILE, "collaboration stakeholders Board reporting leadership ownership conflict evidence", False),
    (r"metric|\bkpi\b|\bnps\b|retention|activation|measure success",
     Intent.ARTIFACT, "metrics activation retention task success NPS thresholds acceptance criteria", False),
    (r"contact|email|phone|reach|get in touch|touch base|hire (him|her|them)|\bcv\b|resume|liên hệ|lien he",
     Intent.CONTACT, "contact email phone open to roles", False),
    (r"available|start date|when can.*(start|join)|notice period|relocat|remote|onsite|hybrid|based in",
     Intent.LOGISTICS, "availability start date location onsite hybrid Ho Chi Minh City", False),
    (r"^\s*(hi|hello|hey|yo|xin ch[aà]o|ch[aà]o)\b|what can you (do|help)",
     Intent.SMALLTALK, "", False),
    (r"english|language|vietnamese",
     Intent.PROFILE, "English professional working level Vietnamese native documentation", False),
    (r"intro|who is|about (minh|him)|tell me about (minh|him)|gi[oớ]i thi[eệ]u|l[aà] ai",
     Intent.PROFILE, "introduction UX research product discovery AI product highlights", False),
]

_COMPILED = [(re.compile(p, re.I), intent, extra, chart) for p, intent, extra, chart in RULES]


def route(message: str) -> tuple[Intent, str, bool] | None:
    """Return `(intent, retrieval_query, needs_chart)`, or None when no rule is confident.

    None means "ask the model", never "give up".
    """
    for pattern, intent, extra, chart in _COMPILED:
        if pattern.search(message):
            return intent, expand_query(message, extra), chart
    return None


def expand_query(message: str, extra: str = "") -> str:
    """Append the knowledge base's own vocabulary to the visitor's wording.

    Retrieval is lexical-first, so a question phrased in the recruiter's words and a
    passage written in Minh's words may share almost no tokens. The rule table carries
    the bridge.
    """
    return f"{message} {extra}".strip()
