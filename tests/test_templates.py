from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from keel.templates import TemplateRegistry, TemplateSpec


def _spec(
    template_id: str = "paper_review_standard",
    version: str = "1.0.0",
    *,
    status: str = "draft",
    ir_skeleton: dict[str, object] | None = None,
) -> TemplateSpec:
    return TemplateSpec(
        template_id=template_id,
        version=version,
        status=status,
        ir_skeleton=ir_skeleton or {"nodes": [{"id": "review"}]},
    )


def test_content_hash_computed_on_construction() -> None:
    spec = _spec()

    assert spec.content_hash
    assert len(spec.content_hash) == 64


def test_content_hash_deterministic() -> None:
    first = _spec(ir_skeleton={"b": 2, "a": 1})
    second = _spec(ir_skeleton={"a": 1, "b": 2})

    assert first.content_hash == second.content_hash


def test_content_hash_differs_for_different_skeletons() -> None:
    first = _spec(ir_skeleton={"nodes": ["a"]})
    second = _spec(ir_skeleton={"nodes": ["b"]})

    assert first.content_hash != second.content_hash


def test_approve_returns_approved_copy() -> None:
    original = _spec()
    approved = original.approve()

    assert approved is not original
    assert approved.status == "approved"
    assert approved.approved_at is not None
    assert original.status == "draft"
    assert original.approved_at is None


def test_review_returns_reviewed_copy() -> None:
    original = _spec()
    reviewed = original.review()

    assert reviewed is not original
    assert reviewed.status == "reviewed"
    assert reviewed.reviewed_at is not None
    assert original.status == "draft"
    assert original.reviewed_at is None


def test_deprecate_returns_deprecated_copy() -> None:
    original = _spec()
    deprecated = original.deprecate()

    assert deprecated is not original
    assert deprecated.status == "deprecated"
    assert deprecated.deprecated_at is not None
    assert original.status == "draft"
    assert original.deprecated_at is None


def test_default_status_is_draft() -> None:
    spec = TemplateSpec(
        template_id="paper_review_standard",
        version="1.0.0",
        ir_skeleton={"nodes": []},
    )

    assert spec.status == "draft"


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError):
        _spec(status="published")


def test_template_spec_round_trip() -> None:
    spec = _spec()

    restored = TemplateSpec.model_validate_json(spec.model_dump_json())

    assert restored == spec


def test_content_hash_preserved_on_round_trip() -> None:
    spec = _spec()

    restored = TemplateSpec.model_validate_json(spec.model_dump_json())

    assert restored.content_hash == spec.content_hash


def test_approved_at_none_until_approved() -> None:
    spec = _spec()

    assert spec.approved_at is None


def test_reviewed_at_none_until_reviewed() -> None:
    spec = _spec()

    assert spec.reviewed_at is None


def test_register_and_get() -> None:
    registry = TemplateRegistry()
    spec = _spec()

    registry.register(spec)

    assert registry.get(spec.template_id, spec.version) == spec


def test_get_unknown_returns_none() -> None:
    registry = TemplateRegistry()

    assert registry.get("x", "1.0.0") is None


def test_register_duplicate_raises() -> None:
    registry = TemplateRegistry()
    spec = _spec()

    registry.register(spec)

    with pytest.raises(ValueError):
        registry.register(spec)


def test_get_by_hash() -> None:
    registry = TemplateRegistry()
    spec = _spec()
    registry.register(spec)

    assert registry.get_by_hash(spec.content_hash) == spec


def test_get_by_hash_unknown() -> None:
    registry = TemplateRegistry()

    assert registry.get_by_hash("deadbeef") is None


def test_versions_sorted() -> None:
    registry = TemplateRegistry()
    v2 = _spec(version="2.0.0")
    v1 = _spec(version="1.0.0")
    registry.register(v2)
    registry.register(v1)

    assert registry.versions("paper_review_standard") == [v1, v2]


def test_versions_filters_by_template_id() -> None:
    registry = TemplateRegistry()
    a = _spec(template_id="a")
    b = _spec(template_id="b")
    registry.register(a)
    registry.register(b)

    assert registry.versions("a") == [a]


def test_by_status_approved() -> None:
    registry = TemplateRegistry()
    approved = _spec(template_id="a").approve()
    draft_one = _spec(template_id="b")
    draft_two = _spec(template_id="c")
    registry.register(approved)
    registry.register(draft_one)
    registry.register(draft_two)

    assert registry.by_status("approved") == [approved]


def test_by_status_sorted() -> None:
    registry = TemplateRegistry()
    b = _spec(template_id="b", version="2.0.0")
    a2 = _spec(template_id="a", version="2.0.0")
    a1 = _spec(template_id="a", version="1.0.0")
    registry.register(b)
    registry.register(a2)
    registry.register(a1)

    assert registry.by_status("draft") == [a1, a2, b]


def test_update_approve_workflow() -> None:
    registry = TemplateRegistry()
    draft = _spec()
    registry.register(draft)

    registry.update(draft.approve())

    updated = registry.get(draft.template_id, draft.version)
    assert updated is not None
    assert updated.status == "approved"
    assert updated.approved_at is not None


def test_update_unknown_raises() -> None:
    registry = TemplateRegistry()

    with pytest.raises(ValueError):
        registry.update(_spec())


def test_len() -> None:
    registry = TemplateRegistry()
    registry.register(_spec(template_id="a"))
    registry.register(_spec(template_id="b"))

    assert len(registry) == 2


def test_no_platform_imports_in_templates() -> None:
    template_dir = Path(__file__).parents[1] / "src" / "keel" / "templates"

    for path in template_dir.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported = [node.module]
            else:
                continue

            assert not any(
                name == "app"
                or name.startswith("app.")
                or name == "backend"
                or name.startswith("backend.")
                for name in imported
            )
