"""ProvenanceRecorder interface.

keel defines the contract; RSO wires in the concrete implementation
(DB-backed, using the platform's ORM). keel itself only ships NullRecorder
for tests and zero-dependency usage.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from keel.provenance.schema import NodeTrace, PlanProvenance


@runtime_checkable
class ProvenanceRecorder(Protocol):
    """Persist plan lifecycle events.

    Implementations live in the RSO platform layer (app.*) and are injected
    at runtime. keel code accepts a ProvenanceRecorder and calls these methods;
    it never imports a concrete implementation.
    """

    def record_plan_start(self, provenance: PlanProvenance) -> None:
        """Persist the initial provenance record when a plan begins."""
        ...

    def record_node_update(self, plan_id: str, trace: NodeTrace) -> None:
        """Persist an updated NodeTrace (status change, model_usage, audit_trace)."""
        ...

    def record_plan_end(self, provenance: PlanProvenance) -> None:
        """Persist the final provenance record when a plan reaches a terminal state."""
        ...


class NullRecorder:
    """No-op recorder for tests and standalone usage.

    Satisfies the ProvenanceRecorder protocol without any I/O.
    """

    def record_plan_start(self, provenance: PlanProvenance) -> None:
        pass

    def record_node_update(self, plan_id: str, trace: NodeTrace) -> None:
        pass

    def record_plan_end(self, provenance: PlanProvenance) -> None:
        pass
