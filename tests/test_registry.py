from __future__ import annotations

import ast
from pathlib import Path

from keel.registry import (
    GovernanceArchive,
    GovernanceRecord,
    SkillRegistry,
    SkillSpec,
)


def make_skill(
    skill_id: str = "literature_search_v1",
    supported_node_kinds: list[str] | None = None,
    version: str = "1.0.0",
) -> SkillSpec:
    return SkillSpec(
        skill_id=skill_id,
        version=version,
        description=f"{skill_id} description",
        supported_node_kinds=supported_node_kinds or ["literature_search"],
        cost_estimate_usd=0.25,
        tags=["test"],
        metadata={"owner": "keel"},
    )


def make_policies() -> dict[str, object]:
    return {
        "provenance_enabled": True,
        "max_cost_usd": 10.0,
        "allowed_skills": ["literature_search_v1"],
        "network_access": "verified_sources_only",
        "requires_human_approval": True,
        "critic_count": 2,
        "source_breadth": "broad",
    }


def make_record(plan_id: str = "plan-1") -> GovernanceRecord:
    return GovernanceRecord.from_policies(plan_id, make_policies())


def test_register_and_get() -> None:
    registry = SkillRegistry()
    spec = make_skill()

    registry.register(spec)

    assert registry.get("literature_search_v1") == spec


def test_get_unknown_returns_none() -> None:
    assert SkillRegistry().get("nonexistent") is None


def test_register_overwrites() -> None:
    registry = SkillRegistry()
    first = make_skill(version="1.0.0")
    second = make_skill(version="2.0.0")

    registry.register(first)
    registry.register(second)

    assert registry.get("literature_search_v1") == second


def test_all_skill_ids_sorted() -> None:
    registry = SkillRegistry()
    for skill_id in ["zeta", "alpha", "middle"]:
        registry.register(make_skill(skill_id=skill_id))

    assert registry.all_skill_ids() == ["alpha", "middle", "zeta"]


def test_skills_for_node_kind_filters() -> None:
    registry = SkillRegistry()
    literature = make_skill(
        skill_id="literature", supported_node_kinds=["literature_search"]
    )
    synthesis = make_skill(skill_id="synthesis", supported_node_kinds=["synthesis"])
    both = make_skill(
        skill_id="both", supported_node_kinds=["literature_search", "synthesis"]
    )
    registry.register(literature)
    registry.register(synthesis)
    registry.register(both)

    assert registry.skills_for_node_kind("literature_search") == [both, literature]


def test_skills_for_node_kind_sorted() -> None:
    registry = SkillRegistry()
    for skill_id in ["zeta", "alpha", "middle"]:
        registry.register(
            make_skill(skill_id=skill_id, supported_node_kinds=["report_write"])
        )

    skills = registry.skills_for_node_kind("report_write")

    assert [s.skill_id for s in skills] == ["alpha", "middle", "zeta"]


def test_validate_allowed_skills_all_registered() -> None:
    registry = SkillRegistry()
    registry.register(make_skill(skill_id="alpha"))
    registry.register(make_skill(skill_id="beta"))

    assert registry.validate_allowed_skills(["alpha", "beta"]) == []


def test_validate_allowed_skills_missing() -> None:
    registry = SkillRegistry()
    registry.register(make_skill(skill_id="alpha"))

    assert registry.validate_allowed_skills(["alpha", "missing"]) == ["missing"]


def test_registry_starts_empty() -> None:
    assert SkillRegistry().all_skill_ids() == []


def test_skill_spec_round_trip() -> None:
    spec = make_skill()

    restored = SkillSpec.model_validate_json(spec.model_dump_json())

    assert restored == spec


def test_from_policies_captures_floor() -> None:
    record = GovernanceRecord.from_policies("plan-1", make_policies())

    assert record.provenance_enabled is True
    assert record.max_cost_usd == 10.0
    assert record.allowed_skills == ["literature_search_v1"]
    assert record.network_access == "verified_sources_only"


def test_from_policies_captures_tunable() -> None:
    record = GovernanceRecord.from_policies("plan-1", make_policies())

    assert record.requires_human_approval is True
    assert record.critic_count == 2
    assert record.source_breadth == "broad"


def test_from_policies_extra_fields() -> None:
    policies = make_policies()
    policies["max_iterations"] = 10
    policies["convergence_thresholds"] = {"confidence": 0.85}

    record = GovernanceRecord.from_policies("plan-1", policies)

    assert record.extra == {
        "max_iterations": 10,
        "convergence_thresholds": {"confidence": 0.85},
    }


def test_governance_record_immutable_floor() -> None:
    policies = make_policies()
    policies["provenance_enabled"] = False

    record = GovernanceRecord.from_policies("plan-1", policies)

    assert record.provenance_enabled is True


def test_governance_record_round_trip() -> None:
    record = make_record()

    restored = GovernanceRecord.model_validate_json(record.model_dump_json())

    assert restored == record


def test_governance_record_recorded_at_set() -> None:
    assert make_record().recorded_at is not None


def test_archive_record_and_get() -> None:
    archive = GovernanceArchive()
    record = make_record()

    archive.record(record)

    assert archive.get("plan-1") == record


def test_archive_get_unknown() -> None:
    assert GovernanceArchive().get("nonexistent") is None


def test_archive_get_returns_latest() -> None:
    archive = GovernanceArchive()
    first = make_record("plan-1")
    second = GovernanceRecord.from_policies(
        "plan-1", {**make_policies(), "max_cost_usd": 20.0}
    )

    archive.record(first)
    archive.record(second)

    assert archive.get("plan-1") == second


def test_archive_all() -> None:
    archive = GovernanceArchive()
    records = [make_record(f"plan-{i}") for i in range(3)]
    for record in records:
        archive.record(record)

    assert archive.all() == records


def test_archive_len() -> None:
    archive = GovernanceArchive()
    archive.record(make_record("plan-1"))
    archive.record(make_record("plan-2"))

    assert len(archive) == 2


def test_archive_starts_empty() -> None:
    assert len(GovernanceArchive()) == 0


def test_no_platform_imports_in_registry() -> None:
    registry_dir = Path(__file__).resolve().parents[1] / "src" / "keel" / "registry"
    forbidden_roots = {"app", "backend"}

    for path in registry_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".", 1)[0] not in forbidden_roots
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                assert node.module.split(".", 1)[0] not in forbidden_roots
