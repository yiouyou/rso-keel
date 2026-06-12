"""M6 convergence gate tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from keel.convergence import (
    ConvergenceGate,
    ConvergenceIssue,
    ConvergenceResult,
    DeterministicGate,
    RulesGate,
)
from keel.ir.schema import Policies, WorkflowIR


def _policies(**overrides: Any) -> Policies:
    defaults: dict[str, Any] = {"max_cost_usd": 10.0, "allowed_skills": ["skill_a"]}
    defaults.update(overrides)
    return Policies(**defaults)


def _ir(**overrides: Any) -> WorkflowIR:
    base: dict[str, Any] = {
        "schema_version": "v1",
        "objective": "Test convergence",
        "nodes": [{"id": "n1", "kind": "workspace_read"}],
        "edges": [],
        "conditional_edges": [],
        "policies": _policies().model_dump(),
    }
    base.update(overrides)
    return WorkflowIR.model_validate(base)


def test_deterministic_gate_satisfies_protocol() -> None:
    assert isinstance(DeterministicGate(), ConvergenceGate)


def test_rules_gate_satisfies_protocol() -> None:
    assert isinstance(RulesGate(), ConvergenceGate)


def test_convergence_result_issue_codes() -> None:
    result = ConvergenceResult(
        passed=False,
        layer="rules",
        issues=[
            ConvergenceIssue(code="FIRST", message="First issue", layer="rules"),
            ConvergenceIssue(code="SECOND", message="Second issue", layer="rules"),
        ],
    )

    assert result.issue_codes == ["FIRST", "SECOND"]


def test_convergence_result_passed_false_when_issues() -> None:
    result = ConvergenceResult(
        passed=False,
        layer="deterministic",
        issues=[
            ConvergenceIssue(
                code="NO_DATA_SOURCE",
                message="No data source",
                layer="deterministic",
            )
        ],
    )

    assert result.passed is False


def test_deterministic_pass_has_data_source() -> None:
    result = DeterministicGate().check(_ir())

    assert result.passed is True
    assert result.issue_codes == []


def test_deterministic_fail_no_data_source() -> None:
    result = DeterministicGate().check(_ir(nodes=[{"id": "n1", "kind": "synthesis"}]))

    assert result.passed is False
    assert "NO_DATA_SOURCE" in result.issue_codes


def test_deterministic_fail_network_conflict() -> None:
    result = DeterministicGate().check(
        _ir(
            nodes=[{"id": "n1", "kind": "literature_search"}],
            policies=_policies(network_access="none").model_dump(),
        )
    )

    assert result.passed is False
    assert "NETWORK_ACCESS_CONFLICT" in result.issue_codes


def test_deterministic_pass_network_none_no_search() -> None:
    result = DeterministicGate().check(
        _ir(policies=_policies(network_access="none").model_dump())
    )

    assert result.passed is True


def test_deterministic_fail_missing_human_gate() -> None:
    result = DeterministicGate().check(
        _ir(policies=_policies(requires_human_approval=True).model_dump())
    )

    assert result.passed is False
    assert "MISSING_HUMAN_GATE" in result.issue_codes


def test_deterministic_pass_human_gate_present() -> None:
    result = DeterministicGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "approve", "kind": "human_approval"},
            ],
            policies=_policies(requires_human_approval=True).model_dump(),
        )
    )

    assert result.passed is True


def test_deterministic_fail_dangling_edge() -> None:
    result = DeterministicGate().check(
        _ir(edges=[{"from_node": "n1", "to_node": "missing"}])
    )

    assert result.passed is False
    assert "DANGLING_EDGE" in result.issue_codes


def test_deterministic_collects_all_issues() -> None:
    result = DeterministicGate().check(
        _ir(
            nodes=[{"id": "n1", "kind": "literature_search"}],
            edges=[{"from_node": "n1", "to_node": "missing"}],
            policies=_policies(network_access="none").model_dump(),
        )
    )

    assert result.passed is False
    assert "NETWORK_ACCESS_CONFLICT" in result.issue_codes
    assert "DANGLING_EDGE" in result.issue_codes


def test_rules_pass_within_budget() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read", "budget": {"cost_usd": 2.0}},
                {"id": "critic", "kind": "independent_critic", "budget": {"cost_usd": 3.0}},
            ]
        )
    )

    assert result.passed is True


def test_rules_fail_budget_exceeded() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read", "budget": {"cost_usd": 8.0}},
                {"id": "critic", "kind": "independent_critic", "budget": {"cost_usd": 3.0}},
            ]
        )
    )

    assert result.passed is False
    assert "COST_CEILING_EXCEEDED" in result.issue_codes


def test_rules_pass_no_budgets() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "critic", "kind": "independent_critic"},
            ]
        )
    )

    assert result.passed is True


def test_rules_fail_forbidden_skill() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "critic", "kind": "independent_critic", "inputs": {"skill": "skill_b"}},
            ]
        )
    )

    assert result.passed is False
    assert "FORBIDDEN_SKILL" in result.issue_codes


def test_rules_pass_allowed_skill() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "critic", "kind": "independent_critic", "inputs": {"skill": "skill_a"}},
            ]
        )
    )

    assert result.passed is True


def test_rules_fail_source_breadth() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "search_1", "kind": "literature_search"},
                {"id": "search_2", "kind": "literature_search"},
                {"id": "search_3", "kind": "literature_search"},
                {"id": "critic", "kind": "independent_critic"},
            ],
            policies=_policies(source_breadth="narrow").model_dump(),
        )
    )

    assert result.passed is False
    assert "SOURCE_BREADTH_VIOLATION" in result.issue_codes


def test_rules_fail_critic_count() -> None:
    result = RulesGate().check(
        _ir(
            nodes=[
                {"id": "read", "kind": "workspace_read"},
                {"id": "critic", "kind": "independent_critic"},
            ],
            policies=_policies(critic_count=2).model_dump(),
        )
    )

    assert result.passed is False
    assert "CRITIC_COUNT_MISMATCH" in result.issue_codes


def test_rules_pass_critic_count_zero() -> None:
    result = RulesGate().check(
        _ir(policies=_policies(critic_count=0).model_dump())
    )

    assert result.passed is True


def test_no_platform_imports_in_convergence() -> None:
    convergence_dir = Path(__file__).parent.parent / "src" / "keel" / "convergence"
    imported_modules: list[str] = []

    for source_path in sorted(convergence_dir.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

    assert not any(name == "app" or name.startswith("app.") for name in imported_modules)
    assert not any(name == "backend" or name.startswith("backend.") for name in imported_modules)
