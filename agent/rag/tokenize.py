"""One tokenizer, used by both the index builder and the query path.

If these two ever drift apart, retrieval silently degrades and nothing errors — so they
share this module rather than each having their own `.split()`.

Vietnamese matters here: a recruiter may type "kinh nghiệm" while the English knowledge
base says "experience". We cannot fix that with tokenization, but we can make sure
"kinh nghiem" and "kinh nghiệm" hit the same token, so the accent-free spelling people
actually type still matches.
"""

from __future__ import annotations

import re
import unicodedata

_WORD = re.compile(r"[a-z0-9]+(?:[-'./][a-z0-9]+)*", re.UNICODE)

# Dropped from the index: they carry no retrieval signal and inflate document length,
# which pushes BM25 scores down for the chunks that actually answer the question.
STOPWORDS = frozenset("""
a an the and or but if then than that this these those of in on at to for from with
without by as is are was were be been being do does did doing have has had having
i you he she it we they his her their its my your our me him them us
what which who whom whose when where why how can could should would will shall may might
must not no nor so such about into over under again further once here there all any both
each few more most other some only own same too very just also
""".split())

# Never dropped even though they are short or stopword-ish: they are how a recruiter
# names the thing they want.
KEEP = frozenset({"ai", "ux", "ui", "po", "pm", "qa", "rag", "prd", "brd", "uat", "rtm",
                  "hci", "nps", "gpa", "roi", "pmf", "a2a", "mcp", "llm", "b2b", "kpi"})


def fold(text: str) -> str:
    """Strip Vietnamese diacritics so 'kinh nghiệm' and 'kinh nghiem' agree.

    `đ` has no combining form, so it is mapped explicitly — without that line, every
    Vietnamese word containing it would fold to a different token than its typed
    equivalent.
    """
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


IRREGULAR = {
    "analyses": "analysis", "bases": "basis", "criteria": "criterion",
    "matrices": "matrix", "indices": "index", "hypotheses": "hypothesis",
}


def stem(token: str) -> str:
    """Deliberately crude suffix stripping.

    Linguistic correctness is not the goal — agreement is. The index and the query path
    call this same function, so "analysis" collapsing to "analysi" is harmless as long as
    it collapses identically on both sides. What matters is that a recruiter typing
    "wireframe" reaches a chunk that says "wireframes", and that British and American
    spellings ("prioritisation" / "prioritization") land on one token.

    Anything shorter than five characters is left alone: over-stemming short words
    collides unrelated terms, and short words carry little retrieval signal anyway.
    """
    if token in KEEP or len(token) < 5:
        return token
    token = IRREGULAR.get(token, token)

    # British -> American first, so the suffix steps below see a single spelling.
    for british, american in (("isation", "ization"), ("ising", "izing"), ("ise", "ize")):
        if token.endswith(british):
            token = token[: -len(british)] + american
            break

    # Step 1 — plural. Must run before the verb step: "embeddings" is a plural of a
    # gerund, and stripping only one suffix leaves it disagreeing with "embedding".
    if token.endswith("ies") and len(token) > 5:
        token = token[:-3] + "y"
    elif token.endswith("s") and not token.endswith("ss") and len(token) > 4:
        token = token[:-1]

    # Step 2 — verb form.
    if token.endswith("ing") and len(token) > 6:
        token = token[:-3]
    elif token.endswith("ed") and len(token) > 5:
        token = token[:-2]

    # Step 2b — nominalisation, so "evaluation" meets "evaluate" and
    # "communication" meets "communicate".
    if token.endswith("ation") and len(token) > 6:
        token = token[:-3]
        if token.endswith("izat"):
            token = token[:-2]

    # Step 3 — collapse the silent trailing 'e', so "wireframe" and "wireframes"
    # (which step 1 left as "wireframe" and "wireframe") converge with "wirefram"
    # produced from other inflections.
    if token.endswith("e") and len(token) > 4:
        token = token[:-1]

    return token


def tokens(text: str, *, drop_stopwords: bool = True) -> list[str]:
    """Lowercase, accent-fold, stem, and split into retrievable terms."""
    out: list[str] = []
    for match in _WORD.finditer(fold(text.lower())):
        token = match.group(0)
        if token in KEEP:
            out.append(token)
            continue
        if drop_stopwords and token in STOPWORDS:
            continue
        if len(token) == 1 and not token.isdigit():
            continue
        out.append(stem(token))
    return out


def content_terms(query: str) -> list[str]:
    """Distinct query terms, order preserved — the basis of the confidence score."""
    seen: set[str] = set()
    out: list[str] = []
    for token in tokens(query):
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out
