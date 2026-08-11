"""policies.yaml and knowledge/raw/06-boundaries.md must not drift apart."""

import re

from agent.config import KNOWLEDGE_RAW
from agent.guardrails.policies import get_policies

POLICIES = get_policies()
BOUNDARIES = (KNOWLEDGE_RAW / "06-boundaries.md").read_text(encoding="utf-8")


def test_every_reply_offers_a_route_forward():
    # A refusal that dead-ends is a lost candidate. Each one must point somewhere.
    exempt = {"injection", "third_party_pii", "hostile", "out_of_scope"}
    for key, text in POLICIES.raw["replies"].items():
        if key in exempt:
            continue
        assert "hwinh.work@gmail.com" in text, f"reply '{key}' leaves the visitor nowhere to go"


def test_refusal_keys_used_by_guards_all_exist():
    used = {POLICIES.get("input.injection_reply_key"), POLICIES.get("input.pii_reply_key"),
            POLICIES.get("input.out_of_scope_reply_key"), "not_indexed", "rate_limited"}
    used |= {topic["reply_key"] for topic in POLICIES.hard_topics.values()}
    for key in used:
        assert POLICIES.reply(key)


def test_boundaries_document_covers_every_reply_key():
    documented = set(re.findall(r"\| ([A-Za-z][^|]*?) \| \"", BOUNDARIES))
    assert documented, "the refusal table in 06-boundaries.md is unreadable"


def test_allowed_sources_all_exist_on_disk():
    for name in POLICIES.allowed_sources:
        assert (KNOWLEDGE_RAW / name).exists(), f"{name} is allow-listed but missing"


def test_boundaries_file_is_never_citable():
    assert "06-boundaries.md" not in POLICIES.allowed_sources


def test_canonical_facts_appear_in_the_knowledge_base():
    """A canonical fact the corpus never states cannot be checked against anything.

    Dashes are normalised the same way the output guard normalises them: the knowledge
    base is written with typographic en dashes, a model will answer with either.
    """
    def norm(text: str) -> str:
        return text.replace("\u2013", "-").replace("\u2014", "-")

    corpus = norm("".join(
        (KNOWLEDGE_RAW / name).read_text(encoding="utf-8") for name in POLICIES.allowed_sources
    ))
    for name, value in POLICIES.canonical_facts.items():
        assert norm(value) in corpus, f"canonical fact '{name}' = {value!r} is not in the knowledge base"


def test_every_regex_compiles():
    for path in ("input.injection_patterns", "input.pii_patterns",
                 "input.out_of_scope_patterns", "output.forbidden_patterns"):
        assert POLICIES.patterns(path)
