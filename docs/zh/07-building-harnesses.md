# 如何使用 rso-keel 构建可信 Harness

日期：2026-06-11

本文面向想复用 `rso-keel` 的建设者：不只做科研，也可以做合规审查、医疗质控、投研尽调、专利分析、安全评估、政策审查、工程变更评审等场景。共同特征是：系统不只是生成答案，而是必须重视可信、复现、审计、回滚和沉淀。

相关背景文档：

- [为什么要做 rso-keel](./12-deep-rationale.md)

## 1. 什么是 harness

在这里，harness 不是一个 prompt，也不是一组 agent。它是把不可靠的生成式能力接入高责任任务时所需的外部约束系统：

- 规定输入从哪里来。
- 规定哪些工具可以用。
- 规定什么时候必须人工确认。
- 规定输出必须带哪些证据、版本和来源。
- 规定失败时如何回滚。
- 规定成功经验如何固化为可复用 workflow。

一句话：模型负责扩展可能性，harness 负责把可能性变成可承担责任的工作流。

## 2. 哪些场景适合用 rso-keel

适合：

- 输出会影响正式决策，而不是一次性闲聊。
- 结论需要解释来源、证据、版本和责任人。
- 错误成本高，不能只靠“模型看起来合理”。
- 工作流会重复出现，值得沉淀成模板。
- 任务可能中断、等待人工审批或需要恢复执行。
- 需要灰度、指标、fallback 和 rollback。

不适合：

- 纯聊天、低风险创意写作、一次性草稿。
- 没有可定义输入、输出或审批边界的开放探索。
- 只需要一个模型 API wrapper。
- 需要完全自由执行代码、访问网络或调用工具且不做审计的系统。

## 3. rso-keel 提供什么

当前 `rso-keel` 是平台无关的 governance / provenance / orchestration 中间层。它不 import `app.*`、数据库模型、用户系统、计费系统或产品层代码。宿主平台负责用户、项目、权限、持久化和 UI；Keel 负责 workflow 的结构化、验证、编译、执行约束和可追溯输出。

核心模块：

- `keel.ir`：`WorkflowIR` schema 和 fail-closed validator。
- `keel.compiler`：把 `WorkflowIR` 编译成 LangGraph graph。
- `keel.handlers`：平台无关的 `HandlerOutput` 契约。
- `keel.provenance`：plan lifecycle provenance schema。
- `keel.sitl`：`HumanGate`，用于人工确认和 resume。
- `keel.templates`：`TemplateSpec`，用于不可变 workflow 模板和内容 hash。
- `keel.convergence`：DeterministicGate / RulesGate 等收敛检查。
- `keel.policy`：preflight 和 runtime cost guard。
- `keel.lab`：实验建议卡片 schema，可作为高责任建议对象的参考模式。

## 4. 最小架构

一个 Keel-backed harness 至少需要五层：

```text
Host product
  -> domain payload
  -> adapter builds WorkflowIR
  -> keel validate / gates / compile
  -> node handlers run tools/models
  -> HandlerOutput + provenance + artifacts
  -> host persists TaskJob/result/files/metrics
```

宿主平台必须保留的职责：

- 认证、权限、租户隔离。
- 项目、工作区、文件、数据库持久化。
- job queue、worker、重试和部署。
- 模型密钥、计费、速率限制。
- UI、审批体验、指标看板。
- legacy fallback 或人工兜底。

Keel 应该保留的职责：

- workflow 的结构化表示。
- schema validation 和 policy gate。
- 可执行 graph 的编译。
- node handler 的统一输出契约。
- provenance、governance snapshot 和 audit trace。
- human approval interrupt 的标准形状。
- template hash、version、review/approve/deprecate 生命周期。

## 5. 构建流程

### Step 1：定义领域对象

先不要写 agent。先定义这个 harness 里“可承担责任的对象”是什么。

例如科研 harness：

- Problem
- Source
- Claim
- Evidence
- Hypothesis
- Experiment
- Decision
- Artifact

例如合规审查 harness：

- Policy
- Control
- Finding
- Evidence
- Exception
- Remediation
- ApproverDecision
- AuditArtifact

例如投研尽调 harness：

- Company
- SourceFiling
- Claim
- RiskFactor
- Assumption
- Scenario
- InvestmentMemo
- ReviewerDecision

每个对象都应该能回答：

- 谁创建。
- 来自哪个来源。
- 使用哪个 workflow/template/version。
- 当前状态是什么。
- 谁审核过。
- 是否可回滚。
- 是否可复用。

### Step 2：把领域任务降到 Keel v1 的最小安全闭包

当前 `WorkflowIR v1` 锁定 6 类节点。它们不是所有自动化流程的普适本体，而是可信知识工作流的 v1 最小安全闭包：

- `workspace_read`
- `literature_search`
- `independent_critic`
- `synthesis`
- `human_approval`
- `report_write`

不要为了一个领域随手新增 node kind。新增 kind 是 schema 变更，必须 bump `schema_version` 并同步 validator、compiler、tests、provenance 和宿主 bridge。

判断标准：新增 node kind 必须证明现有六类无法安全表达，并且这个新语义会在多个 domain 中复用。否则应该把领域动作封装成已注册 skill、固定 workflow 或 handler payload，由现有 node kind 调用。

推荐做法是先把领域动作映射到现有 node kind：

| 领域动作 | Keel v1 node kind | 说明 |
|---|---|---|
| 读取项目材料、合同、实验记录、代码仓库 | `workspace_read` | 所有内部上下文进入这里 |
| 查文献、法规、专利、公告、标准 | `literature_search` | 只允许 verified sources |
| 独立质疑、找反例、检查风险 | `independent_critic` | 可并行多个 critic |
| 汇总、归纳、构造候选结论 | `synthesis` | 生成结构化中间对象 |
| 人工确认、审批、伦理/安全确认 | `human_approval` | 高风险步骤必须进入这里 |
| 写报告、导出文件、生成审计材料 | `report_write` | 输出正式 artifact |

### Step 3：设计 WorkflowIR

一个最小 IR 应该包含：

- `schema_version`
- `objective`
- `nodes`
- `edges`
- `conditional_edges`
- `policies`

示例：合规审查 harness 的最小 IR。

```json
{
  "schema_version": "v1",
  "objective": "审查供应商合同是否满足数据处理与审计要求",
  "nodes": [
    {
      "id": "read_contract",
      "kind": "workspace_read",
      "inputs": {
        "artifact_type": "contract",
        "required_sections": ["data_processing", "audit_rights", "subprocessors"]
      },
      "budget": {"cost_usd": 0.05}
    },
    {
      "id": "search_policy",
      "kind": "literature_search",
      "inputs": {
        "source_set": "verified_policy_sources",
        "query": "data processing agreement audit rights subprocessors"
      },
      "budget": {"cost_usd": 0.25}
    },
    {
      "id": "critic",
      "kind": "independent_critic",
      "depends_on": ["read_contract", "search_policy"],
      "inputs": {"focus": "missing controls, contradictory clauses, unsupported claims"},
      "budget": {"cost_usd": 0.3}
    },
    {
      "id": "synthesize_findings",
      "kind": "synthesis",
      "depends_on": ["critic"],
      "inputs": {"output_schema": "ComplianceFindingDeck"},
      "budget": {"cost_usd": 0.35}
    },
    {
      "id": "legal_approval",
      "kind": "human_approval",
      "depends_on": ["synthesize_findings"],
      "inputs": {"approver_role": "legal_reviewer"}
    },
    {
      "id": "write_report",
      "kind": "report_write",
      "depends_on": ["legal_approval"],
      "inputs": {"format": "markdown"}
    }
  ],
  "edges": [
    {"from_node": "read_contract", "to_node": "critic"},
    {"from_node": "search_policy", "to_node": "critic"},
    {"from_node": "critic", "to_node": "synthesize_findings"},
    {"from_node": "synthesize_findings", "to_node": "legal_approval"},
    {"from_node": "legal_approval", "to_node": "write_report"}
  ],
  "conditional_edges": [],
  "policies": {
    "provenance_enabled": true,
    "max_cost_usd": 2.0,
    "allowed_skills": ["contract_reader", "verified_policy_search", "compliance_critic"],
    "network_access": "verified_sources_only",
    "max_subagents": 3,
    "max_iterations": 5,
    "requires_human_approval": true,
    "critic_count": 1,
    "source_breadth": "standard"
  }
}
```

### Step 4：让 IR fail-closed

`keel.ir.validator.validate()` 当前有 7 条硬规则：

1. `schema_version` 必须是 `v1`。
2. 每个 `node.kind` 必须在 6 类白名单中。
3. `node.inputs["skill"]` 必须在 `policies.allowed_skills` 中。
4. `provenance_enabled` 必须为 `true`，`max_cost_usd` 必须在允许范围内。
5. `conditional_edges` 不能包含自由代码标记，例如 `lambda`、`eval`、`exec`。
6. 图必须是 DAG，所有引用的 node id 必须存在。
7. 如果 `requires_human_approval=true`，必须存在 `human_approval` 节点。

调用方不要把 validation error 当 warning。高责任 harness 的默认行为应该是拒绝执行，并返回结构化错误。

### Step 5：实现 domain adapter

adapter 负责把产品 payload 转成 `WorkflowIR`。它应该放在宿主平台层，而不是放进 `rso-keel` core。

adapter 的职责：

- 校验用户是否有权访问项目和来源。
- 把 UI payload / API payload 转为领域对象。
- 选择或构造 `WorkflowIR`。
- 绑定 `WorkflowTemplate` 时，从服务端 registry 读取 canonical hash，不信任客户端传入 hash。
- 写入 plan record 或 job payload，保留 `user_id`、`project_id`、`plan_id`、`template_id`、`version`、`content_hash`。
- 转换失败时 fail-closed；只有显式开启 fallback 时才能走 legacy。

adapter 不应该：

- 让客户端直接提交任意 IR 并执行。
- 从自然语言 prompt 中推断权限。
- 把用户上传文件默认放入跨项目知识库。
- 在 Keel core 里 import 平台数据库或业务模型。

### Step 6：实现 node handlers

handler 是真正调用模型、工具、检索、文件系统或报告生成器的地方。Keel compiler 接收 `node_id -> handler` 映射，把 IR 编译成 LangGraph graph。

所有 handler 应该输出或转换为 `HandlerOutput`：

- `summary`
- `generated_files`
- `warnings`
- `next_step`
- `tokens_in`
- `tokens_out`
- `model_usage`
- `output_digest`
- `metadata`

handler 设计规则：

- 输入只读当前 node 需要的 state，不隐式读取全局环境。
- 输出结构化，不把正式结果藏在自然语言段落里。
- 所有生成文件必须有 path；能算 hash 时写 `content_hash`。
- 模型使用必须进入 `model_usage` 或至少写 token 汇总。
- 工具调用失败要返回可追踪错误，不要吞异常。
- 不要让 handler 自己决定绕过 HumanGate。

### Step 7：加入 gates

Keel v1 已有三类基础门：

- `validate(ir)`：schema 和安全底线。
- `DeterministicGate`：无外部调用的结构检查，例如是否有数据源节点、是否缺 HumanGate。
- `RulesGate`：成本、skill allowlist、source breadth、critic count 等规则检查。

建议执行顺序：

```text
payload
  -> adapter
  -> WorkflowIR
  -> validate(ir)
  -> DeterministicGate.check(ir)
  -> RulesGate.check(ir)
  -> PolicyPreflightReport
  -> compile + execute
```

任何 gate fail，都应该停止执行。把 gate result 写进 job result/provenance，方便用户知道是输入问题、权限问题、成本问题还是 workflow 结构问题。

### Step 8：设计 HumanGate

凡是高责任动作，都应该有 `human_approval`：

- 发布正式结论。
- 进入外部提交。
- 建议湿实验、临床、合规例外或重大财务判断。
- 把动态 workflow 固化为模板。
- 把项目内发现发布到跨项目知识库。

HumanGate 的审批 UI 不应该只给“同意/拒绝”。建议包含：

- 系统建议。
- 证据摘要。
- 缺失证据。
- 风险与限制。
- 预期后果。
- 审批人修改意见。
- 决策：approve / reject / revise / escalate。

审批结果必须进入 provenance。resume 时必须重新校验 owner、project 和 plan record，不能只凭 plan id 续跑。

### Step 9：记录 provenance

一个 Keel-backed job 至少要能回答：

- 谁触发了执行。
- 用了哪个 `WorkflowIR`。
- IR hash 是什么。
- 用了哪个 template、version、content hash。
- 每个 node 的状态、耗时、模型使用和错误。
- 哪些人工审批发生过。
- 哪些文件被生成。
- 是否 fallback。
- 哪些警告或 integrity flags 存在。

`PlanProvenance` 的 floor fields 包括：

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

不要把 provenance 当日志。日志用于调试；provenance 用于复现、审计和责任边界。

### Step 10：用 TemplateSpec 沉淀 workflow

一次表现好的动态 workflow 不应该直接变成全局默认。推荐生命周期：

```text
ephemeral run
  -> draft TemplateSpec
  -> reviewed template
  -> project-scoped reuse
  -> approved template
  -> broader reuse
  -> deprecated / rollback
```

`TemplateSpec` 提供：

- `template_id`
- `version`
- `status`: `draft | reviewed | approved | deprecated`
- `ir_skeleton`
- `content_hash`
- `reviewed_at`
- `approved_at`
- `deprecated_at`
- `tags`

规则：

- `content_hash` 必须由 canonical `ir_skeleton` 计算。
- reviewed/approved 模板不可原地修改；变更要创建新版本。
- job 绑定模板时必须记录 template id、version、content hash。
- rollback 应支持 domain 级和 template 级。
- approved 之前必须有指标、人工证据和失败样本。

### Step 11：定义指标和 rollout 门槛

可信 harness 不能只看“跑通”。至少要看：

- success rate。
- fallback rate。
- resume success rate。
- provenance completeness。
- generated file rate。
- human revision rate。
- token/cost median 和 p95。
- source verification pass rate。
- false positive / false negative 样本。
- template adoption rate。
- rollback count。

上线策略：

1. 本地单元测试。
2. 集成测试。
3. opt-in 灰度。
4. 小范围默认。
5. 全域默认。
6. legacy fallback 降级为 emergency path。
7. 移除平行入口。

每一步都要有回滚条件。不要用“CI 绿”替代生产灰度指标。

## 6. 四类可复用 harness 模式

### 6.1 Evidence Review Harness

适合论文审查、政策审查、合规审查、专利审查。

典型流程：

```text
workspace_read
  -> literature_search
  -> independent_critic
  -> synthesis
  -> human_approval
  -> report_write
```

核心对象：

- Source
- Claim
- Evidence
- Finding
- Risk
- ReviewerDecision
- Report

最低门槛：

- 每条 finding 必须绑定 source。
- unsupported claim 只能进入 warnings 或 hypothesis，不得进入 final conclusion。
- final report 必须记录 template/version/hash。

### 6.2 Recommendation Harness

适合实验建议、修复建议、投资建议、工程变更建议。

典型流程：

```text
workspace_read
  -> literature_search
  -> synthesis
  -> independent_critic
  -> human_approval
  -> report_write
```

核心对象：

- Candidate
- ExpectedOutcome
- DecisionRule
- CostRisk
- EvidenceLink
- Approval

参考 `ExperimentCard` 的设计：建议必须包含目的、材料/资源、预期结果、判定规则、风险限制和证据链接。它应该是可审查建议，不是自动执行命令。

### 6.3 Audit Trail Harness

适合安全评估、模型评测、质量体系、财务审计。

典型流程：

```text
workspace_read
  -> independent_critic
  -> synthesis
  -> human_approval
  -> report_write
```

核心对象：

- Control
- Observation
- Evidence
- Exception
- Remediation
- AuditDecision

最低门槛：

- 每个 exception 必须有 evidence。
- 每个 remediation 必须有 owner 和 due date。
- final artifact 必须可从 provenance 重建。

### 6.4 Knowledge Accumulation Harness

适合跨项目知识库、经验沉淀、负结果库、模板推荐。

典型流程：

```text
workspace_read
  -> synthesis
  -> human_approval
  -> report_write
```

核心对象：

- Finding
- NegativeResult
- ReusableTemplate
- Scope
- Permission
- RetentionPolicy

最低门槛：

- 默认项目内可见。
- 跨项目使用必须显式授权。
- 负结果和失败样本也要沉淀。
- 模板推荐只能建议，自动绑定必须受 metrics gate 和 rollback 控制。

## 7. 最小开发切片

不要一开始做通用平台。推荐第一个 PR 只做一条窄路径：

1. 选一个 domain，例如 `compliance_review`。
2. 定义一个 API payload。
3. 写 adapter：payload -> `WorkflowIR`。
4. 写 3-5 个 node handlers。
5. 所有 handler 输出 `HandlerOutput`。
6. 接入 `validate`、`DeterministicGate`、`RulesGate`。
7. 有 HumanGate。
8. 写一个 markdown artifact。
9. result/provenance 记录 plan id、IR hash、template hash、node traces、model usage。
10. 加测试覆盖 success、validation failure、forbidden skill、missing HumanGate、fallback、resume ownership。

第一个切片的验收标准：

- 没有动态任意代码执行。
- 没有无来源强结论。
- 没有绕过人工审批的高风险动作。
- 失败时 fail-closed。
- 每个正式产物都能追溯到 plan/template/source。

## 8. 测试清单

Core tests：

- IR schema parse。
- validator 7 条规则。
- DAG / dangling edge / cycle。
- forbidden skill。
- network access conflict。
- missing HumanGate。
- policy preflight。
- runtime cost guard。
- HandlerOutput serialization。
- TemplateSpec content hash immutability。

Host integration tests：

- project ownership。
- plan record owner。
- resume owner。
- generated files persistence。
- billing/model usage。
- fallback result/provenance。
- template binding canonical hash。
- template rollback。
- metrics aggregation。

Live/e2e tests：

- 一条真实 job 跑通。
- HumanGate pending -> approve -> resume。
- 生成 artifact 可打开。
- provenance 字段完整。
- 关闭 Keel 默认或 template rollback 后能回退。

## 9. 常见错误

错误：把 Keel 当 agent framework。

正确：Keel 是 workflow governance 层。Agent 可以是 handler 内部实现，但不能替代 IR、gate、provenance 和 template。

错误：让客户端提交完整 IR。

正确：客户端只能提交领域 payload 或显式 template binding；服务端 adapter 生成 canonical IR。

错误：把所有模型输出直接写进报告。

正确：模型输出先转结构化对象，经过 critic、gate、source binding 和人工确认后再进入正式 artifact。

错误：把 HumanGate 当 UI 按钮。

正确：HumanGate 是 plan lifecycle 的中断点和责任边界，必须能恢复、审计和校验 owner。

错误：模板只存名字。

正确：模板必须有 version、content hash、status、review/approve/deprecate 生命周期。

错误：上线后再想回滚。

正确：domain fallback、template rollback、metrics gate 和 provenance 从第一天就要设计。

## 10. 何时扩展 Keel core

优先不要扩 core。大多数新 harness 应该只新增宿主层 adapter、handler、template 和 UI。

可以考虑扩 core 的情况：

- 多个 domain 都需要同一个新 node kind。
- 现有 6 类 node 无法安全表达某种基础控制流，并且这个缺口在多个 domain 中重复出现。
- 需要新的 provenance floor field。
- 需要新的 policy gate。
- 需要新的可复用高责任对象 schema。

扩 core 必须同时做：

- bump `schema_version`。
- 更新 Pydantic schema。
- 更新 validator。
- 更新 compiler。
- 更新 provenance。
- 更新 tests。
- 写迁移和兼容策略。
- 明确 v1/v2 template 如何共存。

不要为了一个产品页面的便利扩 core。

## 11. 建设者原则

- 先定义责任对象，再写 agent。
- 先做 fail-closed，再做 fallback。
- 先记录 provenance，再做自动化。
- 先项目内 reviewed，再跨项目 approved。
- 先窄域跑出指标，再扩 domain。
- 先把动态 workflow 固化为模板，再考虑自动推荐。
- 先让人能审计，再让模型更自主。

如果一个 harness 不能回答“这条结论从哪里来、谁确认过、用了哪个版本、失败怎么回滚、下次如何复用”，它还不是可信 harness，只是一个会生成文本的工具。
