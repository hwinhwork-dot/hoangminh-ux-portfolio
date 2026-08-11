"""Load and compile `policies.yaml` once per cold start.

`policies.yaml` is the machine-readable mirror of `knowledge/raw/06-boundaries.md`. If
the two drift, the YAML wins at runtime and the markdown is the bug — but the drift
itself is a defect, which is why `tests/test_guardrails/test_policy_sync.py` asserts
that every refusal case documented in the markdown has a reply key here.

Regexes are compiled eagerly at import: a malformed pattern should break the deploy, not
the first request that happens to reach it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import yaml

from agent.config import POLICIES_PATH


@dataclass(frozen=True)
class Policies:
    raw: dict[str, Any]
    _compiled: dict[str, list[re.Pattern[str]]] = field(default_factory=dict, repr=False)

    # ---------------- lookup ----------------
    def get(self, path: str, default: Any = None) -> Any:
        """Dotted lookup: `get("input.max_chars")`."""
        node: Any = self.raw
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def reply(self, key: str) -> str:
        """Approved wording for a refusal. A missing key is a bug, so it raises."""
        replies = self.raw.get("replies", {})
        if key not in replies:
            raise KeyError(f"no approved reply for '{key}' — add it to policies.yaml")
        return " ".join(replies[key].split())

    def patterns(self, path: str) -> list[re.Pattern[str]]:
        """Compiled regexes for a dotted path, compiled once and cached."""
        if path not in self._compiled:
            raw = self.get(path) or []
            self._compiled[path] = [re.compile(p) for p in raw]
        return self._compiled[path]

    def matches(self, path: str, text: str) -> re.Pattern[str] | None:
        for pattern in self.patterns(path):
            if pattern.search(text):
                return pattern
        return None

    # ---------------- convenience ----------------
    @property
    def hard_topics(self) -> dict[str, dict[str, Any]]:
        return self.get("input.hard_topics", {})

    @property
    def allowed_sources(self) -> list[str]:
        return self.get("retrieval.allowed_sources", [])

    @property
    def canonical_facts(self) -> dict[str, str]:
        return self.get("output.canonical_facts", {})


@lru_cache(maxsize=1)
def get_policies() -> Policies:
    raw = yaml.safe_load(POLICIES_PATH.read_text(encoding="utf-8"))
    policies = Policies(raw=raw)

    # Fail at import rather than mid-request on a bad pattern.
    for path in (
        "input.injection_patterns",
        "input.pii_patterns",
        "input.out_of_scope_patterns",
        "output.forbidden_patterns",
    ):
        policies.patterns(path)
    for topic in policies.hard_topics.values():
        for pattern in topic.get("patterns", []):
            re.compile(pattern)

    return policies
