# rso-keel

[English](../../README.md) | [中文]

面向高责任 AI workflow 的治理、溯源与编排中间层。

`rso-keel` 不是另一个 agent framework，也不绑定某一个 workflow runtime。它是位于 workflow runtime 和领域产品之间的 accountability layer，负责把动态 AI workflow 变成可校验、可审计、可人工确认、可模板化、可回滚的正式工作流。

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

如果一个 AI workflow 会生成论文审查、专利分析、合规发现、实验建议卡、投研 memo 或安全评估，系统需要回答：

- 输入是什么？
- 每条结论由哪些来源支持？
- 运行的是哪个 workflow 版本？
- 使用了哪个模型和工具？
- 哪些步骤经过人工确认？
- 生成了哪些文件？
- 成本是多少？
- 这个 workflow 能否复用？
- 出问题时能否按模板版本回滚？

## 文档入口

- [00 概览](00-overview.md)
- [01 为什么要做 rso-keel](01-why-rso-keel.md)
- [02 什么时候使用](02-when-to-use.md)
- [03 开源生态对比](03-comparison.md)
- [04 快速开始](04-quickstart.md)
- [05 架构](05-architecture.md)
- [06 可信模型](06-trust-model.md)
- [07 构建可信 Harness](07-building-harnesses.md)
- [08 集成](08-integrations.md)
- [09 评估](09-evaluation.md)
- [10 FAQ](10-faq.md)
- [11 RSO 案例](11-case-study-rso.md)
- [12 深度论证](12-deep-rationale.md)

## 核心原语

- `WorkflowIR`
- fail-closed validation
- deterministic/rules gates
- runtime compilation
- `HandlerOutput`
- `PlanProvenance`
- `HumanGate`
- `TemplateSpec`

`rso-keel` 没有平台依赖：不依赖 `app.*`、backend models、用户数据库或计费系统。宿主产品负责 auth、tenancy、storage、queues、UI 和模型凭据；`rso-keel` 提供可承担责任的 workflow contract。
