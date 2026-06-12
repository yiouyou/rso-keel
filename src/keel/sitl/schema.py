"""Schemas for human approval interrupts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

HumanDecisionValue = Literal["approved", "rejected", "needs_revision"]


class ApprovalRequest(BaseModel):
    """Payload suspended at a human_approval node, waiting for a decision."""

    node_id: str
    plan_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanDecision(BaseModel):
    """The human reviewer's decision on an ApprovalRequest."""

    node_id: str
    plan_id: str
    decision: HumanDecisionValue
    reviewer_id: str | None = None
    notes: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalOutcome(BaseModel):
    """Result written into NodeTrace.audit_trace after human gate resolves."""

    request: ApprovalRequest
    decision: HumanDecision
    human_reviewed: bool = True
