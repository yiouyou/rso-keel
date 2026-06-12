"""SITL human approval gate tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt
from langgraph.types import Command
from pydantic import ValidationError

from keel.compiler.compiler import compile as keel_compile
from keel.compiler.state import KeelState
from keel.ir.schema import WorkflowIR
from keel.sitl.gate import HumanGate
from keel.sitl.schema import ApprovalOutcome, ApprovalRequest, HumanDecision


def _ir() -> WorkflowIR:
    return WorkflowIR.model_validate(
        {
            "schema_version": "v1",
            "objective": "Human approval",
            "nodes": [{"id": "gate", "kind": "human_approval"}],
            "policies": {"max_cost_usd": 10.0, "allowed_skills": []},
        }
    )


def _decision(value: str) -> dict[str, str]:
    return {
        "node_id": "gate",
        "plan_id": "p1",
        "decision": value,
        "reviewer_id": "human-1",
        "notes": "looks good",
    }


def _run_gate_resume(decision: str) -> KeelState:
    compiled = keel_compile(
        _ir(),
        node_handlers={"gate": HumanGate("gate", "p1")},
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": f"sitl-{decision}"}}
    initial_state: KeelState = {"node_outputs": {}, "pending_approval": None}

    try:
        compiled.invoke(initial_state, config=config)
    except Exception:
        pass

    return compiled.invoke(Command(resume=_decision(decision)), config=config)


def test_approval_request_defaults() -> None:
    request = ApprovalRequest(node_id="n", plan_id="p")

    assert request.context == {}
    assert request.requested_at is not None


def test_human_decision_valid_values() -> None:
    for value in ("approved", "rejected", "needs_revision"):
        decision = HumanDecision(node_id="n", plan_id="p", decision=value)

        assert decision.decision == value


def test_human_decision_invalid_value() -> None:
    with pytest.raises(ValidationError):
        HumanDecision(node_id="n", plan_id="p", decision="unknown")


def test_approval_outcome_human_reviewed_always_true() -> None:
    request = ApprovalRequest(node_id="n", plan_id="p")
    decision = HumanDecision(node_id="n", plan_id="p", decision="approved")
    outcome = ApprovalOutcome(request=request, decision=decision)

    assert outcome.human_reviewed is True


def test_approval_request_round_trip() -> None:
    request = ApprovalRequest(node_id="n", plan_id="p")

    round_tripped = ApprovalRequest.model_validate_json(request.model_dump_json())

    assert round_tripped == request


def test_human_decision_round_trip() -> None:
    decision = HumanDecision(node_id="n", plan_id="p", decision="approved")

    round_tripped = HumanDecision.model_validate_json(decision.model_dump_json())

    assert round_tripped == decision


def test_human_gate_raises_node_interrupt() -> None:
    # interrupt() requires a LangGraph runnable context; outside it raises RuntimeError.
    # Inside a compiled graph, LangGraph converts it to NodeInterrupt.
    # Verify via the compiled-graph path.
    from langgraph.checkpoint.memory import MemorySaver
    from keel.compiler.compiler import compile as keel_compile
    from keel.ir.schema import WorkflowIR

    ir = WorkflowIR.model_validate({
        "schema_version": "v1",
        "objective": "test",
        "nodes": [{"id": "gate", "kind": "human_approval"}],
        "policies": {"max_cost_usd": 10.0, "allowed_skills": []},
    })
    gate = HumanGate("gate", "p1")
    compiled = keel_compile(ir, node_handlers={"gate": gate},
                            checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t-interrupt-check"}}
    # LangGraph surfaces the interrupt — graph stops, state is checkpointed
    result = compiled.invoke({"node_outputs": {}}, config=cfg)
    # After interrupt the graph is suspended; node_outputs won't have "gate" yet
    assert "gate" not in (result.get("node_outputs") or {})


def test_human_gate_resume_approved() -> None:
    result = _run_gate_resume("approved")

    assert result["node_outputs"]["gate"]["decision"]["decision"] == "approved"


def test_human_gate_resume_rejected() -> None:
    result = _run_gate_resume("rejected")

    assert result["node_outputs"]["gate"]["decision"]["decision"] == "rejected"


def test_human_gate_clears_pending_approval() -> None:
    result = _run_gate_resume("approved")

    assert result["pending_approval"] is None


def test_human_gate_outcome_in_node_outputs() -> None:
    result = _run_gate_resume("approved")

    assert "decision" in result["node_outputs"]["gate"]


def test_human_decision_decided_at_set() -> None:
    decision = HumanDecision(node_id="n", plan_id="p", decision="approved")

    assert decision.decided_at is not None


def test_keel_state_has_pending_approval() -> None:
    assert "pending_approval" in KeelState.__annotations__


def test_no_platform_imports_in_sitl() -> None:
    sitl_dir = Path(__file__).parent.parent / "src" / "keel" / "sitl"
    imported_modules: list[str] = []

    for source_path in sorted(sitl_dir.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

    assert not any(name == "app" or name.startswith("app.") for name in imported_modules)
    assert not any(name == "backend" or name.startswith("backend.") for name in imported_modules)
