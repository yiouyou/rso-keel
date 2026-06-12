# rso-keel FAQ

日期：2026-06-11

## rso-keel 是 agent framework 吗？

不是。

`rso-keel` 是 high-responsibility AI workflow 的 accountability layer。Agent framework 解决 agent 怎么协作和调用工具；`rso-keel` 解决 workflow 如何被校验、审批、审计、回滚和沉淀。

## rso-keel 和 LangGraph、Temporal、Hatchet、DBOS 是什么关系？

它们属于不同层。

- LangGraph：任务内 graph execution、checkpoint、interrupt、resume。
- Temporal：跨服务 durable workflow / saga。
- Hatchet：worker orchestration、queue、concurrency、rate limits。
- DBOS：库形态 durable execution，Postgres-backed workflow state。
- `rso-keel`：workflow accountability contract，包括 IR、validation、provenance、HumanGate、TemplateSpec、rollback。

RSO 当前把 `rso-keel` 编译到 LangGraph，但这不是 `rso-keel` 的全部定位。

```text
rso-keel defines what high-responsibility workflow is allowed to exist.
Workflow runtimes run it.
```

## 为什么不用 execution engine 自己实现？

可以，但你最终需要在 workflow runtime 层之上自己实现：

- typed IR。
- validator。
- policy gates。
- handler output contract。
- provenance schema。
- HumanGate owner/resume contract。
- template version/hash/status。
- domain/template rollback。
- rollout metrics。

`rso-keel` 把这层显式化。

## rso-keel 会不会太重？

如果你的任务只是一次性低风险生成，`rso-keel` 确实太重。

`rso-keel` 适合：

- 产物会被保存/复用。
- 输出会影响正式决策。
- 需要人工确认。
- 需要复现和审计。
- 需要回滚。
- workflow 会沉淀为模板。

## rso-keel 能保证模型结论正确吗？

不能。

`rso-keel` 保证的是责任链：

- 输入是什么。
- workflow 是哪个版本。
- 哪些 gate 通过。
- 哪些节点运行。
- 哪些模型和工具被使用。
- 哪些人工决策发生。
- 哪些 artifact 被生成。
- 出错如何回滚。

科学、合规、医疗、投研等领域的最终正确性仍需要领域验证。

## rso-keel 支持哪些模型？

`rso-keel` core 不绑定模型。模型调用发生在 node handler 内。

这意味着你可以使用：

- OpenAI。
- Anthropic。
- Gemini。
- Qwen。
- DeepSeek。
- local model。
- non-LLM deterministic tools。

只要 handler 把结果转换为 `HandlerOutput`。

## rso-keel 支持哪些运行时？

当前 RSO 实现编译到 LangGraph。

`rso-keel` 的核心 contract 是：

- `WorkflowIR`。
- validator/gates。
- `HandlerOutput`。
- `PlanProvenance`。
- `HumanGate` shape。
- `TemplateSpec`。

理论上未来可支持其他 runtime，但必须保留这些 contract。

## rso-keel 是否替代 Temporal / Hatchet / DBOS？

不替代。

Temporal、Hatchet、DBOS 解决 execution、worker orchestration 或 durable execution。`rso-keel` 解决 AI workflow accountability。

它们可以组合：

- LangGraph 负责图内 checkpoint。
- DBOS 负责图外昂贵步骤。
- Temporal 负责跨服务 saga。
- Hatchet 负责 worker queue/concurrency/rate limit。
- `rso-keel` 负责 IR/provenance/template/rollback。

## rso-keel 是否替代 Guardrails？

不替代。

Guardrails 适合校验单次模型输入/输出。`rso-keel` 适合治理整个 workflow lifecycle。

推荐组合：

```text
handler -> Guardrails validates LLM output -> HandlerOutput -> rso-keel provenance
```

## rso-keel 是否替代 Phoenix / OpenTelemetry / LangSmith？

不替代。

Observability 工具记录和分析 trace。`rso-keel` 产生 provenance 和治理语义。`rso-keel` provenance 可以导出到 observability 系统。

## 为什么 rso-keel core 不处理用户和权限？

因为不同宿主平台的权限模型不同。

`rso-keel` core 保持平台无关：

- 不 import platform DB。
- 不知道 user table。
- 不知道 billing ledger。
- 不知道 file storage。

宿主平台在 adapter 和 bridge 层做 ownership 校验，并把 actor/project/source 信息传入 `rso-keel` contract。

## 客户端可以直接提交 WorkflowIR 吗？

不建议。

高责任场景中，客户端应该提交 domain payload 或显式 template binding。服务端 adapter 生成 canonical `WorkflowIR`，并从 server-side registry 读取 template hash。

不要信任客户端传入的 content hash。

## 什么时候应该扩展 node kind？

谨慎扩展。

`WorkflowIR v1` 锁定 6 类 node。它们是可信知识工作流的 v1 最小安全闭包，不是所有自动化流程的通用本体。多数场景应先映射到现有 node kind：

- read。
- search。
- critic。
- synthesis。
- human approval。
- report write。

只有多个 domain 都无法安全表达同一种基础控制流，而且新增 node kind 值得同步增加 validator、compiler、provenance、tests 和回滚复杂度时，才考虑 bump schema version 并扩展 core。

## rso-keel 开源后最应该展示什么？

三件事：

1. 15 分钟 quickstart。
2. 一个真实 case study。
3. 与 LangGraph/Temporal/Hatchet/DBOS/Guardrails/Phoenix 的清晰对比。

外部读者需要先理解“为什么不是又一个 agent framework 或 workflow runtime”。
