# 如何评估一个 rso-keel Harness 是否可靠

日期：2026-06-11

`rso-keel` harness 的评价标准不是“模型回答得好不好”，而是“这个 AI workflow 是否能被组织安全采用、持续改进、出错回滚”。

## 1. 四层评估

```text
Layer 1: Structural correctness
Layer 2: Execution reliability
Layer 3: Output accountability
Layer 4: Production adoption
```

四层都过，才算可靠。

## 2. Layer 1：结构正确性

目标：workflow 在执行前就是合法的。

必须检查：

- `WorkflowIR` schema parse。
- validator 7 条规则。
- DAG 无环。
- node id 引用存在。
- allowed skills。
- cost ceiling。
- network access policy。
- required HumanGate。
- no free-code conditional edges。

推荐指标：

- invalid IR rejection rate。
- validation error taxonomy。
- policy preflight pass/fail count。

最低要求：

- 非法 IR fail-closed。
- validation failure 不 enqueue job。
- 错误结构化返回给调用方。

## 3. Layer 2：执行可靠性

目标：合法 workflow 能稳定运行、暂停、恢复、失败可解释。

必须检查：

- handler registry 完整。
- checkpoint/resume 正常。
- HumanGate pending -> approve/reject/revise。
- owner/project resume 校验。
- generated files 写入。
- model usage 汇总。
- runtime cost guard。
- handler failure provenance。
- fallback path。

推荐指标：

- job success rate。
- resume success rate。
- fallback rate。
- node failure rate。
- generated file rate。
- median/p95 latency。
- median/p95 cost。

最低要求：

- resume 成功率可观测。
- handler failure 不丢 provenance。
- fallback_used 必须进入 result/provenance。

## 4. Layer 3：输出可问责

目标：正式产物能解释来源、版本、审批和限制。

必须检查：

- artifact -> job -> plan id 可追踪。
- plan id -> WorkflowIR hash 可追踪。
- template id/version/content hash 可追踪。
- node traces 完整。
- source ids 完整。
- warnings 和 limitations 未被吞掉。
- HumanGate decision 可追踪。
- unsupported claims 不进入 final conclusion。

推荐指标：

- provenance completeness。
- source verification pass rate。
- unsupported claim count。
- human revision rate。
- warning rate。
- severe missing evidence count。

最低要求：

- 缺 `plan_id`、IR hash、node traces 视为严重缺陷。
- 无来源强结论不得进入正式报告。

## 5. Layer 4：生产采用

目标：workflow 可以灰度、放量、回滚、沉淀。

必须检查：

- template registry。
- template status lifecycle。
- template-level rollback。
- domain-level rollback。
- rollout metrics。
- auto-bind gate 默认关闭。
- metrics gate 开启后可解释 selected/skipped。
- approved template 有 review evidence。

推荐指标：

- template adoption rate。
- template rollback count。
- auto-bind selected/skipped count。
- success rate vs legacy baseline。
- cost delta vs legacy baseline。
- user open/adoption rate。
- post-run manual correction rate。

最低要求：

- 不能用 CI 绿替代生产灰度。
- 缺 legacy baseline 时，默认判 `insufficient_data`，不能判 pass。

## 6. Gold set

高责任 harness 应该有 gold set。

Gold set 应包含：

- 成功样本。
- 失败样本。
- 边界样本。
- 缺来源样本。
- 需要 HumanGate 的样本。
- 应触发 fallback 的样本。
- 应拒绝执行的非法 IR。

每个样本至少记录：

- input。
- expected decision。
- expected evidence。
- expected warnings。
- expected artifact shape。
- reviewer notes。

## 7. Red-team scenarios

建议持续测试：

- 客户端伪造 template hash。
- 跨项目 resume plan。
- IR 引用 forbidden skill。
- LLM 生成条件边包含 `eval` / `exec`。
- workflow 缺 source node。
- HumanGate 被绕过。
- handler 输出 generated file 但文件不存在。
- model usage 缺失。
- fallback 后 provenance 丢失。
- approved template skeleton hash drift。

## 8. Release gate

一个新 `rso-keel` harness 默认开启前，建议满足：

- structural tests pass。
- integration tests pass。
- at least one live e2e pass。
- provenance completeness >= 99%。
- resume success rate >= 95% in test/canary sample。
- generated file rate no worse than baseline。
- median cost no more than 25% above baseline unless explicitly approved。
- fallback tested。
- rollback tested。
- owner signs off。

## 9. Evaluation principle

不要只评估模型输出。

评估对象应该是完整责任链：

```text
input
  -> IR
  -> gates
  -> execution
  -> human decisions
  -> artifacts
  -> provenance
  -> metrics
  -> template lifecycle
  -> rollback
```

一个 harness 只有在这条链上可靠，才值得默认开启。
