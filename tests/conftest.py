"""Shared fixtures.

Design rule for this suite: only `answer_minh` needs a model. Everything else — routing,
retrieval, both guards, chart building, the API contract — is deterministic and must pass
with no API key set. If a test here needs a network call, the boundary is in the wrong
place.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def _no_network(request):
    """Unit tests must not call a provider.

    Once a real key is configured this suite would otherwise fire an embeddings request
    on every retrieval and a completion on every graph test: slow, billable and
    non-deterministic. Model behaviour belongs to `eval/run_eval.py`. What is under test
    here is the deterministic contract — routing, retrieval, guards, markup — which is
    most of the system by design.
    """
    import agent.rag.embed as embed
    from agent.services import llm

    saved = (embed.available, llm.enabled, llm.complete, llm.complete_json)
    embed.available = lambda: False
    llm.enabled = lambda: False
    llm.complete = lambda *a, **k: None
    llm.complete_json = lambda *a, **k: None
    yield
    embed.available, llm.enabled, llm.complete, llm.complete_json = saved


@pytest.fixture(scope="session")
def policies():
    from agent.guardrails.policies import get_policies

    return get_policies()


@pytest.fixture(scope="session")
def index():
    """The built knowledge index. Skips the suite if `scripts/ingest_kb.py` never ran."""
    from agent.config import KNOWLEDGE_INDEX

    if not (KNOWLEDGE_INDEX / "index.json").exists():
        pytest.skip("no index — run `python scripts/ingest_kb.py`")
    return KNOWLEDGE_INDEX


@pytest.fixture
def state():
    from agent.orchestrator.state import StudioState

    return StudioState(message="", session_id="test-session")
