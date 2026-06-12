"""End-to-end integration test — minimal closed loop.

Verifies that all keel modules work together in the full lifecycle:

  IR definition
    → validate (7-rule validator)
    → DeterministicGate check
    → RulesGate check
    → compile(ir, handlers, checkpointer)
    → invoke  [WorkspaceReadHandler — cache miss, result stored]
    → HumanGate interrupt
    → resume with HumanDecision
    → PlanProvenance recorded at each step
    → GovernanceArchive captures policies snapshot
    → crash recovery: re-invoke same thread_id → WorkspaceReadHandler cache hit

This is NOT a unit test — it exercises real module interactions.
No mocks, no monkeypatching. Uses NullRecorder and InMemoryCache throughout.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from keel.audit.schema import AuditTrace
from keel.compiler.compiler import compile as keel_compile
from keel.compiler.state import KeelState
from keel.convergence.deterministic import DeterministicGate
from keel.convergence.rules import RulesGate
from keel.handlers.workspace_read import WorkspaceReadHandler
from keel.ir.schema import WorkflowIR
from keel.ir.validator import validate
from keel.persistence.cache import ContentHashCache, InMemoryCache
from keel.persistence.checkpointer import make_checkpointer
from keel.provenance.recorder import NullRecorder
from keel.provenance.schema import (
    KeelActor,
    NodeTrace,
    PlanProvenance,
)
from keel.registry.governance import GovernanceArchive, GovernanceRecord
from keel.registry.schema import SkillRegistry, SkillSpec
from keel.sitl.gate import HumanGate
from keel.sitl.schema import ApprovalOutcome
from langgraph.types import Command


# ---------------------------------------------------------------------------
# Test IR — paper review scenario (minimal)
# ---------------------------------------------------------------------------

PAPER_REVIEW_IR = {
    "schema_version": "v1",
    "objective": "Review paper: 'Neural scaling laws revisited'",
    "nodes": [
        {"id": "read_paper",   "kind": "workspace_read",
         "inputs": {"skill": "file_reader"}},
        {"id": "critic",       "kind": "independent_critic",
         "depends_on": ["read_paper"],
         "inputs": {"skill": "independent_critic_v1"}},
        {"id": "human_gate",   "kind": "human_approval",
         "depends_on": ["critic"]},
        {"id": "write_report", "kind": "report_write",
         "depends_on": ["human_gate"]},
    ],
    "edges": [
        {"from_node": "read_paper",   "to_node": "critic"},
        {"from_node": "critic",       "to_node": "human_gate"},
        {"from_node": "human_gate",   "to_node": "write_report"},
    ],
    "policies": {
        "max_cost_usd": 5.0,
        "allowed_skills": ["file_reader", "independent_critic_v1"],
        "requires_human_approval": True,
        "critic_count": 1,
    },
}


def _build_ir() -> WorkflowIR:
    return WorkflowIR.model_validate(PAPER_REVIEW_IR)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolver(call_log: list[str]):
    def resolve(node_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        call_log.append(node_id)
        return {"content": f"file-content-for-{node_id}", "status": "ok"}
    return resolve


def _build_handlers(
    cache: ContentHashCache,
    call_log: list[str],
    plan_id: str,
) -> dict:
    return {
        "read_paper": WorkspaceReadHandler("read_paper", cache, _resolver(call_log)),
        "human_gate": HumanGate("human_gate", plan_id),
        "critic": lambda state: {
            **state,
            "node_outputs": {
                **state.get("node_outputs", {}),
                "critic": {
                    "issues": [],
                    "suggestions": ["Verify claims with cited sources"],
                },
            },
        },
        "write_report": lambda state: {
            **state,
            "node_outputs": {
                **state.get("node_outputs", {}),
                "write_report": {"report": "Final report written."},
            },
        },
    }


# ---------------------------------------------------------------------------
# E2E Test
# ---------------------------------------------------------------------------


def test_full_pipeline_validate_to_provenance() -> None:
    """Full lifecycle: validate → gate checks → compile → invoke → provenance."""
    ir = _build_ir()

    # 1. IR validator — must pass all 7 rules
    validate(ir)

    # 2. DeterministicGate — structural checks
    det_result = DeterministicGate().check(ir)
    assert det_result.passed, f"DeterministicGate failed: {det_result.issue_codes}"

    # 3. RulesGate — policy checks
    rules_result = RulesGate().check(ir)
    assert rules_result.passed, f"RulesGate failed: {rules_result.issue_codes}"

    # 4. Skill registry — register allowed skills
    registry = SkillRegistry()
    registry.register(SkillSpec(
        skill_id="file_reader", version="1.0.0",
        supported_node_kinds=["workspace_read"],
    ))
    registry.register(SkillSpec(
        skill_id="independent_critic_v1", version="1.0.0",
        supported_node_kinds=["independent_critic"],
    ))
    unregistered = registry.validate_allowed_skills(ir.policies.allowed_skills)
    assert unregistered == [], f"Unregistered skills: {unregistered}"

    # 5. GovernanceArchive — capture policies before running
    plan_id = str(uuid.uuid4())
    gov_archive = GovernanceArchive()
    gov_record = GovernanceRecord.from_policies(plan_id, ir.policies.model_dump())
    gov_archive.record(gov_record)
    assert len(gov_archive) == 1
    assert gov_archive.get(plan_id).provenance_enabled is True

    # 6. PlanProvenance — start record
    actor = KeelActor(user_id="researcher-1", project_id="proj-keel")
    prov = PlanProvenance.start(
        plan_id=plan_id,
        ir_json=ir.model_dump_json(),
        ir_schema_version=ir.schema_version,
        objective=ir.objective,
        actor=actor,
        policies=ir.policies,
    )
    assert prov.workflow_ir_hash  # non-empty SHA-256
    recorder = NullRecorder()
    recorder.record_plan_start(prov)

    # 7. Compile with MemorySaver checkpointer
    cache = ContentHashCache(InMemoryCache())
    call_log: list[str] = []
    checkpointer = make_checkpointer()  # MemorySaver
    handlers = _build_handlers(cache, call_log, plan_id)
    compiled = keel_compile(ir, node_handlers=handlers, checkpointer=checkpointer)

    cfg = {"configurable": {"thread_id": plan_id}}
    initial: KeelState = {"node_outputs": {}}

    # 8. First invoke — runs read_paper + critic, then suspends at human_gate
    result1 = compiled.invoke(initial, config=cfg)
    assert "read_paper" in call_log, "WorkspaceReadHandler must have been called"
    assert "read_paper" in result1.get("node_outputs", {})
    # human_gate interrupted — write_report not yet reached
    assert "write_report" not in result1.get("node_outputs", {})

    # 9. Record node traces for completed nodes
    for node_id in ["read_paper", "critic"]:
        node = next(n for n in ir.nodes if n.id == node_id)
        trace = NodeTrace(node_id=node_id, kind=node.kind, status="succeeded")
        recorder.record_node_update(plan_id, trace)

    # 10. Resume with human decision
    human_decision = {
        "node_id": "human_gate",
        "plan_id": plan_id,
        "decision": "approved",
        "reviewer_id": "senior-reviewer",
        "notes": "Claims are consistent with cited literature.",
    }
    result2 = compiled.invoke(Command(resume=human_decision), config=cfg)

    assert "human_gate" in result2.get("node_outputs", {})
    gate_output = result2["node_outputs"]["human_gate"]
    assert gate_output["decision"]["decision"] == "approved"
    assert "write_report" in result2.get("node_outputs", {})

    # 11. Record human gate trace with audit_trace
    outcome = ApprovalOutcome.model_validate(gate_output)
    gate_trace = NodeTrace(
        node_id="human_gate",
        kind="human_approval",
        status="succeeded",
        audit_trace=AuditTrace(
            skill_id="human_gate",
            issues_found=[],
            suggested_experiments=[outcome.decision.notes],
        ),
    )
    recorder.record_node_update(plan_id, gate_trace)

    # 12. Finalise provenance
    prov.status = "succeeded"
    prov.integrity.human_reviewed = outcome.human_reviewed
    recorder.record_plan_end(prov)

    assert prov.integrity.human_reviewed is True


def test_crash_recovery_workspace_read_zero_repeat() -> None:
    """Crash between first and second invoke — WorkspaceReadHandler not called twice."""
    ir = _build_ir()
    validate(ir)

    cache = ContentHashCache(InMemoryCache())
    call_log: list[str] = []
    checkpointer = make_checkpointer()
    plan_id = "crash-test-plan"
    cfg = {"configurable": {"thread_id": plan_id}}
    initial: KeelState = {"node_outputs": {}}

    # First run — reads file, hits human_gate, suspends
    compiled_v1 = keel_compile(
        ir, node_handlers=_build_handlers(cache, call_log, plan_id),
        checkpointer=checkpointer,
    )
    compiled_v1.invoke(initial, config=cfg)
    assert call_log.count("read_paper") == 1

    # Simulate crash — discard compiled graph, rebuild
    del compiled_v1
    compiled_v2 = keel_compile(
        ir, node_handlers=_build_handlers(cache, call_log, plan_id),
        checkpointer=checkpointer,
    )

    # Resume — LangGraph restores from checkpoint; cache absorbs WorkspaceReadHandler
    compiled_v2.invoke(Command(resume={
        "node_id": "human_gate", "plan_id": plan_id,
        "decision": "approved", "reviewer_id": "r1", "notes": "",
    }), config=cfg)

    assert call_log.count("read_paper") == 1, (
        "WorkspaceReadHandler called more than once — cache did not absorb repeat"
    )


def test_governance_floor_captured_in_archive() -> None:
    """GovernanceArchive always captures the governance floor fields."""
    ir = _build_ir()
    plan_id = "gov-test"
    archive = GovernanceArchive()
    archive.record(GovernanceRecord.from_policies(plan_id, ir.policies.model_dump()))

    record = archive.get(plan_id)
    assert record.provenance_enabled is True       # floor — always True
    assert record.max_cost_usd == 5.0              # floor
    assert "file_reader" in record.allowed_skills  # floor
    assert record.requires_human_approval is True  # tunable — captured as-configured


def test_convergence_gates_catch_bad_ir() -> None:
    """DeterministicGate catches IR violations that would break runtime."""
    bad_ir = WorkflowIR.model_validate({
        "schema_version": "v1",
        "objective": "Bad plan",
        "nodes": [
            {"id": "critic", "kind": "independent_critic"},
            {"id": "report", "kind": "report_write"},
        ],
        "edges": [{"from_node": "critic", "to_node": "ghost_node"}],  # dangling!
        "policies": {
            "max_cost_usd": 5.0,
            "allowed_skills": [],
            "requires_human_approval": True,  # but no human_approval node!
        },
    })
    result = DeterministicGate().check(bad_ir)
    assert not result.passed
    assert "NO_DATA_SOURCE" in result.issue_codes
    assert "MISSING_HUMAN_GATE" in result.issue_codes
    assert "DANGLING_EDGE" in result.issue_codes
    # All 3 collected — not fail-fast
    assert len(result.issues) >= 3
