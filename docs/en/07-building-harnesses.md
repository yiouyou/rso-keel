# Building Harnesses with rso-keel

A harness is the external constraint system that lets unreliable generative capability enter high-responsibility work.

It defines:

- where inputs come from
- which tools may be used
- when human approval is required
- what output contract is required
- how provenance is recorded
- how failures roll back
- how successful workflows become templates

## Build Order

1. Define domain responsibility objects.
2. Map domain actions to `WorkflowIR`.
3. Add server-side adapter: payload -> `WorkflowIR`.
4. Validate and gate before execution.
5. Implement node handlers.
6. Convert handler results to `HandlerOutput`.
7. Add HumanGate for high-risk steps.
8. Persist `PlanProvenance`.
9. Harden successful workflows into `TemplateSpec`.
10. Add metrics, fallback, and rollback.

## Domain Objects

Examples:

Research:

- Problem
- Source
- Claim
- Evidence
- Hypothesis
- Experiment
- Decision
- Artifact

Compliance:

- Policy
- Control
- Finding
- Evidence
- Exception
- Remediation
- ApproverDecision
- AuditArtifact

Investment diligence:

- Company
- Filing
- Claim
- RiskFactor
- Assumption
- Scenario
- InvestmentMemo
- ReviewerDecision

## Production Checklist

A production harness needs:

- ownership checks
- source registry
- template registry
- plan records
- durable checkpointing
- provenance persistence
- generated artifact storage
- billing/model usage aggregation
- HumanGate UI/resume endpoint
- fallback and rollback
- metrics and rollout gates
