# 什么情况下要用 rso-keel：采用边界与开源生态对照

日期：2026-06-11

本文回答两个问题：

1. 什么情况下应该使用 `rso-keel`。
2. 是否已有类似开源项目可以替代或复用。

相关文档：

- [为什么要做 rso-keel](./12-deep-rationale.md)
- [如何使用 rso-keel 构建可信 Harness](./07-building-harnesses.md)

## 1. 一句话判断

当你的系统不是在“回答问题”，而是在“生成会被复用、审批、审计、回滚或影响正式决策的工作产物”时，就应该考虑 `rso-keel`。

反过来，如果任务只是一次性低风险生成，没有人工确认、没有复现要求、没有跨任务沉淀，也不需要回滚，直接用模型 API、普通 agent framework 或简单 workflow 就够了。

## 2. 必须用 rso-keel 的情况

满足以下任一类，就应该优先用 `rso-keel`，而不是让 LLM/agent 自由执行。

### 2.1 输出会进入正式责任链

例如：

- 论文审查报告。
- 专利分析。
- 实验建议。
- 合规审查结论。
- 医疗质控意见。
- 投研尽调 memo。
- 工程变更评审。
- 安全风险评估。

这些产物不是“参考聊天记录”。它们会被保存、传阅、引用、修改、复用，甚至影响组织决策。因此系统必须回答：

- 这条结论从哪里来。
- 哪些来源支持它。
- 谁确认过。
- 用了哪个 workflow/template/model。
- 有哪些未验证假设。
- 失败或误用时怎么回滚。

### 2.2 需要可复现，而不只是可重复运行

“再跑一次”不等于复现。高责任任务需要知道：

- 输入材料版本。
- Workflow IR hash。
- Template id/version/content hash。
- 每个 node 的执行状态。
- 模型使用和成本。
- 人工审批决策。
- 生成文件 digest。

如果你需要这些字段，说明你需要 harness，而不是普通 agent loop。

### 2.3 需要人工确认点

如果 workflow 中存在以下动作，应该用 `human_approval` / HumanGate：

- 发布正式报告。
- 提交外部系统。
- 建议实验、合规例外、临床判断或重大财务判断。
- 把动态 workflow 固化为模板。
- 把项目内知识发布到跨项目知识库。

普通 HITL 按钮不够。HumanGate 必须是 plan lifecycle 的中断点：可暂停、可恢复、可审计、可校验 owner。

### 2.4 需要 workflow 沉淀

如果同类任务会反复出现，就不要只保存 prompt。应把有效流程沉淀为：

- `WorkflowIR`
- `WorkflowTemplate`
- version
- content hash
- reviewed/approved/deprecated status
- metrics
- rollback switch

这类需求是 `rso-keel` 的核心适用场景。

### 2.5 需要灰度、fallback 和 rollback

当默认执行后端可能从 legacy 切到 AI workflow 时，必须有：

- domain 级 rollback。
- template 级 rollback。
- fallback provenance。
- success/fallback/resume/provenance/cost 指标。
- 灰度门槛。

如果这些缺失，任何“默认启用 AI workflow”的决策都是高风险。

## 3. 应该谨慎使用 rso-keel 的情况

这些场景可以用 Keel，但要控制范围：

- 早期探索，还没有稳定领域对象。
- 用户只是想快速试验 agent 能力。
- 任务价值未验证，尚不值得建 template registry。
- 没有明确审批人或责任人。
- 来源可信度无法定义。

建议做法：

1. 先用简单 prototype 验证任务是否有价值。
2. 一旦产物开始被保存、复用、影响决策，再迁入 Keel。
3. 第一版只做一条窄 workflow，不要先做通用平台。

## 4. 不该用 rso-keel 的情况

不建议使用：

- 单轮问答。
- 低风险草稿。
- 纯创意写作。
- 一次性摘要。
- 不需要审计的内部小工具。
- 完全由现有确定性代码解决的问题。
- 只需要 schema validation 的 LLM 输出。
- 只需要 trace/observability 的应用。

这些场景用 `rso-keel` 会引入不必要的 schema、template、provenance 和审批成本。

## 5. 快速评分表

每项 0-2 分：

| 问题 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| 输出是否影响正式决策 | 不影响 | 间接影响 | 直接影响 |
| 是否需要来源和证据链 | 不需要 | 部分需要 | 强制需要 |
| 是否需要人工确认 | 不需要 | 偶尔需要 | 关键步骤必须 |
| 是否需要复现 | 不需要 | 失败时需要 | 每次都需要 |
| 是否会重复执行 | 一次性 | 低频 | 高频/标准流程 |
| 是否需要模板沉淀 | 不需要 | 项目内需要 | 跨项目/跨用户需要 |
| 是否需要 fallback/rollback | 不需要 | 手工可接受 | 必须自动支持 |
| 错误成本 | 低 | 中 | 高 |

建议：

- 0-4 分：不用 Keel。
- 5-8 分：先 prototype，进入保存/复用阶段后迁入 Keel。
- 9-12 分：用 Keel 做窄域 workflow。
- 13 分以上：从第一版就用 Keel，并设计 metrics、rollback 和 HumanGate。

## 6. 是否有类似开源项目

有很多相邻项目，但它们通常只覆盖 `rso-keel` 的一部分。更准确的说法是：`rso-keel` 不是替代所有这些工具，而是把它们上方的责任链、模板化治理和可回滚 harness 固定下来。

### 6.1 Execution / runtime 类

| 项目 | 主要能力 | 与 rso-keel 的关系 | 为什么不能完全替代 rso-keel |
|---|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | 长运行、有状态 agent graph；支持 persistence、human-in-the-loop、durable execution | RSO 当前使用的任务内 graph runtime | 解决“怎么跑图”，不定义可信 workflow IR、template 生命周期、领域 provenance floor 和 rollback contract |
| [Temporal](https://temporal.io/) | durable execution platform，可自托管或用 Temporal Cloud | 适合跨服务长生命周期 saga | 很强但偏通用业务编排；不能替代 `rso-keel` 的 typed IR、provenance 和 workflow hardening |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | worker orchestration、queue、concurrency、rate limits | 可作为 worker/runtime 层 | 解决调度和并发，不定义 AI workflow 的证据链、审批、模板与回滚 |
| [DBOS Transact](https://www.dbos.dev/dbos-transact) | 开源 durable execution library，使用 Postgres 存 workflow state | 可用于图外昂贵步骤的崩溃恢复 | 解决执行可靠性，不定义 AI workflow 的证据链、模板和审批语义 |
| [Apache Burr](https://burr.apache.org/) | 用状态机构建可靠 AI 应用，支持状态追踪、调试和遥测 | 相似于“显式状态机”理念 | 更偏应用状态机和调试，不提供 Keel 式 fail-closed IR、HumanGate/TemplateSpec/领域责任链 |
| [LlamaIndex Workflows](https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems) | 轻量 event-driven agentic workflow | 可用于构建应用 flow | 偏 workflow 框架，不是治理/审计/模板/回滚层 |
| [pydantic-graph](https://pydantic.dev/docs/ai/graph/graph/) | 类型安全的 async graph/state machine | 可借鉴类型化 graph 表达 | 不处理高责任任务的 provenance、审批、模板固化和 rollout |

结论：如果只需要 workflow 运行、调度、checkpoint 或 durable execution，用这些 runtime 即可；如果要把 workflow 变成可审计、可回滚、可沉淀的正式责任对象，需要 `rso-keel` 这一层。

### 6.2 多 Agent 框架类

| 项目 | 主要能力 | 与 rso-keel 的关系 | 为什么不能完全替代 rso-keel |
|---|---|---|---|
| [Microsoft AutoGen](https://github.com/microsoft/autogen) / [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | 多 Agent 应用和 agentic workflow 框架；AutoGen GitHub 当前提示维护模式，新方向并入 Agent Framework | 可作为 handler 内部 agent 实现 | 强在 agent 协作，不负责宿主平台的 template registry、owner 校验、fallback provenance |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 多 Agent 编排，强调角色、任务、工具和自动化 | 可作为某个 node handler 的内部实现 | 主要解决 agent 团队如何协作，不解决工作产物的版本、审批、复现、回滚 |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | 开源 deep research agent，生成研究报告 | 可作为 research handler 或参考产品 | 偏任务应用，不是通用 governance harness |

结论：多 Agent 框架可以让某个节点更聪明，但不能替代 Keel 对整个 workflow 生命周期的约束。

### 6.3 Guardrails / 输出验证类

| 项目 | 主要能力 | 与 rso-keel 的关系 | 为什么不能完全替代 rso-keel |
|---|---|---|---|
| [Guardrails AI](https://github.com/guardrails-ai/guardrails) | LLM 输入/输出 validation，Guardrails Hub validators | 可用于 handler 输出校验 | 解决单次输入输出是否合规，不解决 plan provenance、template registry、resume、rollback |
| [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) | 给 LLM conversational apps 添加 programmable guardrails | 可用于对话/节点级安全策略 | 强在对话行为和安全约束，不是高责任 workflow 的执行与审计层 |

结论：Guardrails 是 `rso-keel` 的局部组件，不是 `rso-keel` 的替代品。`rso-keel` 需要 guardrails，但还需要 IR、模板、审批、溯源和指标。

### 6.4 Observability / eval / lineage 类

| 项目 | 主要能力 | 与 rso-keel 的关系 | 为什么不能完全替代 rso-keel |
|---|---|---|---|
| [Arize Phoenix](https://arize.com/phoenix/) | 开源 agent observability 和 evaluation；支持 tracing、eval、troubleshooting | 可作为 trace/eval 后端 | 记录发生了什么，但不强制 workflow 结构、审批、模板版本和 rollback |
| [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | GenAI spans/events/metrics 语义规范 | `rso-keel` provenance 可映射或导出到 OTel | 是观测标准，不是 workflow governance runtime |
| [MLflow](https://mlflow.org/) | experiment tracking、model evaluation、model registry、deployment | 可借鉴 registry/lineage 思路 | 偏 ML lifecycle，不覆盖 agentic workflow 的 HumanGate、IR validator、template rollback |

结论：观测工具能告诉你发生了什么；Keel 还要在发生前决定是否允许发生，并在发生后决定能否沉淀和放量。

### 6.5 科研 Agent / 文献系统类

| 项目 | 主要能力 | 与 rso-keel 的关系 | 为什么不能完全替代 rso-keel |
|---|---|---|---|
| [FutureHouse Robin](https://github.com/Future-House/robin) | 多 Agent 自动化科学发现，公开代码和示例 trajectories | 科研 harness 的重要参考 | 是领域系统，不是通用 governance layer；可借鉴 constrained search 和 lab feedback |
| [Sakana AI Scientist / AI Scientist-v2](https://github.com/sakanaai/ai-scientist-v2) | 自动生成假设、跑实验、写论文；v2 引入 agentic tree search | 可借鉴假设空间搜索 | 目标是自动科研产出，不是多租户生产平台的审计/审批/回滚层 |
| [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | 面向人类研究者的端到端 research assistant | 可借鉴 research workflow 阶段划分 | 更像研究助手应用，不提供通用 workflow IR 和平台级 provenance contract |
| [OpenScholar](https://github.com/akariasai/openscholar) | 面向科学文献的 citation-backed synthesis | 可作为 verified literature synthesis 组件 | 聚焦文献综合，不是通用 harness |

结论：这些项目说明 AI 科研 agent 正在成熟，但它们更像 `rso-keel` 上层的领域能力，或某个 handler 的实现，不是 `rso-keel` 的替代。

## 7. 和 rso-keel 最接近的组合

如果从开源生态拼一个类似系统，最接近的组合大概是：

```text
LangGraph / Temporal / Hatchet / DBOS / Burr / LlamaIndex Workflows
  + Guardrails AI / NeMo Guardrails
  + Phoenix / OpenTelemetry
  + MLflow-style registry
  + 自研 typed IR
  + 自研 template registry
  + 自研 provenance contract
  + 自研 HumanGate owner/resume/fallback
  + 自研 rollout metrics
```

这说明 Keel 并不是“没有开源替代所以自研”。更准确地说：开源生态已经提供了很多底层积木，但缺少一个面向高责任 AI workflow 的轻量中间层，把这些积木组合成稳定的采用边界。

## 8. rso-keel 的不可替代组合

单独看每项能力，都有相邻项目：

- 执行/runtime：LangGraph、Temporal、Hatchet、DBOS、Burr、LlamaIndex Workflows。
- guardrail：Guardrails AI / NeMo。
- trace：Phoenix / OpenTelemetry。
- registry：MLflow。
- research agent：Robin / AI Scientist / Agent Laboratory。

但 Keel 组合的是：

- typed `WorkflowIR`。
- fail-closed validator。
- deterministic/rules gates。
- `HandlerOutput` 统一产物契约。
- `PlanProvenance`。
- `HumanGate` pause/resume。
- `TemplateSpec` version/content hash/status。
- domain/template fallback 和 rollback。
- rollout metrics。
- 平台无关 core，宿主平台负责权限和持久化。

这个组合才是“可信 harness”的核心。

## 9. 选型建议

### 只想快速做 agent demo

不用 `rso-keel`。选 CrewAI、AutoGen/Agent Framework、LlamaIndex Workflows 或 LangGraph。

### 要做长运行、多步、有人工介入的 agent

用 LangGraph/Burr/LlamaIndex Workflows 等 runtime。如果还需要组织级审计、模板和回滚，在 runtime 上加 `rso-keel`。

### 只需要输出格式校验

用 Guardrails AI、NeMo Guardrails、Pydantic 或普通 schema validation。不需要 Keel。

### 只需要 trace/eval

用 Phoenix、OpenTelemetry、MLflow 或 LangSmith。Keel 可以把 provenance 导出给这些系统，但不应替代它们。

### 要做科研、合规、医疗、投研、安全这类高责任 workflow

用 `rso-keel`。底层可继续用 LangGraph、Hatchet、DBOS、Temporal 或其他合适 runtime，节点内可用各种 agent/retrieval/guardrail/observability 工具。

### 要做跨服务、数天到数月的复杂业务 saga

先确认 `rso-keel` 的 IR/provenance/template contract 是否稳定。执行层再评估 Temporal、Hatchet 或 DBOS；不要让 execution layer 替代 `rso-keel` 的责任链模型。

## 10. 最终判断

`rso-keel` 应该在“AI 产物需要进入正式工作流”时使用，而不是在“我需要一个 agent 框架”时使用。

它不是 LangGraph、Temporal、Hatchet、DBOS、Guardrails、Phoenix、MLflow、Robin 或 AI Scientist 的替代品。它更像这些能力上方的一层可信 harness contract：把动态 AI workflow 变成可验证、可审批、可追溯、可回滚、可沉淀的生产对象。

因此，是否使用 `rso-keel` 的判断标准不是“任务是否复杂”，而是“任务是否需要承担责任”。

## 参考资料

- LangGraph GitHub, [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- LangChain Docs, [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- LangChain Docs, [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- Hatchet GitHub, [hatchet-dev/hatchet](https://github.com/hatchet-dev/hatchet)
- Hatchet, [Hatchet docs](https://docs.hatchet.run/)
- DBOS, [DBOS Transact](https://www.dbos.dev/dbos-transact)
- Temporal, [Durable Execution Platform](https://temporal.io/)
- Apache Burr, [Build reliable AI agents and applications](https://burr.apache.org/)
- LlamaIndex, [Workflows 1.0](https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems)
- Pydantic, [pydantic-graph](https://pydantic.dev/docs/ai/graph/graph/)
- Microsoft GitHub, [AutoGen](https://github.com/microsoft/autogen)
- Microsoft GitHub, [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- CrewAI GitHub, [crewAI](https://github.com/crewAIInc/crewAI)
- Guardrails AI GitHub, [guardrails](https://github.com/guardrails-ai/guardrails)
- NVIDIA GitHub, [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)
- Arize, [Phoenix](https://arize.com/phoenix/)
- OpenTelemetry, [Semantic conventions for generative AI systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- MLflow, [Open Source AI Platform](https://mlflow.org/)
- FutureHouse GitHub, [Robin](https://github.com/Future-House/robin)
- Sakana AI GitHub, [AI Scientist-v2](https://github.com/sakanaai/ai-scientist-v2)
- Agent Laboratory GitHub, [AgentLaboratory](https://github.com/SamuelSchmidgall/AgentLaboratory)
- OpenScholar GitHub, [OpenScholar](https://github.com/akariasai/openscholar)
