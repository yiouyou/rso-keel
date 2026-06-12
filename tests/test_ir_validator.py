"""Validator tests: 7 rules × (1 pass + 1 fail) = 14 test functions."""

import pytest

from keel.ir.schema import WorkflowIR
from keel.ir.validator import MAX_COST_USD_CEILING, ValidationError, validate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ir(**overrides) -> WorkflowIR:
    """Build a minimal valid WorkflowIR, applying *overrides* to the raw dict."""
    base: dict = {
        "schema_version": "v1",
        "objective": "Test objective",
        "nodes": [{"id": "n1", "kind": "workspace_read"}],
        "edges": [],
        "conditional_edges": [],
        "policies": {
            "max_cost_usd": 10.0,
            "allowed_skills": ["skill_a"],
        },
    }
    base.update(overrides)
    return WorkflowIR.model_validate(base)


def _ir_raw(**overrides) -> dict:
    base: dict = {
        "schema_version": "v1",
        "objective": "Test objective",
        "nodes": [{"id": "n1", "kind": "workspace_read"}],
        "edges": [],
        "conditional_edges": [],
        "policies": {
            "max_cost_usd": 10.0,
            "allowed_skills": ["skill_a"],
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Rule 1 — schema_version
# ---------------------------------------------------------------------------


def test_rule1_pass() -> None:
    ir = _ir(schema_version="v1")
    validate(ir)  # must not raise


def test_rule1_fail() -> None:
    ir = _ir(schema_version="v99")
    with pytest.raises(ValidationError, match="Rule 1"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 2 — node kinds (schema already enforces Literal; test validator message)
# ---------------------------------------------------------------------------


def test_rule2_pass() -> None:
    ir = _ir(nodes=[{"id": "n1", "kind": "synthesis"}])
    validate(ir)


def test_rule2_fail(monkeypatch) -> None:
    """Bypass Pydantic to inject a bad kind directly, then verify the validator catches it."""
    ir = _ir(nodes=[{"id": "n1", "kind": "workspace_read"}])
    # Patch the node kind after construction to simulate a future schema drift.
    ir.nodes[0].__dict__["kind"] = "forbidden_kind"
    with pytest.raises(ValidationError, match="Rule 2"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 3 — skill allowlist
# ---------------------------------------------------------------------------


def test_rule3_pass() -> None:
    ir = _ir(
        nodes=[{"id": "n1", "kind": "synthesis", "inputs": {"skill": "skill_a"}}],
        policies={"max_cost_usd": 10.0, "allowed_skills": ["skill_a"]},
    )
    validate(ir)


def test_rule3_fail() -> None:
    ir = _ir(
        nodes=[{"id": "n1", "kind": "synthesis", "inputs": {"skill": "forbidden_skill"}}],
        policies={"max_cost_usd": 10.0, "allowed_skills": ["skill_a"]},
    )
    with pytest.raises(ValidationError, match="Rule 3"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 4 — governance floor
# ---------------------------------------------------------------------------


def test_rule4_pass() -> None:
    ir = _ir(policies={"max_cost_usd": 50.0, "allowed_skills": []})
    validate(ir)


def test_rule4_fail_cost_zero() -> None:
    ir = _ir(policies={"max_cost_usd": 0.0, "allowed_skills": []})
    with pytest.raises(ValidationError, match="Rule 4"):
        validate(ir)


def test_rule4_fail_cost_exceeds_ceiling() -> None:
    ir = _ir(policies={"max_cost_usd": MAX_COST_USD_CEILING + 1, "allowed_skills": []})
    with pytest.raises(ValidationError, match="Rule 4"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 5 — conditional edges
# ---------------------------------------------------------------------------


def test_rule5_pass() -> None:
    ir = _ir(
        nodes=[
            {"id": "n1", "kind": "workspace_read"},
            {"id": "n2", "kind": "synthesis"},
        ],
        conditional_edges=[
            {
                "from_node": "n1",
                "condition_field": "evidence_level",
                "condition_value": "high",
                "to_node": "n2",
            }
        ],
    )
    validate(ir)


def test_rule5_fail_free_code_in_value() -> None:
    ir = _ir(
        nodes=[
            {"id": "n1", "kind": "workspace_read"},
            {"id": "n2", "kind": "synthesis"},
        ],
        conditional_edges=[
            {
                "from_node": "n1",
                "condition_field": "evidence_level",
                "condition_value": "lambda x: x > 3",
                "to_node": "n2",
            }
        ],
    )
    with pytest.raises(ValidationError, match="Rule 5"):
        validate(ir)


def test_rule5_fail_value_too_long() -> None:
    ir = _ir(
        nodes=[
            {"id": "n1", "kind": "workspace_read"},
            {"id": "n2", "kind": "synthesis"},
        ],
        conditional_edges=[
            {
                "from_node": "n1",
                "condition_field": "confidence_tier",
                "condition_value": "x" * 201,
                "to_node": "n2",
            }
        ],
    )
    with pytest.raises(ValidationError, match="Rule 5"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 6 — DAG (no cycles, all ids exist)
# ---------------------------------------------------------------------------


def test_rule6_pass_linear_chain() -> None:
    ir = _ir(
        nodes=[
            {"id": "a", "kind": "workspace_read"},
            {"id": "b", "kind": "synthesis", "depends_on": ["a"]},
            {"id": "c", "kind": "report_write", "depends_on": ["b"]},
        ],
        edges=[
            {"from_node": "a", "to_node": "b"},
            {"from_node": "b", "to_node": "c"},
        ],
    )
    validate(ir)


def test_rule6_fail_cycle() -> None:
    ir = _ir(
        nodes=[
            {"id": "a", "kind": "workspace_read"},
            {"id": "b", "kind": "synthesis"},
        ],
        edges=[
            {"from_node": "a", "to_node": "b"},
            {"from_node": "b", "to_node": "a"},
        ],
    )
    with pytest.raises(ValidationError, match="Rule 6"):
        validate(ir)


def test_rule6_fail_unknown_depends_on() -> None:
    ir = _ir(
        nodes=[{"id": "a", "kind": "workspace_read", "depends_on": ["ghost"]}],
    )
    with pytest.raises(ValidationError, match="Rule 6"):
        validate(ir)


def test_rule6_fail_edge_unknown_node() -> None:
    ir = _ir(
        nodes=[{"id": "a", "kind": "workspace_read"}],
        edges=[{"from_node": "a", "to_node": "nonexistent"}],
    )
    with pytest.raises(ValidationError, match="Rule 6"):
        validate(ir)


# ---------------------------------------------------------------------------
# Rule 7 — human_approval node required when flag is set
# ---------------------------------------------------------------------------


def test_rule7_pass_flag_set_with_gate() -> None:
    ir = _ir(
        nodes=[
            {"id": "n1", "kind": "workspace_read"},
            {"id": "gate", "kind": "human_approval"},
        ],
        policies={"max_cost_usd": 10.0, "allowed_skills": [], "requires_human_approval": True},
    )
    validate(ir)


def test_rule7_fail_flag_set_no_gate() -> None:
    ir = _ir(
        nodes=[{"id": "n1", "kind": "workspace_read"}],
        policies={"max_cost_usd": 10.0, "allowed_skills": [], "requires_human_approval": True},
    )
    with pytest.raises(ValidationError, match="Rule 7"):
        validate(ir)


def test_rule7_pass_flag_not_set_no_gate() -> None:
    ir = _ir(
        nodes=[{"id": "n1", "kind": "workspace_read"}],
        policies={"max_cost_usd": 10.0, "allowed_skills": [], "requires_human_approval": False},
    )
    validate(ir)  # must not raise
