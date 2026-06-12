from __future__ import annotations

from keel.templates.schema import TemplateSpec, TemplateStatus


class TemplateRegistry:
    """Versioned template store.

    Keyed by (template_id, version). Multiple versions of the same template_id
    can coexist. Historical job runs reference content_hash so they are always
    traceable to the exact template used, even after deprecation.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], TemplateSpec] = {}

    def register(self, spec: TemplateSpec) -> None:
        """Register a template version. Raises ValueError if already registered."""
        key = (spec.template_id, spec.version)
        if key in self._store:
            raise ValueError(
                f"Template '{spec.template_id}' v{spec.version} already registered. "
                "Create a new version instead of overwriting."
            )
        self._store[key] = spec

    def get(self, template_id: str, version: str) -> TemplateSpec | None:
        return self._store.get((template_id, version))

    def get_by_hash(self, content_hash: str) -> TemplateSpec | None:
        """Look up a template by content_hash - enables historical traceability."""
        for spec in self._store.values():
            if spec.content_hash == content_hash:
                return spec
        return None

    def versions(self, template_id: str) -> list[TemplateSpec]:
        """Return all versions of template_id, sorted by version string."""
        results = [s for (tid, _), s in self._store.items() if tid == template_id]
        return sorted(results, key=lambda s: s.version)

    def by_status(self, status: TemplateStatus) -> list[TemplateSpec]:
        """Return all templates with the given status, sorted by (template_id, version)."""
        return sorted(
            [s for s in self._store.values() if s.status == status],
            key=lambda s: (s.template_id, s.version),
        )

    def update(self, spec: TemplateSpec) -> None:
        """Overwrite an existing registration (for approve/deprecate transitions)."""
        key = (spec.template_id, spec.version)
        if key not in self._store:
            raise ValueError(f"Template '{spec.template_id}' v{spec.version} not registered.")
        self._store[key] = spec

    def __len__(self) -> int:
        return len(self._store)
