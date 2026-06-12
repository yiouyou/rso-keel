"""M4 persistence tests.

Key assertion: after crash + resume, expensive work (LLM/IO) is NOT repeated.
Verified by counting resolver call_count — must be 1 across two invocations
of the same graph on the same thread_id.
"""

from __future__ import annotations

from typing import Any

import pytest

from keel.compiler.compiler import compile as keel_compile
from keel.compiler.state import KeelState
from keel.handlers.workspace_read import WorkspaceReadHandler
from keel.ir.schema import WorkflowIR
from keel.persistence.cache import (
    CacheBackend,
    ContentHashCache,
    InMemoryCache,
    _cache_key,
)
from keel.persistence.checkpointer import make_checkpointer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ir(**overrides) -> WorkflowIR:
    base: dict = {
        "schema_version": "v1",
        "objective": "Test",
        "nodes": [{"id": "r1", "kind": "workspace_read"}],
        "policies": {"max_cost_usd": 10.0, "allowed_skills": []},
    }
    base.update(overrides)
    return WorkflowIR.model_validate(base)


def _make_resolver(call_log: list[str]):
    """Return a resolver that records calls and returns a fixed result."""
    def resolver(node_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        call_log.append(node_id)
        return {"content": f"data-from-{node_id}", "status": "ok"}
    return resolver


# ---------------------------------------------------------------------------
# InMemoryCache / CacheBackend
# ---------------------------------------------------------------------------


def test_in_memory_cache_get_miss() -> None:
    cache = InMemoryCache()
    assert cache.get("nonexistent") is None


def test_in_memory_cache_set_get() -> None:
    cache = InMemoryCache()
    cache.set("k1", {"v": 1})
    assert cache.get("k1") == {"v": 1}


def test_in_memory_cache_satisfies_protocol() -> None:
    assert isinstance(InMemoryCache(), CacheBackend)


def test_cache_key_deterministic() -> None:
    k1 = _cache_key({"b": 2, "a": 1})
    k2 = _cache_key({"a": 1, "b": 2})
    assert k1 == k2  # key order must not matter


def test_cache_key_differs_for_different_inputs() -> None:
    k1 = _cache_key({"a": 1})
    k2 = _cache_key({"a": 2})
    assert k1 != k2


# ---------------------------------------------------------------------------
# ContentHashCache.get_or_run
# ---------------------------------------------------------------------------


def test_get_or_run_calls_fn_on_miss() -> None:
    called = []
    cache = ContentHashCache(InMemoryCache())
    result, was_cached = cache.get_or_run({"x": 1}, lambda: (called.append(1) or {"y": 2}))
    assert result == {"y": 2}
    assert was_cached is False
    assert len(called) == 1


def test_get_or_run_skips_fn_on_hit() -> None:
    called = []
    cache = ContentHashCache(InMemoryCache())
    cache.get_or_run({"x": 1}, lambda: {"y": 2})
    result, was_cached = cache.get_or_run({"x": 1}, lambda: (called.append(1) or {"y": 99}))
    assert result == {"y": 2}  # original cached value
    assert was_cached is True
    assert len(called) == 0   # fn was NOT called


def test_get_or_run_different_inputs_call_fn_separately() -> None:
    cache = ContentHashCache(InMemoryCache())
    r1, _ = cache.get_or_run({"x": 1}, lambda: {"v": "a"})
    r2, _ = cache.get_or_run({"x": 2}, lambda: {"v": "b"})
    assert r1 == {"v": "a"}
    assert r2 == {"v": "b"}


# ---------------------------------------------------------------------------
# make_checkpointer
# ---------------------------------------------------------------------------


def test_make_checkpointer_returns_memory_saver_by_default() -> None:
    from langgraph.checkpoint.memory import MemorySaver
    cp = make_checkpointer()
    assert isinstance(cp, MemorySaver)


def test_make_checkpointer_raises_on_bad_postgres_url() -> None:
    with pytest.raises((RuntimeError, Exception)):
        cp = make_checkpointer("postgresql://bad:bad@localhost:9999/nonexistent")
        # Some implementations raise only on first use
        cp.get({"configurable": {"thread_id": "x"}}, None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# WorkspaceReadHandler
# ---------------------------------------------------------------------------


def test_workspace_read_handler_calls_resolver() -> None:
    calls: list[str] = []
    cache = ContentHashCache(InMemoryCache())
    handler = WorkspaceReadHandler("r1", cache, _make_resolver(calls))

    state: KeelState = {"node_outputs": {}}
    result = handler(state)

    assert calls == ["r1"]
    assert result["node_outputs"]["r1"]["status"] == "ok"


def test_workspace_read_handler_cache_hit_no_resolver_call() -> None:
    calls: list[str] = []
    cache = ContentHashCache(InMemoryCache())
    handler = WorkspaceReadHandler("r1", cache, _make_resolver(calls))

    state: KeelState = {"node_outputs": {}}
    handler(state)   # first call — populates cache
    handler(state)   # second call — same inputs → cache hit

    assert len(calls) == 1  # resolver called exactly once


# ---------------------------------------------------------------------------
# CRASH RECOVERY — the central M4 assertion
#
# Scenario:
#   1. Compile graph with MemorySaver checkpointer.
#   2. Invoke on thread_id "run-1" → resolver called once, result checkpointed.
#   3. "Crash": discard the compiled graph object entirely.
#   4. Recompile same IR with SAME checkpointer + SAME cache.
#   5. Invoke on thread_id "run-1" → LangGraph restores from checkpoint.
#   6. Resolver call_count must still be 1 (zero additional LLM/IO cost).
# ---------------------------------------------------------------------------


def test_crash_recovery_zero_repeat_cost() -> None:
    calls: list[str] = []
    cache = ContentHashCache(InMemoryCache())
    checkpointer = make_checkpointer()  # MemorySaver

    thread_cfg = {"configurable": {"thread_id": "run-1"}}
    initial_state: KeelState = {"node_outputs": {}}

    # --- First run (normal execution) ---
    handler_v1 = WorkspaceReadHandler("r1", cache, _make_resolver(calls))
    compiled_v1 = keel_compile(_ir(), node_handlers={"r1": handler_v1}, checkpointer=checkpointer)
    result1 = compiled_v1.invoke(initial_state, config=thread_cfg)

    assert calls == ["r1"], "Resolver must be called exactly once on first run"
    assert result1["node_outputs"]["r1"]["status"] == "ok"

    # --- Simulate crash: drop compiled graph, rebuild from scratch ---
    del compiled_v1

    handler_v2 = WorkspaceReadHandler("r1", cache, _make_resolver(calls))
    compiled_v2 = keel_compile(_ir(), node_handlers={"r1": handler_v2}, checkpointer=checkpointer)

    # Resume: LangGraph will replay from checkpoint; cache prevents re-calling resolver
    result2 = compiled_v2.invoke(initial_state, config=thread_cfg)

    assert len(calls) == 1, (
        f"Resolver was called {len(calls)} times — expected 1. "
        "Cache must absorb the repeated invocation so LLM/IO cost is zero."
    )
    assert result2["node_outputs"]["r1"]["status"] == "ok"


def test_different_thread_ids_run_independently() -> None:
    calls: list[str] = []
    cache = ContentHashCache(InMemoryCache())
    checkpointer = make_checkpointer()

    initial: KeelState = {"node_outputs": {}}
    handler_a = WorkspaceReadHandler("r1", cache, _make_resolver(calls))
    keel_compile(_ir(), node_handlers={"r1": handler_a}, checkpointer=checkpointer).invoke(
        initial, config={"configurable": {"thread_id": "thread-A"}}
    )
    # Different thread but same inputs → cache hit → resolver still called only once total
    handler_b = WorkspaceReadHandler("r1", cache, _make_resolver(calls))
    keel_compile(_ir(), node_handlers={"r1": handler_b}, checkpointer=checkpointer).invoke(
        initial, config={"configurable": {"thread_id": "thread-B"}}
    )

    assert len(calls) == 1, "Same inputs across threads must share cache — one resolver call total"
