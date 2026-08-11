"""L4 — the callable tool set must be closed and declared."""

import pytest

from agent.guardrails.tool_guard import ToolGuardError, assert_allowed


def test_allowlisted_tool_passes():
    assert_allowed("search_knowledge", {"query": "prd"}, 0)


def test_unlisted_tool_is_refused():
    with pytest.raises(ToolGuardError):
        assert_allowed("delete_everything", {}, 0)


def test_budget_is_enforced():
    with pytest.raises(ToolGuardError):
        assert_allowed("search_knowledge", {}, 99)


def test_non_object_arguments_are_refused():
    with pytest.raises(ToolGuardError):
        assert_allowed("search_knowledge", ["query"], 0)


def test_illegal_argument_names_are_refused():
    with pytest.raises(ToolGuardError):
        assert_allowed("search_knowledge", {"__class__": 1}, 0)
