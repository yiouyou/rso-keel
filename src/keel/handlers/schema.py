"""Platform-free handler output contract for Keel node handlers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GeneratedFileRef(BaseModel):
    """Reference to a generated artifact visible to the host platform."""

    model_config = ConfigDict(extra="forbid")

    path: str
    size: int | None = None
    content_hash: str | None = None
    modified_at: str | None = None


class ModelUsage(BaseModel):
    """Model usage reported by one handler invocation."""

    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    provider_cost_cny: Decimal | None = None
    charged_cost_cny: Decimal | None = None


class HandlerOutput(BaseModel):
    """Canonical output emitted by platform handlers into Keel state."""

    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    generated_files: list[GeneratedFileRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_step: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    model_usage: list[ModelUsage] = Field(default_factory=list)
    output_digest: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
