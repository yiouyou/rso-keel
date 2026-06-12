"""M2 provenance schema + recorder tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError as PydanticValidationError

from keel.ir.schema import Policies, WorkflowIR
from keel.provenance.recorder import NullRecorder, ProvenanceRecorder
from keel.provenance.schema import (
    KeelActor,
    NodeTrace,
    PlanIntegrity,
    PlanProvenance,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _actor(**kw) -> KeelActor:
    return KeelActor(user_id="user-1", project_id="proj-1", **kw)


def _policies(**kw) -> Policies:
    defaults: dict = {"max_cost_usd": 10.0, "allowed_skills": ["skill_a"]}
    defaults.update(kw)
    return Policies(**defaults)


def _minimal_ir() -> WorkflowIR:
    return WorkflowIR.model_validate(
        {
            "schema_version": "v1",
            "objective": "Review paper X",
            "nodes": [{"id": "n1", "kind": "workspace_read"}],
            "policies": {"max_cost_usd": 10.0, "allowed_skills": ["skill_a"]},
        }
    )


# ---------------------------------------------------------------------------
# PlanProvenance construction
# ---------------------------------------------------------------------------


def test_plan_provenance_start_factory() -> None:
    ir = _minimal_ir()
    ir_json = ir.model_dump_json()
    prov = PlanProvenance.start(
        plan_id="plan-abc",
        ir_json=ir_json,
        ir_schema_version=ir.schema_version,
        objective=ir.objective,
        actor=_actor(),
        policies=ir.policies,
    )
    assert prov.plan_id == "plan-abc"
    assert prov.schema_version == "keel-v1"
    assert prov.status == "running"
    assert len(prov.workflow_ir_hash) == 64  # SHA-256 hex


def test_workflow_ir_hash_is_deterministic() -> None:
    ir = _minimal_ir()
    ir_json = ir.model_dump_json()
    p1 = PlanProvenance.start(
        plan_id="p", ir_json=ir_json, ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=ir.policies,
    )
    p2 = PlanProvenance.start(
        plan_id="p", ir_json=ir_json, ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=ir.policies,
    )
    assert p1.workflow_ir_hash == p2.workflow_ir_hash


def test_config_snapshot_contains_policies() -> None:
    policies = _policies(max_cost_usd=42.0)
    ir = _minimal_ir()
    prov = PlanProvenance.start(
        plan_id="p", ir_json=ir.model_dump_json(), ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=policies,
    )
    assert prov.config_snapshot["max_cost_usd"] == 42.0
    assert prov.config_snapshot["provenance_enabled"] is True


def test_round_trip_json() -> None:
    ir = _minimal_ir()
    prov = PlanProvenance.start(
        plan_id="p", ir_json=ir.model_dump_json(), ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=ir.policies,
    )
    restored = PlanProvenance.model_validate_json(prov.model_dump_json())
    assert restored == prov


# ---------------------------------------------------------------------------
# Governance floor validation
# ---------------------------------------------------------------------------


def test_empty_plan_id_rejected() -> None:
    with pytest.raises((PydanticValidationError, ValueError)):
        PlanProvenance(
            plan_id="",
            workflow_ir_hash="abc",
            ir_schema_version="v1",
            objective="obj",
            actor=_actor(),
            config_snapshot={},
        )


def test_empty_objective_rejected() -> None:
    with pytest.raises((PydanticValidationError, ValueError)):
        PlanProvenance(
            plan_id="p",
            workflow_ir_hash="abc",
            ir_schema_version="v1",
            objective="   ",
            actor=_actor(),
            config_snapshot={},
        )


def test_schema_version_is_keel_v1() -> None:
    ir = _minimal_ir()
    prov = PlanProvenance.start(
        plan_id="p", ir_json=ir.model_dump_json(), ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=ir.policies,
    )
    assert prov.schema_version == "keel-v1"


def test_schema_version_cannot_be_overridden() -> None:
    """Literal["keel-v1"] means Pydantic rejects any other value."""
    with pytest.raises(PydanticValidationError):
        PlanProvenance(
            schema_version="v1",  # type: ignore[arg-type]
            plan_id="p",
            workflow_ir_hash="abc",
            ir_schema_version="v1",
            objective="obj",
            actor=_actor(),
            config_snapshot={},
        )


# ---------------------------------------------------------------------------
# NodeTrace
# ---------------------------------------------------------------------------


def test_node_trace_defaults() -> None:
    trace = NodeTrace(node_id="n1", kind="workspace_read")
    assert trace.status == "pending"
    assert trace.model_usage == []
    assert trace.audit_trace is None  # M5: changed from dict to AuditTrace | None
    assert trace.error is None


def test_node_trace_round_trip() -> None:
    from keel.audit.schema import AuditTrace
    trace = NodeTrace(
        node_id="n1",
        kind="synthesis",
        status="succeeded",
        model_usage=[{"model": "gpt-4o", "tokens": 500}],
        audit_trace=AuditTrace(skill_id="test_skill", reasoning_steps=3),
    )
    restored = NodeTrace.model_validate_json(trace.model_dump_json())
    assert restored == trace


# ---------------------------------------------------------------------------
# KeelActor — mirrors JobProvenanceActor field names
# ---------------------------------------------------------------------------


def test_keel_actor_field_names_match_platform() -> None:
    """Ensure KeelActor has the same field names as JobProvenanceActor."""
    expected_fields = {"user_id", "project_id", "session_id", "workflow_action_id"}
    assert expected_fields == set(KeelActor.model_fields.keys())


def test_keel_actor_all_optional() -> None:
    actor = KeelActor()
    assert actor.user_id is None


# ---------------------------------------------------------------------------
# PlanIntegrity — mirrors JobProvenanceIntegrity field names
# ---------------------------------------------------------------------------


def test_plan_integrity_field_names_match_platform() -> None:
    """Ensure PlanIntegrity has the same field names as JobProvenanceIntegrity
    (plus human_reviewed which extends the platform model)."""
    fields = set(PlanIntegrity.model_fields.keys())
    # Platform fields that must be present
    assert {"evidence_levels", "partial", "warnings"}.issubset(fields)


def test_plan_integrity_defaults() -> None:
    integrity = PlanIntegrity()
    assert integrity.human_reviewed is False
    assert integrity.partial is False


# ---------------------------------------------------------------------------
# NullRecorder satisfies ProvenanceRecorder protocol
# ---------------------------------------------------------------------------


def test_null_recorder_satisfies_protocol() -> None:
    recorder = NullRecorder()
    assert isinstance(recorder, ProvenanceRecorder)


def test_null_recorder_is_a_no_op() -> None:
    recorder = NullRecorder()
    ir = _minimal_ir()
    prov = PlanProvenance.start(
        plan_id="p", ir_json=ir.model_dump_json(), ir_schema_version="v1",
        objective="obj", actor=_actor(), policies=ir.policies,
    )
    trace = NodeTrace(node_id="n1", kind="workspace_read", status="succeeded")
    recorder.record_plan_start(prov)
    recorder.record_node_update("p", trace)
    recorder.record_plan_end(prov)  # must not raise


# ---------------------------------------------------------------------------
# Integration: PlanProvenance does not conflict with platform JobProvenance
# ---------------------------------------------------------------------------


def test_plan_provenance_serializes_to_json_cleanly() -> None:
    ir = _minimal_ir()
    prov = PlanProvenance.start(
        plan_id="plan-xyz",
        ir_json=ir.model_dump_json(),
        ir_schema_version="v1",
        objective="Review paper X",
        actor=_actor(session_id="sess-1", workflow_action_id="paper_review"),
        policies=ir.policies,
    )
    prov.node_traces.append(NodeTrace(node_id="n1", kind="workspace_read", status="succeeded"))
    data = json.loads(prov.model_dump_json())
    assert data["schema_version"] == "keel-v1"
    assert data["actor"]["user_id"] == "user-1"
    assert data["node_traces"][0]["kind"] == "workspace_read"
