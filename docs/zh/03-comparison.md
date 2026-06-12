# rso-keel 与相邻开源项目对比

日期：2026-06-11

`rso-keel` 的定位容易被误解，因为它靠近很多热门类别：agent framework、workflow runtime、durable execution、guardrails、observability、ML lifecycle、AI scientist。它们都重要，但解决的问题不同。

`rso-keel` 的位置：

```text
domain product
  -> rso-keel accountability contract
  -> graph / agent / tool runtimes
  -> model providers / retrieval / files / databases
```

## 1. 一句话对比

| 项目类型 | 代表项目 | 它解决什么 | rso-keel 解决什么 |
|---|---|---|---|
| Workflow runtime | LangGraph, Temporal, Hatchet, DBOS, Burr, LlamaIndex Workflows | workflow 怎么运行、持久化、调度或恢复 | 运行前后如何被校验、审计、模板化、回滚 |
| Multi-agent | AutoGen, CrewAI | 多个 agent 怎么协作 | agent 协作结果如何进入正式责任链 |
| Guardrails | Guardrails AI, NeMo Guardrails | 单次输入/输出是否合规 | 整个 workflow lifecycle 是否可信 |
| Observability | Phoenix, OpenTelemetry, LangSmith | 记录和评估发生了什么 | 在发生前定义可执行边界，发生后形成责任链 |
| ML lifecycle | MLflow | 实验、模型、评估、registry | agentic workflow 的 IR、HumanGate、template rollback |
| 科研 Agent | Robin, AI Scientist, Agent Laboratory | 领域发现/研究自动化 | 领域系统背后的通用可信 harness |

## 2. Workflow runtime layer

LangGraph、Temporal、Hatchet、DBOS、Burr、LlamaIndex Workflows 等项目都在不同角度解决“workflow 怎么跑”：

- [LangGraph](https://github.com/langchain-ai/langgraph)：任务内 graph execution、checkpoint、interrupt、resume。
- [Temporal](https://temporal.io/)：跨服务 durable workflow / saga。
- [Hatchet](https://github.com/hatchet-dev/hatchet)：worker orchestration、queue、concurrency、rate limits。
- [DBOS](https://www.dbos.dev/dbos-transact)：库形态 durable execution，Postgres-backed workflow state。
- [Apache Burr](https://burr.apache.org/)：显式状态机、追踪和可靠 AI application。
- [LlamaIndex Workflows](https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems)：轻量 event-driven agentic workflow。

`rso-keel` 不替代它们。`rso-keel` 位于它们之上或旁边，定义 high-responsibility workflow 的 accountability contract。

差异：

| 问题 | Workflow runtime layer | rso-keel |
|---|---|---|
| workflow 怎么运行 | 核心能力 | 使用或适配 |
| checkpoint / resume / queue / saga | 核心能力 | 记录和约束其语义 |
| typed accountability IR | 通常需自建 | 核心能力 |
| fail-closed validator | 通常需自建 | 内置 |
| handler 输出统一契约 | 通常需自建 | `HandlerOutput` |
| provenance floor | 通常需自建 | `PlanProvenance` |
| HumanGate 作为责任节点 | 通常需自建 | 核心能力 |
| template version/hash/status | 通常需自建 | `TemplateSpec` |
| domain/template rollback | 通常需自建 | 架构一等概念 |

如果问题是“workflow 怎么跑、怎么排队、怎么 checkpoint、怎么跨服务恢复”，优先选 workflow runtime layer。<br>
如果问题是“AI workflow 是否应该被允许执行，执行后如何审计、复用和回滚”，用 `rso-keel`。

## 3. Guardrails AI / NeMo Guardrails

[Guardrails AI](https://github.com/guardrails-ai/guardrails) 和 [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) 主要解决输入输出约束、结构校验、安全策略和对话行为边界。

`rso-keel` 需要 guardrails，但 `rso-keel` 不是 guardrails。

差异：

| 问题 | Guardrails | rso-keel |
|---|---|---|
| 单次 LLM 输出 schema | 强 | 可使用 |
| 对话安全策略 | 强 | 可使用 |
| 多节点 workflow 生命周期 | 非核心 | 核心 |
| 每个节点的 provenance | 非核心 | 核心 |
| 人工审批后 resume | 非核心 | 核心 |
| 模板固化与回滚 | 非核心 | 核心 |

Guardrails 能判断“这次输出是否合格”。<br>
`rso-keel` 要判断“这个 workflow 是否允许执行、如何执行、如何留下责任链”。

## 4. Phoenix / OpenTelemetry / LangSmith

[Phoenix](https://arize.com/phoenix/)、[OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) 和 LangSmith 等工具解决 observability、tracing、evaluation 和 debugging。

`rso-keel` 不替代 observability backend。`rso-keel` 产生的 provenance 可以导出到这些系统。

差异：

| 问题 | Observability 工具 | rso-keel |
|---|---|---|
| 记录调用链 | 强 | 产生结构化 provenance |
| debug token/latency/error | 强 | 提供治理语义 |
| 事后评估 | 强 | 可接入指标 |
| 执行前 fail-closed | 非核心 | 核心 |
| template lifecycle | 非核心 | 核心 |
| rollback contract | 非核心 | 核心 |

观测工具告诉你发生了什么。<br>
`rso-keel` 决定什么可以发生，并让发生的事可审计、可沉淀。

## 5. AutoGen / CrewAI

[AutoGen](https://github.com/microsoft/autogen)、[Microsoft Agent Framework](https://github.com/microsoft/agent-framework) 和 [CrewAI](https://github.com/crewAIInc/crewAI) 解决 agent 协作、角色分工、工具调用和任务自动化。

这些项目可以作为 `rso-keel` node handler 的内部实现。

差异：

| 问题 | Multi-agent framework | rso-keel |
|---|---|---|
| agent 角色和协作 | 强 | 非核心 |
| 工具调用 | 强 | 通过 handler 接入 |
| agent 自主规划 | 强 | 先转为受控 IR |
| 工作流版本和 hash | 通常需自建 | 核心 |
| 审批/回滚/放量指标 | 通常需自建 | 核心 |

Agent framework 让节点更聪明。<br>
`rso-keel` 让整个 workflow 可承担责任。

## 6. Robin / AI Scientist / Agent Laboratory

[FutureHouse Robin](https://github.com/Future-House/robin)、[Sakana AI Scientist-v2](https://github.com/sakanaai/ai-scientist-v2) 和 [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) 是 AI for Science / automated research 系统。

它们证明 agentic research 是有价值方向，但它们更像 `rso-keel` 上层的领域系统。

差异：

| 问题 | 科研 Agent 系统 | rso-keel |
|---|---|---|
| 自动发现/研究流程 | 强 | 可承载 |
| 科学任务专用逻辑 | 强 | 非核心 |
| 多租户权限/owner/resume | 通常不是重点 | 平台集成重点 |
| 通用 Workflow IR | 通常领域内定义 | 核心 |
| 通用 template/provenance/rollback | 通常需自建 | 核心 |

科研 agent 负责“研究怎么做”。<br>
`rso-keel` 负责“研究 workflow 如何被组织信任和复用”。

## 7. 为什么仍然需要 rso-keel

如果不用 `rso-keel`，你可以用开源项目拼出类似能力：

```text
LangGraph / Temporal / Hatchet / DBOS / Burr / LlamaIndex Workflows
  + Guardrails
  + Phoenix / OTel
  + MLflow-style registry
  + custom IR
  + custom provenance
  + custom HumanGate
  + custom template hash/version
  + custom rollback
  + custom rollout metrics
```

这条路可行，但你最终仍然会发明一个 `rso-keel`-like layer。

`rso-keel` 的价值是把这层提前显式化：

- AI workflow 必须有 typed IR。
- 执行前必须 validate。
- 高风险步骤必须 HumanGate。
- handler 输出必须统一。
- provenance 必须有 floor fields。
- workflow 必须可模板化。
- 模板必须可 review/approve/deprecate。
- 默认切换必须可 rollback。
- 生产放量必须看 metrics。

## 9. 选择建议

| 你的需求 | 建议 |
|---|---|
| 快速 agent demo | 不用 rso-keel，用 LangGraph/CrewAI/AutoGen |
| 多步 agent + checkpoint | LangGraph 或 Burr |
| 单次输出格式校验 | Guardrails/Pydantic |
| trace/eval/debug | Phoenix/OpenTelemetry/LangSmith |
| worker queue/concurrency/rate limit | Hatchet |
| durable execution / 跨服务业务 saga | Temporal/DBOS |
| 高责任 AI workflow | rso-keel + 合适的 runtime/tooling |

最终判断标准不是“任务复杂不复杂”，而是“输出是否需要承担责任”。
