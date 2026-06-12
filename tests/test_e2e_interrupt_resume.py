"""End-to-end integration tests for the compile → run → interrupt → resume cycle.

These tests exercise the *real* LangGraph runtime with a MemorySaver checkpointer
and the real HumanGate, confirming that:

  1. A graph without human_approval runs to completion in one invoke.
  2. A graph with human_approval suspends at the gate (returns __interrupt__).
  3. The suspended graph resumes correctly after Command(resume=decision) and
     produces the expected terminal output.
  4. A rejected decision is written into node_outputs correctly.
  5. ir_json stored in checkpoint metadata survives round-trip deserialization.

No mocks for LangGraph internals — this is the real stack.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from keel.compiler.compiler import compile as keel_compile
from keel.compiler.state import KeelState
from keel.ir.schema import IREdge, IRNode, Policies, WorkflowIR
from keel.sitl.gate import HumanGate
from keel.sitl.schema import HumanDecision


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _policies() -> Policies:
    return Policies(max_cost_usd=1.0, allowed_skills=["test"])


def _make_handler(node_id: str, output: dict[str, Any] | None = None):
    """Return a synchronous node handler that records its execution."""
    def handler(state: KeelState) -> KeelState:
        current = dict(state.get("node_outputs") or {})
        current[node_id] = output or {"node_id": node_id, "done": True}
        return {**state, "node_outputs": current}
    return handler


def _linear_ir(*node_ids: str, with_human_gate: bool = False) -> WorkflowIR:
    """Build a linear IR with the given sequence of node IDs.

    If with_human_gate is True, inserts a human_approval node between the
    second-to-last and last node so there's always at least one node before
    and after the gate.
    """
    if with_human_gate:
        # e.g. [read, synthesise, human_gate, write]
        ids = list(node_ids[:-1]) + ["human_gate"] + [node_ids[-1]]
    else:
        ids = list(node_ids)

    kinds: dict[str, Any] = {
        "read": "workspace_read",
        "synthesise": "synthesis",
        "write": "report_write",
        "human_gate": "human_approval",
    }

    nodes = [
        IRNode(id=nid, kind=kinds.get(nid, "independent_critic"))
        for nid in ids
    ]
    edges = [IREdge(from_node=ids[i], to_node=ids[i + 1]) for i in range(len(ids) - 1)]
    return WorkflowIR(
        schema_version="1",
        objective="e2e test",
        nodes=nodes,
        edges=edges,
        policies=_policies(),
    )


def _human_decision(node_id: str, plan_id: str, value: str = "approved") -> dict[str, Any]:
    return HumanDecision(
        node_id=node_id,
        plan_id=plan_id,
        decision=value,  # type: ignore[arg-type]
    ).model_dump()


# ---------------------------------------------------------------------------
# 1. Linear graph with NO HumanGate — completes in one invoke
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_linear_graph_completes_without_interrupt():
    ir = _linear_ir("read", "synthesise", "write")
    plan_id = "e2e-plan-no-gate"
    handlers = {
        "read": _make_handler("read", {"text": "paper text"}),
        "synthesise": _make_handler("synthesise", {"summary": "done"}),
        "write": _make_handler("write", {"report_path": "/out/report.md"}),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    result = await compiled.ainvoke({"node_outputs": {}}, config=cfg)

    assert "__interrupt__" not in result
    outputs = result["node_outputs"]
    assert outputs["read"]["text"] == "paper text"
    assert outputs["write"]["report_path"] == "/out/report.md"


# ---------------------------------------------------------------------------
# 2. Graph with HumanGate — first invoke suspends
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_human_gate_suspends_on_first_invoke():
    ir = _linear_ir("read", "synthesise", "write", with_human_gate=True)
    plan_id = "e2e-plan-gate-suspend"
    handlers = {
        "read": _make_handler("read", {"text": "paper text"}),
        "synthesise": _make_handler("synthesise", {"summary": "ok"}),
        "human_gate": HumanGate("human_gate", plan_id),
        "write": _make_handler("write", {"report_path": "/out/final.md"}),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    result = await compiled.ainvoke({"node_outputs": {}}, config=cfg)

    assert "__interrupt__" in result
    interrupts = result["__interrupt__"]
    assert len(interrupts) == 1
    payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
    assert payload["node_id"] == "human_gate"
    assert payload["plan_id"] == plan_id
    # Nodes before the gate ran
    assert "read" in result["node_outputs"]
    assert "synthesise" in result["node_outputs"]
    # write_report did NOT run yet
    assert "write" not in result["node_outputs"]


# ---------------------------------------------------------------------------
# 3. Approved resume — graph completes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_human_gate_approved_resume_completes():
    ir = _linear_ir("read", "synthesise", "write", with_human_gate=True)
    plan_id = "e2e-plan-gate-approved"
    handlers = {
        "read": _make_handler("read"),
        "synthesise": _make_handler("synthesise"),
        "human_gate": HumanGate("human_gate", plan_id),
        "write": _make_handler("write", {"report_path": "/out/approved.md"}),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    # Phase 1: invoke → suspend
    phase1 = await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    assert "__interrupt__" in phase1

    # Phase 2: resume with approved decision
    decision = _human_decision("human_gate", plan_id, "approved")
    phase2 = await compiled.ainvoke(Command(resume=decision), config=cfg)

    assert "__interrupt__" not in phase2
    outputs = phase2["node_outputs"]
    assert outputs["write"]["report_path"] == "/out/approved.md"
    assert "human_gate" in outputs
    assert outputs["human_gate"]["decision"]["decision"] == "approved"


# ---------------------------------------------------------------------------
# 4. Rejected resume — decision recorded, graph still completes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_human_gate_rejected_decision_recorded():
    ir = _linear_ir("read", "synthesise", "write", with_human_gate=True)
    plan_id = "e2e-plan-gate-rejected"
    handlers = {
        "read": _make_handler("read"),
        "synthesise": _make_handler("synthesise"),
        "human_gate": HumanGate("human_gate", plan_id),
        "write": _make_handler("write"),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    decision = _human_decision("human_gate", plan_id, "rejected")
    result = await compiled.ainvoke(Command(resume=decision), config=cfg)

    gate_output = result["node_outputs"]["human_gate"]
    assert gate_output["decision"]["decision"] == "rejected"


# ---------------------------------------------------------------------------
# 5. needs_revision decision recorded
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_human_gate_needs_revision_decision_recorded():
    ir = _linear_ir("read", "synthesise", "write", with_human_gate=True)
    plan_id = "e2e-plan-needs-revision"
    handlers = {
        "read": _make_handler("read"),
        "synthesise": _make_handler("synthesise"),
        "human_gate": HumanGate("human_gate", plan_id),
        "write": _make_handler("write"),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    decision = _human_decision("human_gate", plan_id, "needs_revision")
    result = await compiled.ainvoke(Command(resume=decision), config=cfg)

    assert result["node_outputs"]["human_gate"]["decision"]["decision"] == "needs_revision"


# ---------------------------------------------------------------------------
# 6. Checkpoint metadata round-trip (ir_json survives persist + retrieve)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_checkpoint_metadata_survives_round_trip():
    """ir_json stored in invoke config appears in snapshot.metadata after suspend."""
    ir = _linear_ir("read", "synthesise", "write", with_human_gate=True)
    plan_id = "e2e-plan-metadata"
    ir_json = ir.model_dump_json()
    handlers = {
        "read": _make_handler("read"),
        "synthesise": _make_handler("synthesise"),
        "human_gate": HumanGate("human_gate", plan_id),
        "write": _make_handler("write"),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {
        "configurable": {"thread_id": plan_id},
        "metadata": {"ir_json": ir_json, "job_id": "job-e2e"},
    }

    result = await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    assert "__interrupt__" in result

    # Retrieve checkpoint and verify metadata
    snapshot = await checkpointer.aget_tuple({"configurable": {"thread_id": plan_id}})
    assert snapshot is not None
    meta = snapshot.metadata or {}
    assert "ir_json" in meta
    # Round-trip: deserialize back into WorkflowIR
    recovered = WorkflowIR.model_validate_json(meta["ir_json"])
    assert recovered.objective == ir.objective
    assert len(recovered.nodes) == len(ir.nodes)


# ---------------------------------------------------------------------------
# 7. Second invoke after completion is idempotent (no crash)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completed_graph_second_invoke_idempotent():
    """Invoking a completed (non-interrupted) graph again returns the cached state."""
    ir = _linear_ir("read", "write")
    plan_id = "e2e-plan-idempotent"
    handlers = {
        "read": _make_handler("read"),
        "write": _make_handler("write", {"report_path": "/done.md"}),
    }
    checkpointer = MemorySaver()
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": plan_id}}

    r1 = await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    assert "__interrupt__" not in r1

    # Second invoke with same thread_id — LangGraph replays from checkpoint
    r2 = await compiled.ainvoke({"node_outputs": {}}, config=cfg)
    assert "__interrupt__" not in r2
    assert r2["node_outputs"]["write"]["report_path"] == "/done.md"
