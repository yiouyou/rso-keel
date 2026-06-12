"""LangGraph state schema for compiled Keel workflows."""

from typing import Annotated, Any, TypedDict


def _merge_dicts(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return {**a, **b}


class KeelState(TypedDict, total=False):
    """State shared by WorkflowIR nodes during LangGraph execution."""

    # Annotated with a merge reducer so parallel critic nodes can write
    # their individual outputs concurrently without INVALID_CONCURRENT_GRAPH_UPDATE.
    node_outputs: Annotated[dict[str, Any], _merge_dicts]
    evidence_level: str | None
    confidence_tier: str | None
    requires_human_review: bool
    safety_ethics_flags: bool
    opportunity_rank_tier: str | None
    next_decision: str | None
    pending_approval: dict[str, Any] | None
    error: str | None
