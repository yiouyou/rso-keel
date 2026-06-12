"""Execution policy preflight and runtime cost guard helpers.

This module is intentionally platform-free. RSO can call it from the bridge
layer, while the core package remains unaware of users, projects, billing, or
TaskJob persistence.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from keel.convergence.protocol import ConvergenceResult
from keel.ir.schema import WorkflowIR


class PolicyPreflightReport(BaseModel):
    """Structured snapshot of the policy checks performed before execution."""

    passed: bool
    max_cost_usd: float
    estimated_node_cost_usd: float
    allowed_skills: list[str] = Field(default_factory=list)
    network_access: str
    requires_human_approval: bool
    critic_count: int
    issue_codes: list[str] = Field(default_factory=list)
    validation_error: str | None = None


class RuntimeCostSnapshot(BaseModel):
    """Runtime cost estimate from node outputs and IR policy rates."""

    tokens_in: int
    tokens_out: int
    approx_cost_usd: float
    max_cost_usd: float
    exceeded: bool
    warning: str | None = None


def build_policy_preflight_report(
    ir: WorkflowIR,
    *,
    deterministic: ConvergenceResult | None = None,
    rules: ConvergenceResult | None = None,
    validation_error: str | None = None,
) -> PolicyPreflightReport:
    """Build a serializable preflight report from validation/gate results."""
    issue_codes: list[str] = []
    if validation_error:
        issue_codes.append("IR_VALIDATION_FAILED")
    for result in (deterministic, rules):
        if result is not None:
            issue_codes.extend(result.issue_codes)

    return PolicyPreflightReport(
        passed=validation_error is None
        and (deterministic.passed if deterministic is not None else True)
        and (rules.passed if rules is not None else True),
        max_cost_usd=ir.policies.max_cost_usd,
        estimated_node_cost_usd=_estimated_node_cost_usd(ir),
        allowed_skills=list(ir.policies.allowed_skills),
        network_access=ir.policies.network_access,
        requires_human_approval=ir.policies.requires_human_approval,
        critic_count=ir.policies.critic_count,
        issue_codes=issue_codes,
        validation_error=validation_error,
    )


class RuntimeCostGuard:
    """Estimate runtime cost from completed node outputs."""

    def check_state(self, ir: WorkflowIR, state: dict[str, Any]) -> RuntimeCostSnapshot:
        node_outputs = state.get("node_outputs")
        tokens_in = 0
        tokens_out = 0
        if isinstance(node_outputs, dict):
            for value in node_outputs.values():
                if isinstance(value, dict):
                    tokens_in += _coerce_int(value.get("tokens_in"))
                    tokens_out += _coerce_int(value.get("tokens_out"))

        approx_cost_usd = self.estimate_cost_usd(
            ir,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
        exceeded = approx_cost_usd > ir.policies.max_cost_usd
        warning = None
        if exceeded:
            warning = (
                f"Approximate cost {approx_cost_usd:.3f} USD exceeded "
                f"max_cost_usd {ir.policies.max_cost_usd:.2f} USD"
            )
        return RuntimeCostSnapshot(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            approx_cost_usd=approx_cost_usd,
            max_cost_usd=ir.policies.max_cost_usd,
            exceeded=exceeded,
            warning=warning,
        )

    def estimate_cost_usd(
        self,
        ir: WorkflowIR,
        *,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        """Estimate USD cost using per-direction rates when available."""
        if ir.policies.cost_per_1k_input or ir.policies.cost_per_1k_output:
            return (
                tokens_in / 1000.0 * ir.policies.cost_per_1k_input
                + tokens_out / 1000.0 * ir.policies.cost_per_1k_output
            )
        return (
            (tokens_in + tokens_out)
            / 1000.0
            * ir.policies.cost_per_1k_tokens
        )


def _estimated_node_cost_usd(ir: WorkflowIR) -> float:
    total = 0.0
    for node in ir.nodes:
        if node.budget is not None and "cost_usd" in node.budget:
            total += float(node.budget["cost_usd"])
    return total


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return 0
