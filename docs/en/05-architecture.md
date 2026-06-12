# Architecture

`rso-keel` is an accountability layer between domain harness logic and workflow runtimes.

```text
Host product
  -> domain adapter
  -> rso-keel core
  -> workflow runtime
  -> handlers
  -> host persistence / UI / metrics
```

## Layers

```text
Product / platform layer
  users, projects, auth, billing, UI, files, queues, deployment

Domain harness layer
  domain objects, source policy, adapters, handlers, domain review logic

Accountability layer
  rso-keel: WorkflowIR, validation, gates, HandlerOutput,
  PlanProvenance, HumanGate, TemplateSpec, metrics, rollback

Workflow runtime layer
  graph execution, checkpoint, interrupt, queue, durable state, saga

Model / tool / source layer
  LLMs, retrieval, search, databases, file parsers, deterministic tools
```

## Core Modules

| Module | Responsibility |
|---|---|
| `keel.ir` | `WorkflowIR`, node schema, policies, validation |
| `keel.compiler` | IR to runtime graph compilation |
| `keel.convergence` | deterministic and rules gates |
| `keel.handlers` | `HandlerOutput`, `GeneratedFileRef`, `ModelUsage` |
| `keel.provenance` | `PlanProvenance`, actor, node traces, integrity |
| `keel.sitl` | `HumanGate`, approval request/decision schema |
| `keel.templates` | `TemplateSpec`, status lifecycle, content hash |
| `keel.policy` | preflight report and runtime cost guard |
| `keel.lab` | `ExperimentCard` schema |

## Runtime Boundary

RSO currently compiles `rso-keel` workflows to LangGraph. That is an implementation choice.

`rso-keel` owns the accountable contract. The runtime owns execution mechanics.

## Host Boundary

`rso-keel` core intentionally does not import host platform code. The host owns:

- user auth
- project ownership
- database models
- billing
- file storage
- UI
- model credentials
- source credentials

This boundary keeps `rso-keel` extractable and open-sourceable.
