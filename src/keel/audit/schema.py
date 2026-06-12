"""M5 audit_trace protocol schema."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SignalType(str, Enum):
    reasoning = "reasoning"
    search = "search"
    extraction = "extraction"
    validation = "validation"
    critique = "critique"


class IntermediateSignal(BaseModel):
    step: int
    signal_type: SignalType
    content: str
    confidence: float | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("confidence")
    @classmethod
    def _confidence_range(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @field_validator("step")
    @classmethod
    def _step_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("step must be >= 1")
        return v


class AuditTrace(BaseModel):
    """Structured audit trail for one skill execution.

    Records WHAT the skill did - steps taken, signals, issues found,
    suggested experiments. Does NOT assert truth; true/false is for
    the manuscript / cited literature / humans / experiments.
    """

    skill_id: str
    skill_version: str | None = None
    reasoning_steps: int = 0
    intermediate_signals: list[IntermediateSignal] = Field(default_factory=list)
    issues_found: list[str] = Field(default_factory=list)
    suggested_experiments: list[str] = Field(default_factory=list)
    raw_model_calls: int = 0
    model_usage: list[dict[str, Any]] = Field(default_factory=list)


class SkillResponse(BaseModel):
    """Standard envelope returned by any Type 2 skill."""

    ok: bool
    result: dict[str, Any]
    audit_trace: AuditTrace
