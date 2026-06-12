"""workspace_read handler — first real M4 handler wired to the idempotent cache.

Reads a file (or any content) from the workspace. The actual I/O is provided
by a *content_resolver* callable injected at construction time so that:
  - keel itself has zero filesystem / platform dependency
  - tests inject a fake resolver
  - RSO injects the real workspace reader

The result is cached by content-hash so that on LangGraph checkpoint resume
(crash recovery) the expensive step is NOT repeated — LLM/IO cost is zero.
"""

from __future__ import annotations

from typing import Any, Callable

from keel.compiler.state import KeelState
from keel.persistence.cache import ContentHashCache

# Signature: (node_id, inputs) → result dict
ContentResolver = Callable[[str, dict[str, Any]], dict[str, Any]]


class WorkspaceReadHandler:
    """Handler for NodeKind == 'workspace_read'.

    Args:
        node_id:          The IR node id this handler is bound to.
        cache:            Idempotent cache — same inputs → same result, no re-run.
        content_resolver: Injected function that performs the actual I/O.
                          Signature: (node_id, inputs) -> result_dict.
                          keel never calls platform code directly.
    """

    def __init__(
        self,
        node_id: str,
        cache: ContentHashCache,
        content_resolver: ContentResolver,
    ) -> None:
        self._node_id = node_id
        self._cache = cache
        self._resolver = content_resolver

    def __call__(self, state: KeelState) -> KeelState:
        inputs = dict(state.get("node_outputs", {}).get(self._node_id + "_inputs") or {})
        # Use the full state inputs for cache keying so cache is IR-specific.
        cache_inputs = {"node_id": self._node_id, "inputs": inputs}

        result, _was_cached = self._cache.get_or_run(
            cache_inputs,
            lambda: self._resolver(self._node_id, inputs),
        )

        current_outputs = dict(state.get("node_outputs") or {})
        current_outputs[self._node_id] = result

        return {**state, "node_outputs": current_outputs}
