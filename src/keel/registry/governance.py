from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class GovernanceRecord(BaseModel):
    """Immutable snapshot of governance state for one plan run.

    Records which policies were active, which skills were allowed,
    and the floor fields that cannot be disabled.
    Governance floor fields (provenance_enabled, max_cost_usd,
    allowed_skills, network_access) are always captured.
    """

    plan_id: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    provenance_enabled: bool
    max_cost_usd: float
    allowed_skills: list[str]
    network_access: str

    requires_human_approval: bool
    critic_count: int
    source_breadth: str

    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_policies(
        cls, plan_id: str, policies_dict: dict[str, Any]
    ) -> GovernanceRecord:
        """Create a GovernanceRecord from a serialised Policies dict."""
        return cls(
            plan_id=plan_id,
            provenance_enabled=True,
            max_cost_usd=policies_dict["max_cost_usd"],
            allowed_skills=policies_dict.get("allowed_skills", []),
            network_access=policies_dict.get(
                "network_access", "verified_sources_only"
            ),
            requires_human_approval=policies_dict.get(
                "requires_human_approval", False
            ),
            critic_count=policies_dict.get("critic_count", 1),
            source_breadth=policies_dict.get("source_breadth", "standard"),
            extra={
                k: v
                for k, v in policies_dict.items()
                if k
                not in {
                    "provenance_enabled",
                    "max_cost_usd",
                    "allowed_skills",
                    "network_access",
                    "requires_human_approval",
                    "critic_count",
                    "source_breadth",
                }
            },
        )


class GovernanceArchive:
    """In-memory archive of GovernanceRecords (one per plan run).

    Production RSO replaces this with a DB-backed implementation.
    keel ships only the in-memory version for tests and standalone use.
    """

    def __init__(self) -> None:
        self._records: list[GovernanceRecord] = []

    def record(self, entry: GovernanceRecord) -> None:
        self._records.append(entry)

    def get(self, plan_id: str) -> GovernanceRecord | None:
        for r in reversed(self._records):
            if r.plan_id == plan_id:
                return r
        return None

    def all(self) -> list[GovernanceRecord]:
        return list(self._records)

    def __len__(self) -> int:
        return len(self._records)
