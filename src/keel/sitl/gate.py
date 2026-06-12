"""LangGraph interrupt handler for human approval nodes."""

from __future__ import annotations

from langgraph.types import interrupt

from keel.compiler.state import KeelState
from keel.sitl.schema import ApprovalOutcome, ApprovalRequest, HumanDecision


class HumanGate:
    """Handler for human_approval nodes."""

    def __init__(self, node_id: str, plan_id: str) -> None:
        self.node_id = node_id
        self.plan_id = plan_id

    def __call__(self, state: KeelState) -> KeelState:
        request = ApprovalRequest(
            node_id=self.node_id,
            plan_id=self.plan_id,
            context=dict(state.get("node_outputs") or {}),
        )
        raw_decision = interrupt(request.model_dump())

        decision = HumanDecision.model_validate(raw_decision)
        outcome = ApprovalOutcome(request=request, decision=decision)

        current_outputs = dict(state.get("node_outputs") or {})
        current_outputs[self.node_id] = outcome.model_dump()

        return {
            **state,
            "node_outputs": current_outputs,
            "pending_approval": None,
        }
