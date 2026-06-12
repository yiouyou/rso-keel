"""Schema serialisation round-trip tests."""

import json

import pytest
from pydantic import ValidationError as PydanticValidationError

from keel.ir.schema import (
    ConditionalEdge,
    IREdge,
    IRNode,
    Policies,
    WorkflowIR,
)


def _minimal_ir(**overrides) -> dict:
    base = {
        "schema_version": "v1",
        "objective": "Review paper X",
        "nodes": [{"id": "n1", "kind": "workspace_read"}],
        "edges": [],
        "conditional_edges": [],
        "policies": {
            "max_cost_usd": 10.0,
            "allowed_skills": ["read_file"],
        },
    }
    base.update(overrides)
    return base


def test_round_trip_json() -> None:
    ir = WorkflowIR.model_validate(_minimal_ir())
    dumped = ir.model_dump_json()
    restored = WorkflowIR.model_validate_json(dumped)
    assert restored == ir


def test_round_trip_dict() -> None:
    ir = WorkflowIR.model_validate(_minimal_ir())
    restored = WorkflowIR.model_validate(ir.model_dump())
    assert restored == ir


def test_provenance_enabled_always_true() -> None:
    ir = WorkflowIR.model_validate(_minimal_ir())
    assert ir.policies.provenance_enabled is True


def test_provenance_enabled_cannot_be_false() -> None:
    data = _minimal_ir()
    data["policies"]["provenance_enabled"] = False
    with pytest.raises(PydanticValidationError):
        WorkflowIR.model_validate(data)


def test_all_six_node_kinds_parse() -> None:
    kinds = [
        "workspace_read",
        "literature_search",
        "independent_critic",
        "synthesis",
        "human_approval",
        "report_write",
    ]
    for kind in kinds:
        node = IRNode(id="n", kind=kind)  # type: ignore[arg-type]
        assert node.kind == kind


def test_invalid_node_kind_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        IRNode(id="n", kind="unknown_kind")  # type: ignore[arg-type]


def test_all_six_condition_fields_parse() -> None:
    fields = [
        "evidence_level",
        "confidence_tier",
        "requires_human_review",
        "safety_ethics_flags",
        "opportunity_rank_tier",
        "next_decision",
    ]
    for field in fields:
        edge = ConditionalEdge(
            from_node="a", condition_field=field, condition_value="high", to_node="b"  # type: ignore[arg-type]
        )
        assert edge.condition_field == field


def test_invalid_condition_field_rejected() -> None:
    with pytest.raises(PydanticValidationError):
        ConditionalEdge(
            from_node="a",
            condition_field="free_text_expression",  # type: ignore[arg-type]
            condition_value="x > 3",
            to_node="b",
        )


def test_policies_defaults() -> None:
    p = Policies(max_cost_usd=5.0, allowed_skills=[])
    assert p.max_subagents == 4
    assert p.max_iterations == 10
    assert p.requires_human_approval is False
    assert p.network_access == "verified_sources_only"


def test_network_access_none_allowed() -> None:
    p = Policies(max_cost_usd=5.0, allowed_skills=[], network_access="none")
    assert p.network_access == "none"


def test_policies_cost_per_1k_tokens_defaults() -> None:
    p = Policies(max_cost_usd=1.0, allowed_skills=[])
    assert p.cost_per_1k_tokens == 0.003


def test_policies_cost_per_1k_tokens_custom() -> None:
    p = Policies(max_cost_usd=1.0, allowed_skills=[], cost_per_1k_tokens=0.003)
    assert p.cost_per_1k_tokens == 0.003
    # Round-trips through JSON
    p2 = Policies.model_validate_json(p.model_dump_json())
    assert p2.cost_per_1k_tokens == 0.003
