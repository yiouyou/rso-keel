# Comparison

`rso-keel` is often confused with workflow runtimes, agent frameworks, guardrails, observability systems, and AI scientist projects. It is adjacent to all of them, but it solves a different problem.

## Summary

| Category | Examples | They solve | rso-keel solves |
|---|---|---|---|
| Workflow runtime | LangGraph, Temporal, Hatchet, DBOS, Burr, LlamaIndex Workflows | how workflows run, persist, queue, checkpoint, or recover | whether AI workflows are allowed, auditable, reusable, and rollbackable |
| Multi-agent framework | AutoGen, CrewAI | how agents collaborate | how agent outputs enter a formal responsibility chain |
| Guardrails | Guardrails AI, NeMo Guardrails | whether one input/output is valid | whether the full workflow lifecycle is accountable |
| Observability | Phoenix, OpenTelemetry, LangSmith | what happened | what was allowed to happen and how it becomes provenance |
| ML lifecycle | MLflow | experiments, models, registry | agentic workflow IR, HumanGate, template rollback |
| AI scientist systems | Robin, AI Scientist, Agent Laboratory | domain research automation | the governance harness underneath formal research workflows |

## Workflow Runtime Layer

LangGraph, Temporal, Hatchet, DBOS, Burr, and LlamaIndex Workflows all help workflows run.

`rso-keel` sits above or beside them. It defines the accountability contract:

- `WorkflowIR`
- validation
- gates
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`
- metrics and rollback

If your problem is “how does the workflow run?”, choose a runtime.

If your problem is “is this AI workflow allowed, auditable, reusable, and rollbackable?”, use `rso-keel`.

## Guardrails

Guardrails validate model input/output. `rso-keel` governs the whole workflow lifecycle.

They compose well:

```text
handler -> Guardrails/Pydantic validates output -> HandlerOutput -> PlanProvenance
```

## Observability

Phoenix, OpenTelemetry, LangSmith, and similar tools help trace and evaluate what happened.

`rso-keel` defines the accountable workflow structure before it happens and produces provenance after it happens.

Observability is not provenance. It can store or visualize provenance.

## Agent Frameworks

AutoGen, CrewAI, and similar systems can be used inside a node handler.

They make a node smarter. `rso-keel` makes the entire workflow accountable.

## Closest Open-Source Stack

Without `rso-keel`, a team often ends up assembling:

```text
workflow runtime
  + guardrails
  + observability
  + registry
  + custom IR
  + custom provenance
  + custom HumanGate
  + custom template version/hash
  + custom rollback
  + custom rollout metrics
```

That is effectively a `rso-keel`-like layer. `rso-keel` makes it explicit.
