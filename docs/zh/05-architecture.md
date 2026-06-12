# rso-keel 架构

`rso-keel` 是高责任 AI workflow 的 accountability layer，位于领域 harness 和 workflow runtime 之间。

```text
Host product
  -> domain adapter
  -> rso-keel core
  -> workflow runtime
  -> handlers
  -> host persistence / UI / metrics
```

## 分层

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

## Core 模块

| 模块 | 职责 |
|---|---|
| `keel.ir` | `WorkflowIR`、node schema、policies、validator |
| `keel.compiler` | IR 到 runtime graph 的编译 |
| `keel.convergence` | deterministic gate 和 rules gate |
| `keel.handlers` | `HandlerOutput`、`GeneratedFileRef`、`ModelUsage` |
| `keel.provenance` | `PlanProvenance`、actor、node traces、integrity |
| `keel.sitl` | `HumanGate`、approval request/decision schema |
| `keel.templates` | `TemplateSpec`、状态生命周期、content hash |
| `keel.policy` | preflight report 和 runtime cost guard |
| `keel.lab` | `ExperimentCard` 高责任建议对象 schema |

## Runtime 边界

RSO 当前把 `rso-keel` workflow 编译到 LangGraph。这是实现选择，不是 `rso-keel` 的全部抽象。

`rso-keel` 负责：

- IR。
- validator。
- gates。
- handler output contract。
- provenance schema。
- template lifecycle。
- rollback semantics。

workflow runtime 负责：

- graph execution。
- checkpoint。
- interrupt / resume。
- queue / concurrency / rate limit。
- durable workflow / saga。

## Host 边界

`rso-keel` core 不 import 平台代码，不负责：

- user auth。
- project ownership。
- database models。
- billing ledger。
- file storage。
- frontend UI。
- model credentials。
- source credentials。

这些由宿主平台 adapter / bridge 层负责。这个边界保证 `rso-keel` 可嵌入、可抽取、可开源。
