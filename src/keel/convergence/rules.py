from __future__ import annotations

from typing import Any

from keel.convergence.protocol import ConvergenceIssue, ConvergenceResult
from keel.ir.schema import WorkflowIR


class RulesGate:
    """Check policy and budget rules for a WorkflowIR."""

    layer = "rules"

    def check(self, ir: WorkflowIR, state: dict[str, Any] | None = None) -> ConvergenceResult:
        issues: list[ConvergenceIssue] = []

        total_cost = 0.0
        for node in ir.nodes:
            if node.budget is not None and "cost_usd" in node.budget:
                total_cost += float(node.budget["cost_usd"])

        if total_cost > ir.policies.max_cost_usd:
            issues.append(
                ConvergenceIssue(
                    code="COST_CEILING_EXCEEDED",
                    message=(
                        f"Estimated node cost {total_cost:.2f} USD exceeds "
                        f"max_cost_usd {ir.policies.max_cost_usd:.2f}"
                    ),
                    layer=self.layer,
                    suggestion="Reduce node budgets or raise max_cost_usd in policies",
                )
            )

        for node in ir.nodes:
            skill = node.inputs.get("skill")
            if skill is not None and skill not in ir.policies.allowed_skills:
                issues.append(
                    ConvergenceIssue(
                        code="FORBIDDEN_SKILL",
                        message=(
                            f"Node '{node.id}' uses skill '{skill}' not in allowed_skills"
                        ),
                        layer=self.layer,
                        suggestion=(
                            f"Add '{skill}' to policies.allowed_skills or remove it "
                            "from the node"
                        ),
                    )
                )

        literature_search_count = sum(
            1 for node in ir.nodes if node.kind == "literature_search"
        )
        if ir.policies.source_breadth == "narrow" and literature_search_count > 2:
            issues.append(
                ConvergenceIssue(
                    code="SOURCE_BREADTH_VIOLATION",
                    message=(
                        "source_breadth is 'narrow' but "
                        f"{literature_search_count} literature_search nodes found (max 2)"
                    ),
                    layer=self.layer,
                    suggestion="Reduce literature_search nodes or set source_breadth to 'standard'",
                )
            )

        critic_count = sum(1 for node in ir.nodes if node.kind == "independent_critic")
        if critic_count != ir.policies.critic_count:
            issues.append(
                ConvergenceIssue(
                    code="CRITIC_COUNT_MISMATCH",
                    message=(
                        f"Expected {ir.policies.critic_count} independent_critic node(s) "
                        f"but found {critic_count}"
                    ),
                    layer=self.layer,
                    suggestion=(
                        "Adjust critic_count in policies or add/remove independent_critic nodes"
                    ),
                )
            )

        return ConvergenceResult(
            passed=len(issues) == 0,
            layer=self.layer,
            issues=issues,
        )
