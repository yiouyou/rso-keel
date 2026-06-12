from __future__ import annotations

from typing import Any

from keel.convergence.protocol import ConvergenceIssue, ConvergenceResult
from keel.ir.schema import WorkflowIR


class DeterministicGate:
    """Check WorkflowIR structure without external calls or probabilistic inputs."""

    layer = "deterministic"

    def check(self, ir: WorkflowIR, state: dict[str, Any] | None = None) -> ConvergenceResult:
        issues: list[ConvergenceIssue] = []
        node_ids = {node.id for node in ir.nodes}

        if not any(node.kind in {"workspace_read", "literature_search"} for node in ir.nodes):
            issues.append(
                ConvergenceIssue(
                    code="NO_DATA_SOURCE",
                    message="Plan has no data-source node (workspace_read or literature_search)",
                    layer=self.layer,
                    suggestion="Add a workspace_read or literature_search node to ground the plan",
                )
            )

        if ir.policies.network_access == "none" and any(
            node.kind == "literature_search" for node in ir.nodes
        ):
            issues.append(
                ConvergenceIssue(
                    code="NETWORK_ACCESS_CONFLICT",
                    message="literature_search node present but network_access is 'none'",
                    layer=self.layer,
                    suggestion=(
                        "Remove literature_search nodes or set network_access to "
                        "verified_sources_only"
                    ),
                )
            )

        if ir.policies.requires_human_approval and not any(
            node.kind == "human_approval" for node in ir.nodes
        ):
            issues.append(
                ConvergenceIssue(
                    code="MISSING_HUMAN_GATE",
                    message="requires_human_approval is True but no human_approval node found",
                    layer=self.layer,
                    suggestion=(
                        "Add a human_approval node or set requires_human_approval to False"
                    ),
                )
            )

        for edge in ir.edges:
            issues.extend(self._dangling_edge_issues(edge.from_node, edge.to_node, node_ids))
        for edge in ir.conditional_edges:
            issues.extend(self._dangling_edge_issues(edge.from_node, edge.to_node, node_ids))

        return ConvergenceResult(
            passed=len(issues) == 0,
            layer=self.layer,
            issues=issues,
        )

    def _dangling_edge_issues(
        self,
        from_node: str,
        to_node: str,
        node_ids: set[str],
    ) -> list[ConvergenceIssue]:
        issues: list[ConvergenceIssue] = []
        for node_id in (from_node, to_node):
            if node_id not in node_ids:
                issues.append(
                    ConvergenceIssue(
                        code="DANGLING_EDGE",
                        message=f"Edge references unknown node '{node_id}'",
                        layer=self.layer,
                        suggestion="Remove the edge or add the missing node",
                    )
                )
        return issues
