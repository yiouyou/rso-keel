from __future__ import annotations

from keel.convergence.deterministic import DeterministicGate
from keel.convergence.rules import RulesGate
from keel.ir.schema import WorkflowIR
from keel.policy.execution import RuntimeCostGuard, build_policy_preflight_report


def _ir() -> WorkflowIR:
    return WorkflowIR.model_validate(
        {
            "schema_version": "v1",
            "objective": "policy execution test",
            "nodes": [
                {
                    "id": "read",
                    "kind": "workspace_read",
                    "inputs": {"skill": "reader"},
                    "budget": {"cost_usd": 0.2},
                },
                {
                    "id": "write",
                    "kind": "report_write",
                    "depends_on": ["read"],
                    "inputs": {"skill": "writer"},
                    "budget": {"cost_usd": 0.3},
                },
            ],
            "edges": [{"from_node": "read", "to_node": "write"}],
            "policies": {
                "max_cost_usd": 1.0,
                "allowed_skills": ["reader", "writer"],
                "critic_count": 0,
                "cost_per_1k_input": 0.001,
                "cost_per_1k_output": 0.002,
            },
        }
    )


def test_policy_preflight_report_captures_policy_snapshot():
    ir = _ir()
    report = build_policy_preflight_report(
        ir,
        deterministic=DeterministicGate().check(ir),
        rules=RulesGate().check(ir),
    )

    assert report.passed is True
    assert report.max_cost_usd == 1.0
    assert report.estimated_node_cost_usd == 0.5
    assert report.allowed_skills == ["reader", "writer"]
    assert report.network_access == "verified_sources_only"
    assert report.requires_human_approval is False
    assert report.critic_count == 0
    assert report.issue_codes == []


def test_policy_preflight_report_records_validation_error():
    report = build_policy_preflight_report(_ir(), validation_error="bad ir")

    assert report.passed is False
    assert report.issue_codes == ["IR_VALIDATION_FAILED"]
    assert report.validation_error == "bad ir"


def test_runtime_cost_guard_uses_directional_rates():
    snapshot = RuntimeCostGuard().check_state(
        _ir(),
        {
            "node_outputs": {
                "read": {"tokens_in": 1000, "tokens_out": 2000},
                "write": {"tokens_in": "3000", "tokens_out": 4000.0},
            }
        },
    )

    assert snapshot.tokens_in == 4000
    assert snapshot.tokens_out == 6000
    assert snapshot.approx_cost_usd == 0.016
    assert snapshot.exceeded is False
    assert snapshot.warning is None


def test_runtime_cost_guard_flags_ceiling_exceeded():
    ir = _ir()
    ir.policies.max_cost_usd = 0.01

    snapshot = RuntimeCostGuard().check_state(
        ir,
        {"node_outputs": {"write": {"tokens_in": 5000, "tokens_out": 5000}}},
    )

    assert snapshot.exceeded is True
    assert snapshot.warning is not None
    assert "max_cost_usd" in snapshot.warning
