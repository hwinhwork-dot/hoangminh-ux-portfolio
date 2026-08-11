"""Routing — deterministic rules before any model call."""

import pytest

from agent.orchestrator.router import route
from agent.schemas import Intent


@pytest.mark.parametrize("message,intent", [
    ("Tell me about the VinFast test-drive assistant", Intent.PROJECT),
    ("Tell me about EchoMind", Intent.PROJECT),
    ("What did he do at SIHUB?", Intent.PROJECT),
    ("What is Minh doing right now?", Intent.PROFILE),
    ("hiện tại Minh đang làm ở đâu?", Intent.PROFILE),
    ("Does he actually know RAG?", Intent.AI_PRODUCT),
    ("How does he think about AI safety and guardrails?", Intent.AI_PRODUCT),
    ("Has he built multi-agent systems?", Intent.AI_PRODUCT),
    ("Which level of PRD can Minh write?", Intent.ARTIFACT),
    ("How does he run UAT?", Intent.ARTIFACT),
    ("Compare his projects", Intent.COMPARISON),
    ("Show me a chart of his skills", Intent.METRIC),
    ("How do I contact him?", Intent.CONTACT),
    ("When can he start?", Intent.LOGISTICS),
    ("hi", Intent.SMALLTALK),
])
def test_rules_route_without_a_model(message, intent):
    result = route(message)
    assert result is not None, f"{message!r} fell through to the model"
    assert result[0] == intent


def test_specific_rules_beat_generic_ones():
    # "the VinFast AI assistant" must be a project question, not a capability question.
    assert route("tell me about the VinFast AI assistant")[0] == Intent.PROJECT


@pytest.mark.parametrize("message", ["Compare his projects", "Show me a chart of his skills",
                                     "kinh nghiệm làm việc"])
def test_chart_intents_request_a_chart(message):
    assert route(message)[2] is True


def test_prose_intents_do_not_request_a_chart():
    assert route("Which level of PRD can Minh write?")[2] is False


def test_unmatched_message_defers_to_the_model():
    assert route("zxcv qwerty asdf") is None


def test_query_is_expanded_with_knowledge_base_vocabulary():
    _, query, _ = route("Does he know RAG?")
    assert "chunking" in query and "Does he know RAG?" in query
