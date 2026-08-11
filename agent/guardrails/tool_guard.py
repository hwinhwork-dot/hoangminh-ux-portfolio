"""L4 — allowlist, argument validation and call budget for tool invocations.

Small on purpose. The reason this layer exists is not that the tools are dangerous — two
of the three are pure functions — but that the *set* of callable tools must be a closed,
declared list rather than whatever the model decides to name. A model that can invent a
tool name can eventually be talked into inventing one that exists.
"""

from __future__ import annotations

from agent.guardrails.policies import get_policies


class ToolGuardError(RuntimeError):
    """A tool call violated policy. Never surfaced to the visitor verbatim."""


def assert_allowed(tool_name: str, args: dict, calls_so_far: int = 0) -> None:
    policies = get_policies()
    allowlist = policies.get("tools.allowlist", [])
    budget = policies.get("tools.max_calls_per_turn", 4)

    if tool_name not in allowlist:
        raise ToolGuardError(f"tool '{tool_name}' is not on the allowlist")
    if calls_so_far >= budget:
        raise ToolGuardError(f"tool call budget of {budget} exhausted")
    if not isinstance(args, dict):
        raise ToolGuardError("tool arguments must be an object")
    for key in args:
        if not isinstance(key, str) or not key.isidentifier() or key.startswith("_"):
            raise ToolGuardError(f"illegal argument name: {key!r}")
