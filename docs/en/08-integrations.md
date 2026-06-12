# Integrations

`rso-keel` is the contract layer, not the everything layer.

It is designed to integrate with:

- workflow runtimes
- guardrails
- observability systems
- registries
- domain agents
- source systems

## Workflow Runtimes

Use workflow runtimes for execution mechanics:

- LangGraph: graph execution, checkpoint, interrupt, resume
- Temporal: cross-service durable workflow / saga
- Hatchet: worker orchestration, queues, concurrency, rate limits
- DBOS: durable execution backed by Postgres
- Burr / LlamaIndex Workflows: state-machine or event-driven workflows

`rso-keel` should provide the accountable contract that those runtimes execute.

## Guardrails

Use Guardrails AI, NeMo Guardrails, or Pydantic at node boundaries:

```text
handler -> validate model output -> HandlerOutput -> PlanProvenance
```

## Observability

Use Phoenix, OpenTelemetry, LangSmith, or similar systems for traces and evaluations.

Suggested mapping:

| rso-keel field | Observability mapping |
|---|---|
| `plan_id` | trace id / root span attribute |
| `node_id` | span name / attribute |
| `workflow_ir_hash` | trace attribute |
| template id/version/hash | trace attributes |
| `model_usage` | GenAI span attributes |
| HumanGate decision | event |
| fallback | trace attribute |

Observability is not provenance, but it can store and visualize provenance.

## Domain Agents

Domain agents can live inside node handlers.

```text
rso-keel node handler
  -> domain agent runs internally
  -> structured result
  -> HandlerOutput
```

The domain agent must not bypass `WorkflowIR`, validation, HumanGate, provenance, or template binding.
