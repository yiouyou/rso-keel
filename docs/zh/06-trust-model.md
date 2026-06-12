# rso-keel Trust Model

日期：2026-06-11

`rso-keel` 的可信模型不是“相信模型更聪明”，而是“系统能证明一个 AI workflow 是如何被允许、执行、确认、产出、回滚和沉淀的”。

## 1. 信任边界

`rso-keel` 不信任以下输入：

- 自由文本 prompt。
- LLM 生成的计划。
- 客户端传入的 template hash。
- handler 自己声称的最终状态。
- 没有来源绑定的强结论。
- 没有 owner 校验的 resume 请求。

`rso-keel` 只信任经过宿主平台和 `rso-keel` contract 双重约束后的对象：

- 宿主平台校验过的 user/project/source 权限。
- 服务端 adapter 生成的 `WorkflowIR`。
- `validate()` 和 gates 通过的 workflow。
- 服务端 registry 返回的 template/version/content hash。
- `HandlerOutput` 统一输出。
- `PlanProvenance` 记录的执行事实。
- HumanGate 记录的人工决策。

## 2. 可信链条

`rso-keel` 的可信链条如下：

```text
Authenticated actor
  -> authorized domain payload
  -> server-side adapter
  -> WorkflowIR
  -> validator
  -> deterministic/rules gates
  -> compiled graph
  -> registered node handlers
  -> HandlerOutput
  -> PlanProvenance
  -> generated artifacts
  -> metrics
  -> TemplateSpec or rollback
```

任何一环失败，都不应该静默继续。高责任 workflow 的默认行为是 fail-closed。

## 3. WorkflowIR：限制动态性

模型可以提出动态 workflow，但不能直接执行自由文本计划。它必须先被转换为 `WorkflowIR`。

`WorkflowIR v1` 锁定 6 类 node。它们不是所有自动化流程的通用本体，而是可信科研/知识工作流的 v1 最小安全闭包：

- `workspace_read`
- `literature_search`
- `independent_critic`
- `synthesis`
- `human_approval`
- `report_write`

这 6 类节点刻意覆盖一条高责任知识工作流的最小责任链：内部证据、外部补证、独立质疑、综合判断、人工确认、正式输出。动态计划可以变化，但只能在受控 grammar 内变化。

如果一个领域动作看起来放不进这 6 类，默认先把它封装成已注册 skill 或固定 workflow，由现有 node kind 调用。只有当多个 domain 都证明现有六类无法安全表达同一种基础控制流时，才考虑 bump `schema_version` 并扩展 node kind。

## 4. Validator：默认拒绝

`keel.ir.validator.validate()` 的角色是防止非法 workflow 进入执行。

它检查：

- schema version。
- node kind 白名单。
- skill allowlist。
- provenance 是否开启。
- cost ceiling。
- conditional edge 是否包含自由代码。
- graph 是否为 DAG。
- 需要人工确认时是否存在 `human_approval` node。

这不是 lint。validation failure 应该停止执行。

## 5. Gates：把策略放在执行前

`rso-keel` 的 gate 分层：

- `DeterministicGate`：结构性检查，不调用外部系统。
- `RulesGate`：成本、source breadth、critic count、skill policy 等规则。
- host gate：宿主平台的权限、配额、项目策略、合规策略。

原则：

- 能在执行前发现的问题，不留到执行后。
- 能用确定性规则判断的问题，不交给 LLM 判断。
- LLM/专家判断必须标记为 judgment，不伪装成确定性事实。

## 6. HandlerOutput：统一节点产物

每个 handler 最终都应输出或转换为 `HandlerOutput`：

- `summary`
- `generated_files`
- `warnings`
- `next_step`
- `tokens_in`
- `tokens_out`
- `model_usage`
- `output_digest`
- `metadata`

这样 provenance、billing、generated files、UI 和 metrics 不需要理解每个 handler 的私有格式。

## 7. PlanProvenance：不是日志

日志用于 debug。Provenance 用于责任链。

`PlanProvenance` 至少记录：

- `schema_version`
- `plan_id`
- `workflow_ir_hash`
- `ir_schema_version`
- `objective`
- `actor`
- `config_snapshot`
- `node_traces`
- `model_usage`
- `integrity`

一个正式产物必须能回到：

```text
artifact
  -> job
  -> plan_id
  -> workflow_ir_hash
  -> template/version/hash
  -> node traces
  -> sources and approvals
```

## 8. HumanGate：人工确认是生命周期节点

`rso-keel` 的 HumanGate 不是“页面上有一个确认按钮”。它是 workflow graph 中的一等节点：

- 进入 gate 时 workflow 可暂停。
- 暂停状态不占 worker slot。
- 审批结果进入 provenance。
- resume 时必须校验 owner/project/plan。
- 审批后从 checkpoint 继续。

这让人工确认从 UI 状态变成执行语义。

## 9. TemplateSpec：沉淀但不污染

一次成功的 workflow 不能直接变成默认流程。Keel 用 `TemplateSpec` 让 workflow 经历生命周期：

```text
draft
  -> reviewed
  -> approved
  -> deprecated
```

每个 template 都有：

- `template_id`
- `version`
- `status`
- `ir_skeleton`
- `content_hash`
- timestamps
- tags

规则：

- hash 由 canonical skeleton 计算。
- reviewed/approved 后不原地修改。
- 新变化创建新 version。
- job 记录绑定的 template/version/hash。
- 出问题可 template-level rollback。

## 10. Rollback：可信系统必须能后退

`rso-keel` 的默认假设是：新 workflow 可能出错。

因此需要：

- domain-level fallback。
- template-level rollback。
- fallback result/provenance。
- rollback metrics。
- rollback 演练。

没有 rollback 的 AI 默认路径，不应进入生产。

## 11. Metrics：信任要被持续验证

Keel harness 至少要观测：

- success rate。
- fallback rate。
- resume success rate。
- provenance completeness。
- generated file rate。
- token/cost median and p95。
- human revision rate。
- source verification pass rate。
- template adoption rate。
- rollback count。

CI 通过只说明代码路径可运行。生产信任必须来自真实 workload 的持续指标。

## 12. Host Platform Boundary

`rso-keel` core 保持平台无关，不处理：

- user auth。
- project ownership。
- database models。
- billing account。
- file storage。
- UI。
- external source credentials。

这些属于宿主平台。

`rso-keel` 只定义平台应该提供和记录哪些 contract。这个边界让 `rso-keel` 可以嵌入不同产品，而不把某个产品的权限模型写死进 core。

## 13. Trust Statement

`rso-keel` 不证明模型结论一定正确。

`rso-keel` 证明的是：

```text
The workflow was allowed,
the inputs and policies were recorded,
the graph was validated,
the nodes ran under known handlers,
the human gates were captured,
the artifacts and model usage were recorded,
and the template can be reused or rolled back.
```

这就是高责任 AI workflow 的最低可信边界。
