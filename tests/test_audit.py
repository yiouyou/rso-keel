"""M5 audit_trace protocol tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from keel.audit.sample_skill import IndependentCriticSkill
from keel.audit.schema import AuditTrace, IntermediateSignal, SignalType, SkillResponse
from keel.provenance.recorder import NullRecorder
from keel.provenance.schema import NodeTrace


def test_intermediate_signal_valid() -> None:
    signal = IntermediateSignal(
        step=1,
        signal_type=SignalType.reasoning,
        content="checked source",
        confidence=0.8,
    )

    assert signal.step == 1
    assert signal.signal_type is SignalType.reasoning
    assert signal.content == "checked source"
    assert signal.confidence == 0.8


def test_intermediate_signal_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        IntermediateSignal(
            step=1,
            signal_type=SignalType.validation,
            content="checked source",
            confidence=1.5,
        )


def test_intermediate_signal_step_zero() -> None:
    with pytest.raises(ValidationError):
        IntermediateSignal(
            step=0,
            signal_type=SignalType.validation,
            content="checked source",
        )


def test_audit_trace_defaults() -> None:
    trace = AuditTrace(skill_id="x")

    assert trace.skill_version is None
    assert trace.reasoning_steps == 0
    assert trace.intermediate_signals == []
    assert trace.issues_found == []
    assert trace.suggested_experiments == []
    assert trace.raw_model_calls == 0
    assert trace.model_usage == []


def test_audit_trace_round_trip() -> None:
    trace = AuditTrace(
        skill_id="x",
        intermediate_signals=[
            IntermediateSignal(
                step=1,
                signal_type=SignalType.extraction,
                content="extracted claim",
                confidence=0.9,
            )
        ],
    )

    restored = AuditTrace.model_validate_json(trace.model_dump_json())

    assert restored == trace


def test_skill_response_has_audit_trace() -> None:
    response = SkillResponse(
        ok=True,
        result={"value": "accepted"},
        audit_trace=AuditTrace(skill_id="x"),
    )

    assert isinstance(response.audit_trace, AuditTrace)


def test_independent_critic_skill_no_issues() -> None:
    response = IndependentCriticSkill().run(
        {"text": "The sample supports claim A.", "claim": "claim A"}
    )

    assert response.ok is True
    assert response.audit_trace.issues_found == []
    assert response.result == {"claim": "claim A", "issues_count": 0}


def test_independent_critic_skill_issue_found() -> None:
    response = IndependentCriticSkill().run(
        {"text": "The sample supports another claim.", "claim": "claim A"}
    )

    assert response.ok is False
    assert response.audit_trace.issues_found
    assert response.result == {"claim": "claim A", "issues_count": 1}


def test_intermediate_signals_populated() -> None:
    response = IndependentCriticSkill().run(
        {"text": "The sample supports claim A.", "claim": "claim A"}
    )

    assert len(response.audit_trace.intermediate_signals) >= 2


def test_audit_trace_does_not_assert_truth() -> None:
    response = IndependentCriticSkill().run(
        {"text": "The sample supports another claim.", "claim": "claim A"}
    )

    assert response.audit_trace.suggested_experiments == [
        "Verify claim against cited sources",
        "Run independent replication experiment",
    ]


def test_node_trace_accepts_audit_trace() -> None:
    audit_trace = AuditTrace(skill_id="x")
    node_trace = NodeTrace(
        node_id="n1",
        kind="independent_critic",
        audit_trace=audit_trace,
    )

    assert node_trace.audit_trace == audit_trace


def test_node_trace_audit_trace_none_by_default() -> None:
    assert NodeTrace(node_id="n1", kind="independent_critic").audit_trace is None


def test_wire_into_provenance_recorder() -> None:
    response = IndependentCriticSkill().run(
        {"text": "The sample supports another claim.", "claim": "claim A"}
    )
    node_trace = NodeTrace(
        node_id="n1",
        kind="independent_critic",
        status="succeeded",
        audit_trace=response.audit_trace,
    )

    NullRecorder().record_node_update("plan-1", node_trace)

    assert isinstance(node_trace.audit_trace, AuditTrace)


def test_no_platform_imports_in_audit() -> None:
    audit_dir = Path(__file__).parents[1] / "src" / "keel" / "audit"

    for path in audit_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            else:
                continue

            assert not any(name == "app" or name.startswith("app.") for name in names)
            assert not any(
                name == "backend" or name.startswith("backend.") for name in names
            )
