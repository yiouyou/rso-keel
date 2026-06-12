from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

TemplateStatus = Literal["draft", "reviewed", "approved", "deprecated"]


class TemplateSpec(BaseModel):
    """A versioned, content-hashed IR skeleton (template).

    content_hash is computed from ir_skeleton on construction and is immutable.
    Once approved, the template cannot be modified - create a new version instead.
    """

    template_id: str
    version: str
    status: TemplateStatus = "draft"
    description: str = ""
    ir_skeleton: dict[str, Any]
    content_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    deprecated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _compute_hash(self) -> TemplateSpec:
        if not self.content_hash:
            canonical = json.dumps(self.ir_skeleton, sort_keys=True, default=str)
            self.content_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self

    def review(self) -> TemplateSpec:
        """Return a new reviewed copy. Original is unchanged."""
        return self.model_copy(
            update={
                "status": "reviewed",
                "reviewed_at": datetime.now(timezone.utc),
            }
        )

    def approve(self) -> TemplateSpec:
        """Return a new approved copy. Original is unchanged (immutable pattern)."""
        return self.model_copy(
            update={
                "status": "approved",
                "approved_at": datetime.now(timezone.utc),
            }
        )

    def deprecate(self) -> TemplateSpec:
        """Return a new deprecated copy."""
        return self.model_copy(
            update={
                "status": "deprecated",
                "deprecated_at": datetime.now(timezone.utc),
            }
        )
