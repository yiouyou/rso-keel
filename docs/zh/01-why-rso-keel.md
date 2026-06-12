# Why rso-keel

日期：2026-06-11

一句话：

> Workflow runtimes make AI workflows run. `rso-keel` makes high-responsibility AI workflows governable, auditable, and rollbackable.

`rso-keel` 不是另一个 agent framework，也不是某个 runtime 的插件。它解决的是另一个问题：当 AI workflow 产生的结果要进入正式工作、被复用、被审计、被人工确认、被回滚、被沉淀成模板时，普通 agent loop、workflow runtime 或 durable execution engine 都还缺少一层可信龙骨。

本文统一使用 **workflow runtime layer** 指代让 workflow 跑起来的下层能力。它比 “execution layer” 更准确，因为这层不只执行节点，还可能负责 checkpoint、interrupt、resume、queue、concurrency、rate limit、durable state 和跨服务 saga。LangGraph、Temporal、Hatchet、DBOS、Burr、LlamaIndex Workflows 都属于这个大类的不同实现或相邻能力。

## 1. 分层地图

理解 `rso-keel`，先把 AI workflow 系统分成五层：

```text
Product / platform layer
  users, projects, auth, billing, UI, files, queues, deployment

Domain harness layer
  domain objects, source policy, adapters, handlers, domain-specific review logic

Accountability layer
  rso-keel: WorkflowIR, validation, gates, HandlerOutput,
  PlanProvenance, HumanGate, TemplateSpec, metrics, rollback

Workflow runtime layer
  LangGraph, Temporal, Hatchet, DBOS, Burr, LlamaIndex Workflows
  graph execution, checkpoint, interrupt, queue, durable state, saga

Model / tool / source layer
  LLMs, retrieval, search, databases, file parsers, lab systems, deterministic tools
```

`rso-keel` 位于 **domain harness layer** 和 **workflow runtime layer** 之间：

- 向上，它给产品和领域 harness 一个可解释的责任链。
- 向下，它不关心具体 runtime 是 LangGraph、Temporal、Hatchet 还是 DBOS，只要求 runtime 执行的是经过校验的 workflow contract。
- 向外，它不替代 Guardrails、Phoenix、OpenTelemetry、MLflow、domain agents，而是让这些工具参与一个可审计的正式工作流。

这也是为什么 `rso-keel` 不应被描述成 “LangGraph wrapper”。LangGraph 是 RSO 当前选择的任务内 graph runtime；`rso-keel` 是 runtime 之上的 accountability layer。

## 2. 普通 agent 的隐性失败模式

很多 AI workflow 一开始看起来很成功：

```text
prompt
  -> agent plans
  -> tools run
  -> report generated
```

但当它进入真实组织时，问题会集中暴露：

- 这个报告用了哪些输入材料？
- 哪条结论来自哪个 source？
- 哪个模型、哪个 prompt、哪个 workflow 版本生成了它？
- 哪些步骤被人工确认过？
- 中途暂停后如何安全 resume？
- 失败时能不能回滚到 legacy path？
- 一次成功的 workflow 如何固化为可复用模板？
- 某个模板版本出问题时能否只回滚这个版本，而不是关闭整个系统？
- 成本、token、generated files、warnings、fallback 是否一致记录？

如果这些问题回答不了，系统就不是 production harness，只是一个会生成文本的 agent。

## 3. rso-keel 的核心命题

`rso-keel` 的核心命题是：

> 高责任 AI workflow 不能从自由文本计划直接进入执行。它必须先变成可校验、可版本化、可审计、可回滚的中间表示。

因此 `rso-keel` 把动态 AI workflow 拆成一条责任链：

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

模型可以越来越强，agent 可以越来越自主，但只要结果进入正式工作流，组织仍然需要这条责任链。

## 4. rso-keel 解决什么

`rso-keel` 解决的是 workflow governance，而不是模型能力或 workflow runtime。

| 问题 | 没有 rso-keel 时 | 有 rso-keel 时 |
|---|---|---|
| 动态计划 | prompt 或 Python 代码直接执行 | 先转换为 typed `WorkflowIR` |
| 安全边界 | 依赖调用方约定 | validator fail-closed |
| 工具权限 | handler 自己判断 | `allowed_skills` 和 policy gate |
| 人工确认 | UI 按钮或外部状态 | `human_approval` 是 workflow node |
| 输出格式 | 每个 handler 各写各的 | `HandlerOutput` 统一契约 |
| 溯源 | 日志里找 | `PlanProvenance` floor fields |
| 复用 | 复制 prompt | `TemplateSpec` version + content hash |
| 回滚 | 临时关开关 | domain/template 级 rollback |
| 放量 | 人工感觉 | metrics gate |

## 5. rso-keel 不解决什么

`rso-keel` 不试图替代：

- LLM provider。
- agent framework。
- search / retrieval system。
- observability backend。
- workflow runtime layer。
- host platform 的用户、项目、权限、计费、文件系统。

这些都可以继续使用。`rso-keel` 只要求：当它们参与一个高责任 workflow 时，必须通过统一的 IR、gate、handler output、provenance 和 template contract 暴露出来。

## 6. 为什么不是“自己写一层 wrapper”

很多团队一开始会写自己的 wrapper：

```text
run_agent()
save_result()
maybe_ask_human()
```

这在 demo 阶段足够，但很快会变成散落在业务代码里的隐式协议：

- 一个 endpoint 自己处理 owner。
- 一个 worker 自己处理 resume。
- 一个 handler 自己记录 token。
- 一个 report writer 自己写 generated files。
- 一个 config flag 自己控制 rollback。
- 一个 prompt 文件名被当成 template version。

`rso-keel` 的价值是把这些隐式约定变成显式 contract。contract 一旦稳定，模型、handler、runtime、产品入口都可以替换，而责任链不散。

## 7. 为什么模型越强越需要 rso-keel

弱模型的问题是“想不到”。强模型的问题是“太像真的”。

模型越强，越容易生成结构完整、语气自信、看似专业的输出。组织采用时的风险不再只是“答案不好”，而是：

- 错误结论进入正式知识库。
- 无来源 claim 被二次引用。
- 动态 workflow 绕过人工确认。
- 成功经验只留在一次聊天中，无法复用。
- 失败没有负证据沉淀，下一次重复犯错。

因此，模型越强，越需要把它的能力装进可审计、可回滚、可沉淀的外部结构。

## 8. rso-keel 的优秀性

`rso-keel` 的优秀性不在于“更聪明”，而在于它把高责任 AI workflow 的必要约束做成了一组小而硬的原语：

- **Typed Workflow IR**：动态计划先结构化，再执行。
- **Fail-closed validation**：非法 workflow 默认拒绝。
- **Workflow runtime boundary**：当前在 RSO 中编译到 LangGraph，但核心 contract 不等于 LangGraph，也不排斥 Temporal、Hatchet、DBOS 或其他 workflow runtime。
- **HandlerOutput**：平台 handler 的输出统一。
- **PlanProvenance**：每次执行有最低溯源字段。
- **HumanGate**：人工确认是可恢复 workflow 节点，不是 UI 装饰。
- **TemplateSpec**：workflow 可版本化、hash 化、review/approve/deprecate。
- **Rollback-first**：domain/template 级回滚是一等能力。
- **Host-platform boundary**：`rso-keel` core 不碰用户、数据库、计费和业务权限。

这些原语组合起来，形成的是“可信 harness contract”。

## 9. 什么时候 rso-keel 值得引入

当你的系统开始出现这些需求时，`rso-keel` 值得引入：

- 输出会影响正式决策。
- 报告需要审计和复现。
- 需要人工审批后继续执行。
- workflow 会被多次复用。
- 需要把动态 workflow 固化为模板。
- 需要灰度、fallback、rollback。
- 需要跨团队解释“AI 做了什么，为什么允许它这么做”。

如果只是低风险一次性生成，不需要 `rso-keel`。`rso-keel` 是给高责任 workflow 的，不是给所有 prompt 的。

## 10. 最短定义

`rso-keel` is an accountability layer for high-responsibility AI workflows.

它让 AI workflow 从：

```text
agent did something
```

变成：

```text
this validated workflow version ran these nodes,
with these sources, costs, approvals, artifacts, and rollback options
```

这就是 `rso-keel` 的必要性。
