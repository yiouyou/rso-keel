# rso-keel

面向高责任 AI workflow 的治理、溯源与编排中间层。

`rso-keel` 不是 agent framework，也不绑定某一个 workflow runtime。它位于 workflow runtime 和领域产品之间，负责把动态 AI workflow 变成可校验、可审计、可人工确认、可模板化、可回滚的正式工作流。

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

## 为什么需要 rso-keel

AI agent 已经可以规划、搜索、写作、调用工具、协调多个 agent。但这还不足以支撑高责任工作。

如果一个 AI workflow 会生成论文审查、专利分析、合规发现、实验建议卡、投研 memo 或安全评估，系统必须能回答：

- 输入是什么？
- 每条结论由哪些来源支持？
- 运行的是哪个 workflow 版本？
- 使用了哪个模型和工具？
- 哪些步骤经过人工确认？
- 生成了哪些文件？
- 成本是多少？
- 这个 workflow 能否复用？
- 出问题时能否按模板版本回滚？

这些答案不应该散落在 prompt、日志、UI 状态、worker 分支和零散数据库字段里。它们应该成为 workflow contract 的一部分。

## 分层定位

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

`rso-keel` 位于 domain harness layer 和 workflow runtime layer 之间。

## 推荐阅读顺序

- [01 为什么要做 rso-keel](./01-why-rso-keel.md)
- [02 什么时候使用](./02-when-to-use.md)
- [03 开源生态对比](./03-comparison.md)
- [04 快速开始](./04-quickstart.md)

## 构建与集成

- [05 架构](./05-architecture.md)
- [06 可信模型](./06-trust-model.md)
- [07 构建可信 Harness](./07-building-harnesses.md)
- [08 集成](./08-integrations.md)
- [09 评估](./09-evaluation.md)
- [10 FAQ](./10-faq.md)

## RSO 生产案例

- [11 RSO 迁移案例](./11-case-study-rso.md)
- [12 深度论证](./12-deep-rationale.md)

## 一句话

如果你的 AI workflow 只需要生成文本，`rso-keel` 太重。

如果你的 AI workflow 要生成可承担责任的正式工作产物，`rso-keel` 是缺失的一层。
