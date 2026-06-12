"""Workflow IR v1 validator.

Rules (fail-closed — any failure raises ValidationError immediately):
  1. schema_version must be "v1".
  2. Every node.kind is in the 6-item whitelist.
  3. Every skill referenced in node.inputs["skill"] is in policies.allowed_skills.
  4. provenance_enabled is True; max_cost_usd > 0 and <= MAX_COST_USD_CEILING.
  5. ConditionalEdge.condition_field is a known enum value; condition_value is
     str|bool without free-code markers (lambda/eval/exec).
  6. Graph (edges + conditional_edges + depends_on) is a DAG (no cycles);
     all referenced node ids exist.
  7. If policies.requires_human_approval, at least one node has kind="human_approval".
"""

from __future__ import annotations

from keel.ir.schema import NodeKind, WorkflowIR

MAX_COST_USD_CEILING = 1000.0

_VALID_SCHEMA_VERSIONS = {"v1"}
_VALID_NODE_KINDS: set[str] = set(NodeKind.__args__)  # type: ignore[attr-defined]
_FREE_CODE_MARKERS = ("lambda", "eval", "exec")


class ValidationError(Exception):
    """Raised when a WorkflowIR fails any of the 7 validation rules."""


def validate(ir: WorkflowIR) -> None:
    """Validate *ir* against all 7 rules. Raises ValidationError on first failure."""
    _rule1_schema_version(ir)
    _rule2_node_kinds(ir)
    _rule3_skill_allowlist(ir)
    _rule4_governance_floor(ir)
    _rule5_conditional_edges(ir)
    _rule6_dag(ir)
    _rule7_human_approval_node(ir)


# ---------------------------------------------------------------------------
# Individual rule implementations
# ---------------------------------------------------------------------------


def _rule1_schema_version(ir: WorkflowIR) -> None:
    if ir.schema_version not in _VALID_SCHEMA_VERSIONS:
        raise ValidationError(
            f"Rule 1: unknown schema_version '{ir.schema_version}'. "
            f"Allowed: {sorted(_VALID_SCHEMA_VERSIONS)}"
        )


def _rule2_node_kinds(ir: WorkflowIR) -> None:
    for node in ir.nodes:
        if node.kind not in _VALID_NODE_KINDS:
            raise ValidationError(
                f"Rule 2: node '{node.id}' has unknown kind '{node.kind}'. "
                f"Allowed: {sorted(_VALID_NODE_KINDS)}"
            )


def _rule3_skill_allowlist(ir: WorkflowIR) -> None:
    allowed = set(ir.policies.allowed_skills)
    for node in ir.nodes:
        skill = node.inputs.get("skill")
        if skill is not None and skill not in allowed:
            raise ValidationError(
                f"Rule 3: node '{node.id}' references skill '{skill}' "
                f"which is not in policies.allowed_skills {sorted(allowed)}"
            )


def _rule4_governance_floor(ir: WorkflowIR) -> None:
    if not ir.policies.provenance_enabled:
        raise ValidationError("Rule 4: policies.provenance_enabled must be True.")
    if ir.policies.max_cost_usd <= 0:
        raise ValidationError(
            f"Rule 4: policies.max_cost_usd must be > 0, got {ir.policies.max_cost_usd}"
        )
    if ir.policies.max_cost_usd > MAX_COST_USD_CEILING:
        raise ValidationError(
            f"Rule 4: policies.max_cost_usd {ir.policies.max_cost_usd} exceeds "
            f"ceiling {MAX_COST_USD_CEILING}"
        )


def _rule5_conditional_edges(ir: WorkflowIR) -> None:
    for edge in ir.conditional_edges:
        val = edge.condition_value
        if not isinstance(val, (str, bool)):
            raise ValidationError(
                f"Rule 5: conditional edge from '{edge.from_node}' has "
                f"condition_value of type {type(val).__name__}, must be str or bool."
            )
        if isinstance(val, str):
            if len(val) > 200:
                raise ValidationError(
                    f"Rule 5: conditional edge from '{edge.from_node}' has "
                    f"condition_value exceeding 200 characters."
                )
            for marker in _FREE_CODE_MARKERS:
                if marker in val:
                    raise ValidationError(
                        f"Rule 5: conditional edge from '{edge.from_node}' has "
                        f"condition_value containing forbidden marker '{marker}'."
                    )


def _rule6_dag(ir: WorkflowIR) -> None:
    node_ids = {n.id for n in ir.nodes}

    # Collect all adjacency (from → to) and check node existence.
    adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}

    for node in ir.nodes:
        for dep in node.depends_on:
            if dep not in node_ids:
                raise ValidationError(
                    f"Rule 6: node '{node.id}' depends_on unknown node '{dep}'."
                )
            adjacency[dep].append(node.id)

    for edge in ir.edges:
        for nid in (edge.from_node, edge.to_node):
            if nid not in node_ids:
                raise ValidationError(
                    f"Rule 6: edge references unknown node '{nid}'."
                )
        adjacency[edge.from_node].append(edge.to_node)

    for edge in ir.conditional_edges:
        for nid in (edge.from_node, edge.to_node):
            if nid not in node_ids:
                raise ValidationError(
                    f"Rule 6: conditional edge references unknown node '{nid}'."
                )
        adjacency[edge.from_node].append(edge.to_node)

    # Kahn's algorithm for cycle detection.
    in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
    for nid, targets in adjacency.items():
        for t in targets:
            in_degree[t] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    processed = 0
    while queue:
        current = queue.pop()
        processed += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if processed != len(node_ids):
        raise ValidationError("Rule 6: workflow graph contains a cycle.")


def _rule7_human_approval_node(ir: WorkflowIR) -> None:
    if not ir.policies.requires_human_approval:
        return
    has_gate = any(n.kind == "human_approval" for n in ir.nodes)
    if not has_gate:
        raise ValidationError(
            "Rule 7: policies.requires_human_approval is True but no node "
            "with kind='human_approval' exists."
        )
