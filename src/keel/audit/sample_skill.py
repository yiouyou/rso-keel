"""Sample Type 2 skill that emits a structured audit trace."""

from __future__ import annotations

from typing import Any

from keel.audit.schema import AuditTrace, IntermediateSignal, SignalType, SkillResponse


class IndependentCriticSkill:
    SKILL_ID = "independent_critic_v1"
    SKILL_VERSION = "0.1.0"

    def run(self, inputs: dict[str, Any]) -> SkillResponse:
        text = inputs.get("text", "")
        claim = inputs.get("claim", "")

        signals = [
            IntermediateSignal(
                step=1,
                signal_type=SignalType.extraction,
                content=f"Extracted claim: {claim}",
                confidence=0.9,
            ),
            IntermediateSignal(
                step=2,
                signal_type=SignalType.critique,
                content="Checked claim against text",
                confidence=0.7,
            ),
        ]

        issues = []
        if claim and claim not in text:
            issues.append(f"Claim '{claim}' not found verbatim in text")

        suggested = [
            "Verify claim against cited sources",
            "Run independent replication experiment",
        ] if issues else []

        trace = AuditTrace(
            skill_id=self.SKILL_ID,
            skill_version=self.SKILL_VERSION,
            reasoning_steps=2,
            intermediate_signals=signals,
            issues_found=issues,
            suggested_experiments=suggested,
            raw_model_calls=0,
            model_usage=[],
        )

        return SkillResponse(
            ok=len(issues) == 0,
            result={"claim": claim, "issues_count": len(issues)},
            audit_trace=trace,
        )
