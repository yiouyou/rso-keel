"""Workflow IR v1 Pydantic schema.

v1 locks exactly 6 node kinds and 6 condition fields as a minimal safety core
for accountable knowledge workflows. This is not a universal workflow ontology:
extensions require a schema_version bump.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enumerations (Literal unions so Pydantic validates at parse time)
# ---------------------------------------------------------------------------

NodeKind = Literal[
    "workspace_read",
    "literature_search",
    "independent_critic",
    "synthesis",
    "human_approval",
    "report_write",
]

ConditionField = Literal[
    "evidence_level",
    "confidence_tier",
    "requires_human_review",
    "safety_ethics_flags",
    "opportunity_rank_tier",
    "next_decision",
]

NetworkAccess = Literal["verified_sources_only", "none"]

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class IRNode(BaseModel):
    id: str
    kind: NodeKind
    depends_on: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    budget: dict[str, Any] | None = None


class IREdge(BaseModel):
    from_node: str
    to_node: str


class ConditionalEdge(BaseModel):
    from_node: str
    condition_field: ConditionField
    condition_value: str | bool
    to_node: str


class Policies(BaseModel):
    # --- governance floor (always on, cannot be disabled) ---
    provenance_enabled: Literal[True] = True
    max_cost_usd: float
    allowed_skills: list[str]
    network_access: NetworkAccess = "verified_sources_only"

    # --- tunable (optional with defaults) ---
    max_subagents: int = 4
    max_iterations: int = 10
    requires_human_approval: bool = False
    critic_count: int = 1
    source_breadth: str = "standard"
    convergence_thresholds: dict[str, Any] = Field(default_factory=dict)
    # Cost rates for the post-run cost guard (USD per 1k tokens).
    # Use per-direction fields for accuracy; cost_per_1k_tokens is a legacy
    # flat-rate fallback used only when both directional fields are zero.
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    cost_per_1k_tokens: float = 0.003  # legacy flat-rate fallback


# ---------------------------------------------------------------------------
# Top-level IR
# ---------------------------------------------------------------------------


class WorkflowIR(BaseModel):
    schema_version: str
    objective: str
    nodes: list[IRNode]
    edges: list[IREdge] = Field(default_factory=list)
    conditional_edges: list[ConditionalEdge] = Field(default_factory=list)
    policies: Policies
