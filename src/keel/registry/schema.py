from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from keel.ir.schema import NodeKind


class SkillSpec(BaseModel):
    """Describes one registered capability that nodes can invoke."""

    skill_id: str
    version: str
    description: str = ""
    supported_node_kinds: list[NodeKind]
    cost_estimate_usd: float = 0.0
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    """In-memory registry of available skills.

    keel provides the mechanism; RSO registers actual science-source skills
    by calling register(). Plans can only reference skills present in the registry.
    """

    def __init__(self) -> None:
        self._skills: dict[str, SkillSpec] = {}

    def register(self, spec: SkillSpec) -> None:
        """Register a skill. Re-registering the same skill_id overwrites."""
        self._skills[spec.skill_id] = spec

    def get(self, skill_id: str) -> SkillSpec | None:
        """Return the SkillSpec for skill_id, or None if not registered."""
        return self._skills.get(skill_id)

    def all_skill_ids(self) -> list[str]:
        """Return sorted list of all registered skill_ids."""
        return sorted(self._skills.keys())

    def skills_for_node_kind(self, kind: NodeKind) -> list[SkillSpec]:
        """Return all skills that support the given node kind, sorted by skill_id."""
        return sorted(
            [s for s in self._skills.values() if kind in s.supported_node_kinds],
            key=lambda s: s.skill_id,
        )

    def validate_allowed_skills(self, allowed_skills: list[str]) -> list[str]:
        """Return skill_ids in allowed_skills that are not registered."""
        return [sid for sid in allowed_skills if sid not in self._skills]
