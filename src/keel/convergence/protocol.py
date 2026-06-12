from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from keel.ir.schema import WorkflowIR


class ConvergenceIssue(BaseModel):
    """A single problem found by a convergence gate layer."""

    code: str
    message: str
    layer: str
    suggestion: str = ""


class ConvergenceResult(BaseModel):
    passed: bool
    layer: str
    issues: list[ConvergenceIssue] = Field(default_factory=list)

    @property
    def issue_codes(self) -> list[str]:
        return [issue.code for issue in self.issues]


@runtime_checkable
class ConvergenceGate(Protocol):
    """Contract for all convergence gate layers (deterministic, rules, critic, human)."""

    def check(self, ir: WorkflowIR, state: dict[str, Any] | None = None) -> ConvergenceResult:
        ...
