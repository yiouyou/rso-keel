# rso-keel 集成

`rso-keel` 是 contract layer，不是 everything layer。它应该和已有 runtime、guardrails、observability、registry、domain agents 配合使用。

## Workflow runtime

workflow runtime 负责执行机制：

- LangGraph：graph execution、checkpoint、interrupt、resume。
- Temporal：跨服务 durable workflow / saga。
- Hatchet：worker orchestration、queue、concurrency、rate limits。
- DBOS：Postgres-backed durable execution。
- Burr / LlamaIndex Workflows：状态机或 event-driven workflow。

`rso-keel` 提供这些 runtime 要执行的 accountable workflow contract。

## Guardrails

Guardrails AI、NeMo Guardrails、Pydantic 适合在 node 边界做输入/输出校验：

```text
handler -> validate model output -> HandlerOutput -> PlanProvenance
```

Guardrails 不替代 `WorkflowIR`、HumanGate、provenance、template lifecycle 和 rollback。

## Observability

Phoenix、OpenTelemetry、LangSmith 等适合做 trace、eval、debug。

建议映射：

| rso-keel 字段 | Observability 映射 |
|---|---|
| `plan_id` | trace id / root span attribute |
| `node_id` | span name / attribute |
| `workflow_ir_hash` | trace attribute |
| template id/version/hash | trace attributes |
| `model_usage` | GenAI span attributes |
| HumanGate decision | event |
| fallback | trace attribute |

Observability 不是 provenance，但可以存储和展示 provenance。

## Domain agents

领域 agent 可以放在 node handler 内部：

```text
rso-keel node handler
  -> domain agent runs internally
  -> structured result
  -> HandlerOutput
```

领域 agent 不应绕过 `WorkflowIR`、validation、HumanGate、provenance 或 template binding。

## Source systems

高责任 workflow 需要 verified sources：

- 文献数据库。
- 专利数据库。
- 法规/政策库。
- 内部知识库。
- 用户上传文件。
- 实验记录。

`rso-keel` core 不应包含 source credentials 或 source-specific clients。宿主平台 adapter 和 handler 负责访问来源，并把 source id 写入 handler metadata / provenance。
