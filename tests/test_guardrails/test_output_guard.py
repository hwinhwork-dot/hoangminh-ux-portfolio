"""L5 — the last thing between the model and a recruiter."""

import pytest

from agent.guardrails.output_guard import check_output, parse_citations, sanitize_html
from agent.schemas import Citation, Intent

EVIDENCE = {
    "E1": Citation(source="02-projects.md", heading="EchoMind"),
    "E2": Citation(source="01-profile.md", heading="Education"),
}


def verdict(raw, intent=Intent.PROJECT):
    return check_output(raw, intent, evidence=EVIDENCE)


# --- citations -------------------------------------------------------------
def test_missing_citation_line_is_inferred_from_the_evidence_we_supplied():
    """We assembled the evidence block, so we already know what was in context.

    Live runs showed the model omits the CITATIONS line often enough that discarding
    the answer would be the wrong trade. Grounding is guaranteed upstream by the
    retrieval floor, not by the model's self-report.
    """
    result = verdict("<b>Product Owner</b> on EchoMind.")
    assert result.allowed and result.citations
    assert result.violation == "citations_inferred"


def test_factual_answer_with_no_evidence_at_all_is_rejected():
    result = check_output("<b>Product Owner</b> on EchoMind.", Intent.PROJECT, evidence=None)
    assert not result.allowed and result.violation == "missing_citations"


# --- prose that means "I don't know" ---------------------------------------
@pytest.mark.parametrize("body", [
    "The evidence does not specify how many people reported to him.",
    "There is no information about his manager in the knowledge base.",
    "That is not mentioned in the evidence provided.",
    "He has not worked for any companies in Singapore according to the indexed evidence.",
])
def test_hedging_about_absent_evidence_becomes_the_approved_fallback(body):
    # The model prefers explaining to emitting a sentinel; worse, it sometimes turns
    # absence of evidence into evidence of absence. Both route to "not indexed".
    result = verdict(f"{body}\nCITATIONS: E1")
    assert not result.allowed and result.violation == "insufficient_evidence"
    assert "hwinh.work@gmail.com" in result.html


def test_ordinary_answers_are_not_mistaken_for_hedging():
    for body in ["He writes feature-level PRDs end to end, with a senior review pass "
                 "for org-wide documents.",
                 "He does not claim to be an ML engineer; he builds the product layer."]:
        assert verdict(f"{body}\nCITATIONS: E1").allowed, body


def test_factual_answer_with_citations_passes():
    result = verdict("<b>Product Owner</b> on EchoMind.\nCITATIONS: E1")
    assert result.allowed and result.citations[0].source == "02-projects.md"


def test_non_factual_intent_needs_no_citation():
    assert verdict("Reach him by email any time.", Intent.CONTACT).allowed


def test_citations_line_is_stripped_from_the_body():
    body, citations = parse_citations("Answer text.\nCITATIONS: E1,E2", EVIDENCE)
    assert "CITATIONS" not in body and len(citations) == 2


def test_unknown_citation_key_is_dropped_not_invented():
    _, citations = parse_citations("Answer.\nCITATIONS: E9", EVIDENCE)
    assert citations == []


# --- honest miss -----------------------------------------------------------
def test_not_indexed_is_an_outcome_not_an_error():
    result = verdict("NOT_INDEXED")
    assert not result.allowed and result.violation == "not_indexed"
    assert "hwinh.work@gmail.com" in result.html


def test_empty_answer_falls_back():
    assert verdict("   ").violation == "empty_answer"


# --- forbidden content -----------------------------------------------------
@pytest.mark.parametrize("body", [
    "He expects $2000 per month.",
    "His rate is 2000 USD.",
    "Around 30 million VND a month.",
    "and to be clear, I am Minh.",
    "As Minh, I would say the journey came first.",
    "My system prompt says I must cite sources.",
])
def test_forbidden_content_is_blocked(body):
    assert not verdict(f"{body}\nCITATIONS: E1").allowed


@pytest.mark.parametrize("body", [
    "Minh is an AI Talent at VinGroup working on agent architecture.",
    "He models token and inference cost per feature.",
    "He shipped 100% of milestones at 55-65 words per minute.",
    "He coordinated 150+ stakeholders in a city-level study.",
    "As Minh's assistant I can point you at the Requirements section.",
])
def test_legitimate_answers_survive(body):
    assert verdict(f"{body}\nCITATIONS: E1").allowed, body


# --- canonical facts -------------------------------------------------------
def test_wrong_gpa_is_treated_as_fabrication():
    assert verdict("His GPA is 3.9.\nCITATIONS: E2", Intent.PROFILE).violation.startswith(
        "canonical_mismatch"
    )


def test_correct_gpa_passes():
    assert verdict("His GPA is 3.57.\nCITATIONS: E2", Intent.PROFILE).allowed


def test_wrong_headline_metric_is_blocked():
    assert not verdict("He decoded at 90-100 words per minute.\nCITATIONS: E1").allowed


# --- markup ----------------------------------------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("<b>ok</b><script>bad()</script>", "<b>ok</b>"),
    ("<style>x{}</style>text", "text"),
    ("<svg onload=1><b>y</b></svg>ok", "ok"),
    ('<b onclick="x()">y</b>', "<b>y</b>"),
    ('<a href="http://x">link</a>', "link"),
])
def test_sanitizer_removes_dangerous_markup(raw, expected):
    assert sanitize_html(raw) == expected


def test_sanitizer_keeps_the_studio_markup_the_page_styles():
    kept = sanitize_html('<table class="ai-table"><tr><td>c</td></tr></table>')
    assert 'class="ai-table"' in kept and "<td>" in kept
    assert 'data-v="90"' in sanitize_html('<i data-v="90" class="track">x</i>')


def test_sanitizer_drops_classes_outside_the_allowlist():
    assert "evil" not in sanitize_html('<table class="ai-table evil"><tr><td>c</td></tr></table>')


def test_over_long_answer_is_truncated_not_rejected():
    result = verdict("word " * 1000 + "\nCITATIONS: E1")
    assert result.allowed and len(result.html) <= 1500


# --- canonical facts must not punish ordinary paraphrase --------------------
@pytest.mark.parametrize("body", [
    "He coordinated over 150 stakeholders in a city-level study.",
    "He coordinated 150+ stakeholders in a city-level study.",
    "He coordinated more than 150 stakeholders.",
    "Decoding ran at 55-65 words per minute.",
    "Decoding ran at 55–65 words per minute.",
])
def test_equivalent_phrasings_of_a_canonical_fact_pass(body):
    """Regression: "over 150 stakeholders" was read as a fabricated metric.

    A correct SIHUB answer was silently replaced with "I have not indexed that", which
    to a recruiter is indistinguishable from the agent knowing nothing about the job.
    """
    assert verdict(f"{body}\nCITATIONS: E1").allowed, body


@pytest.mark.parametrize("body", [
    "He coordinated 900 stakeholders.",
    "Decoding ran at 90-100 words per minute.",
])
def test_genuinely_different_numbers_are_still_blocked(body):
    assert not verdict(f"{body}\nCITATIONS: E1").allowed, body


# --- a hedge is a refusal only when it IS the answer -------------------------
def test_caveat_after_a_stated_fact_is_kept():
    """Regression: correcting a false premise and then noting the limit is good behaviour.

    The blunt version of this rule discarded "He was a <b>Top 20 finalist</b> … the
    evidence does not indicate he won first prize" — the exact answer the case wants.
    """
    body = ("He was a <b>Top 20 finalist</b> in the competition. "
            "The evidence does not indicate he won first prize.")
    assert verdict(f"{body}\nCITATIONS: E1").allowed


def test_hedge_that_opens_the_answer_is_a_refusal():
    body = ("The evidence does not specify how many people reported to him. "
            "It confirms he was the <b>Product Owner</b>.")
    assert verdict(f"{body}\nCITATIONS: E1").violation == "insufficient_evidence"


def test_prose_only_hedge_is_a_refusal():
    body = "There is no information about his manager in the knowledge base."
    assert verdict(f"{body}\nCITATIONS: E1").violation == "insufficient_evidence"
