"""Plan lifecycle provenance schema (keel-v1).

Designed to be compatible with the RSO platform's JobProvenance shape so that
the platform layer can merge/extend without conflicts, while remaining
completely free of app.* imports.

Alignment with app/job_payloads.JobProvenance:
  - KeelActor     ↔ JobProvenanceActor   (same field names/types)
  - PlanIntegrity ↔ JobProvenanceIntegrity (same field names/types)
  - model_usage   ↔ JobProvenance.model_usage (same list[dict] shape)
  - schema_version uses "keel-v1" string to avoid int collision with platform's v1
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from keel.audit.schema import AuditTrace
from keel.ir.schema import NodeKind, Policies

# ---------------------------------------------------------------------------
# Shared status literals
# ---------------------------------------------------------------------------

PlanStatus = Literal["pending", "running", "succeeded", "partial", "failed"]
NodeStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]

# ---------------------------------------------------------------------------
# Sub-models (field names mirror JobProvenance sub-models for compatibility)
# ---------------------------------------------------------------------------


class KeelActor(BaseModel):
    """Who triggered this plan.

    Field names intentionally mirror JobProvenanceActor so RSO can pass the
    same actor dict to both models without adaptation.
    """

    user_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    workflow_action_id: str | None = None


class NodeTrace(BaseModel):
    """Execution record for a single IR node within a plan run."""

    node_id: str
    kind: NodeKind
    status: NodeStatus = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    model_usage: list[dict[str, Any]] = Field(default_factory=list)
    audit_trace: AuditTrace | None = None
    error: str | None = None


class PlanIntegrity(BaseModel):
    """Integrity metadata for a plan run.

    Field names mirror JobProvenanceIntegrity for RSO-layer compatibility.
    """

    evidence_levels: list[str] = Field(default_factory=list)
    # human_reviewed replaces review_required (clearer semantics for plan lifecycle)
    human_reviewed: bool = False
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level provenance record
# ---------------------------------------------------------------------------


class PlanProvenance(BaseModel):
    """Full provenance record for one plan execution lifecycle.

    Governance floor (always present, cannot be omitted):
      - schema_version: identifies the keel record format
      - plan_id: unique execution id
      - workflow_ir_hash: content hash of the IR that drove this run
      - config_snapshot: the Policies that were active (config enters provenance)
      - actor, integrity: who/what ran and with what confidence
    """

    schema_version: Literal["keel-v1"] = "keel-v1"

    # Governance floor — all required, no defaults
    plan_id: str
    workflow_ir_hash: str
    ir_schema_version: str
    objective: str
    actor: KeelActor
    config_snapshot: dict[str, Any]  # serialised Policies (config enters provenance)

    # Lifecycle
    status: PlanStatus = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Per-node execution records
    node_traces: list[NodeTrace] = Field(default_factory=list)

    # Aggregated across all nodes — mirrors JobProvenance.model_usage shape
    model_usage: list[dict[str, Any]] = Field(default_factory=list)

    integrity: PlanIntegrity = Field(default_factory=PlanIntegrity)

    @model_validator(mode="after")
    def _floor_fields_non_empty(self) -> PlanProvenance:
        if not self.plan_id.strip():
            raise ValueError("plan_id must not be empty")
        if not self.workflow_ir_hash.strip():
            raise ValueError("workflow_ir_hash must not be empty")
        if not self.ir_schema_version.strip():
            raise ValueError("ir_schema_version must not be empty")
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        return self

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def start(
        cls,
        *,
        plan_id: str,
        ir_json: str,
        ir_schema_version: str,
        objective: str,
        actor: KeelActor,
        policies: Policies,
    ) -> PlanProvenance:
        """Create a fresh provenance record at plan-start time."""
        ir_hash = hashlib.sha256(ir_json.encode()).hexdigest()
        config_snapshot = json.loads(policies.model_dump_json())
        return cls(
            plan_id=plan_id,
            workflow_ir_hash=ir_hash,
            ir_schema_version=ir_schema_version,
            objective=objective,
            actor=actor,
            config_snapshot=config_snapshot,
            status="running",
        )
