# rso-keel

Governance, provenance, and orchestration for high-responsibility AI workflows.

`rso-keel` is not an agent framework and it is not tied to one workflow runtime. It is the accountability layer above workflow runtimes and agent frameworks.

```text
domain payload
  -> WorkflowIR
  -> validation and gates
  -> compiled graph
  -> node handlers
  -> HandlerOutput
  -> PlanProvenance
  -> WorkflowTemplate
  -> metrics and rollback
```

## Why It Exists

AI agents can plan, search, write, call tools, and coordinate with other agents. That still is not enough for high-responsibility work.

If an AI workflow produces a research review, patent analysis, compliance finding, lab experiment card, investment memo, or safety assessment, the host product must answer:

- What inputs did it use?
- Which sources support each claim?
- Which workflow version ran?
- Which model and tools were used?
- Which steps required human approval?
- What files were generated?
- What did it cost?
- Can this exact workflow be reused?
- Can this template be rolled back?

`rso-keel` exists because those answers should be part of the workflow contract, not scattered across prompts, logs, UI state, worker branches, and one-off database fields.

## Layer Model

```text
Product / platform layer
  users, projects, auth, billing, UI, files, queues, deployment

Domain harness layer
  domain objects, source policy, adapters, handlers, domain review logic

Accountability layer
  rso-keel: WorkflowIR, validation, gates, HandlerOutput,
  PlanProvenance, HumanGate, TemplateSpec, metrics, rollback

Workflow runtime layer
  LangGraph, Temporal, Hatchet, DBOS, Burr, LlamaIndex Workflows
  graph execution, checkpoint, interrupt, queue, durable state, saga

Model / tool / source layer
  LLMs, retrieval, search, databases, file parsers, lab systems, deterministic tools
```

`rso-keel` sits between the domain harness layer and the workflow runtime layer.

## Start Here

- [01 Why rso-keel](./01-why-rso-keel.md)
- [02 When to Use](./02-when-to-use.md)
- [03 Comparison](./03-comparison.md)
- [04 Quickstart](./04-quickstart.md)

## Build With It

- [05 Architecture](./05-architecture.md)
- [06 Trust Model](./06-trust-model.md)
- [07 Building Harnesses](./07-building-harnesses.md)
- [08 Integrations](./08-integrations.md)
- [09 Evaluation](./09-evaluation.md)
- [10 FAQ](./10-faq.md)

## RSO Production Context

- [11 RSO Case Study](./11-case-study-rso.md)

## Short Version

If your AI workflow only needs to produce text, `rso-keel` is too much.

If your AI workflow needs to produce accountable work, `rso-keel` is the missing layer.
