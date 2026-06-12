# FAQ

## Is rso-keel an agent framework?

No.

Agent frameworks coordinate agents and tools. `rso-keel` governs whether a high-responsibility workflow is valid, auditable, approvable, reusable, and rollbackable.

## Is it tied to LangGraph?

No.

RSO currently compiles `rso-keel` workflows to LangGraph, but the core contract is runtime-independent:

- `WorkflowIR`
- validation
- gates
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`
- rollback

## Does it replace Temporal, Hatchet, or DBOS?

No.

Those systems are workflow runtime / durable execution / worker orchestration layers. `rso-keel` is the accountability layer above them.

## Does it replace Guardrails?

No.

Guardrails validate specific model inputs or outputs. `rso-keel` governs the full workflow lifecycle.

## Does it guarantee correctness?

No.

It guarantees traceability and accountability. Scientific, medical, legal, or financial correctness still requires domain validation.

## When is it too heavy?

It is too heavy for one-off, low-risk generation.

Use it when outputs affect formal work and need provenance, approval, reuse, and rollback.

## Can clients submit WorkflowIR directly?

Not in high-responsibility settings.

Clients should submit domain payloads or explicit template bindings. Server-side adapters should build canonical `WorkflowIR`, and server-side registries should provide template hashes.
