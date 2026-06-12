# Why rso-keel

> Workflow runtimes make AI workflows run. `rso-keel` makes high-responsibility AI workflows governable, auditable, and rollbackable.

`rso-keel` is not another agent framework, and it is not a plugin for one runtime. It addresses a different problem: when AI workflow outputs enter formal work, get reused, get audited, require human approval, need rollback, or become templates, ordinary agent loops and workflow runtimes are missing an accountability layer.

## The Layering

```text
Product / platform layer
Domain harness layer
Accountability layer        <- rso-keel
Workflow runtime layer      <- LangGraph / Temporal / Hatchet / DBOS / Burr / LlamaIndex
Model / tool / source layer
```

`rso-keel` is between the domain harness layer and the workflow runtime layer.

It gives the product and domain layer an accountable chain of custody. It does not care whether the runtime is LangGraph, Temporal, Hatchet, DBOS, or something else, as long as the runtime executes a validated workflow contract.

## The Hidden Failure Mode

A basic agent workflow may look successful:

```text
prompt
  -> agent plans
  -> tools run
  -> report generated
```

But when it enters a real organization, the hard questions appear:

- Which sources support this claim?
- Which workflow version ran?
- Which model and tool calls were used?
- Who approved the high-risk step?
- Can the job resume safely after interruption?
- Can a broken template version be rolled back?
- Can a successful dynamic workflow become a reusable template?
- Are cost, tokens, generated files, warnings, and fallback recorded consistently?

If the system cannot answer those questions, it is not a production harness. It is a text-generating agent.

## Core Claim

High-responsibility AI workflows must not execute directly from free-form model plans. They must first become typed, validated, versioned, auditable, and rollbackable intermediate representations.

That is why `rso-keel` uses:

- `WorkflowIR`
- fail-closed validation
- deterministic and rules gates
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`
- metrics
- rollback controls

## What rso-keel Is Good At

`rso-keel` is not smarter than the model. It is stricter than the workflow.

It makes these properties explicit:

- Dynamic plans become typed workflow IR.
- Invalid workflows are rejected before execution.
- Human approval is a lifecycle node, not a UI decoration.
- Handler outputs use one contract.
- Formal artifacts can be traced back to plan, template, sources, model usage, and human decisions.
- Successful workflows can be hardened into versioned templates.
- Bad workflow versions can be rolled back.

## What It Does Not Replace

`rso-keel` does not replace:

- LLM providers
- workflow runtimes
- agent frameworks
- retrieval systems
- observability tools
- durable execution engines
- host platform auth, billing, storage, or UI

It makes those systems participate in an accountable workflow contract.
