# Case Study：RSO 如何迁移到 rso-keel 单一编排架构

日期：2026-06-11

本文记录 `rso-keel` 在 RSO 真实产品中的采用案例。它不是概念 demo，而是从 legacy runner + opt-in `rso-keel` 的双路径，迁移到 review/reference/patent/lab 默认 `rso-keel` 编排的生产路径。

公开版只保留可复用的架构经验；内部迁移 PR 顺序、生产配置和部署细节不随首版开源仓库发布。

## 1. 初始问题

RSO 原有后台任务逐渐形成多个并行路径：

- legacy review runner。
- Keel opt-in review path。
- reference import path。
- patent workflow path。
- lab experiment proposal path。

短期双路径有价值，因为它允许 Keel 在真实负载下灰度。但长期会造成系统分裂：

- 两套 job lifecycle。
- 两套 progress/generated files 语义。
- 两套 provenance。
- 两套 billing/model usage 汇总。
- resume/ownership 安全边界不一致。
- fallback 行为分散在不同 worker 分支。
- 新 workflow 无法统一沉淀为 template。

## 2. 关键风险不是“能不能跑”

迁移前最重要的判断是：最高风险不是缺少功能，而是生产责任链不完整。

早期发现的关键缺口包括：

- resume job 在 worker 分支顺序上可能被 `project_id is None` 拦截。
- `/api/keel/review` 需要 project ownership 校验。
- `/api/keel/resume` 不能只凭 `plan_id` 续跑，必须校验 owner/project。
- checkpoint metadata 不能承载完整 IR，需要 plan record 作为单一真相源。
- handler 输出必须统一，否则 provenance/billing/generated files 会继续分裂。

这些问题即使不继续开发 Keel，也属于 production safety 问题。

## 3. 迁移策略

RSO 没有直接删除 legacy runner，而是把旧实现逐步降级为 Keel handler。

目标架构：

```text
TaskJob
  -> WorkflowTemplate or WorkflowIR
  -> Keel graph
  -> registered handlers
  -> unified provenance / billing / progress / generated_files
```

迁移原则：

- 先收口安全边界，再默认切换。
- 先让 legacy runner 成为 handler，再删除平行 lifecycle 语义。
- 先有 rollback，再扩大默认范围。
- 先有 metrics，再谈自动模板绑定。
- Keel core 保持零平台 import。

## 4. PR 序列的核心阶段

实际迁移被拆成多个小 PR，核心阶段如下：

| 阶段 | 目标 |
|---|---|
| PR-0 | 修正测试基线，确保 backend 和 `rso-keel` 独立测试可运行 |
| PR-1a | P0 ownership 安全修复，包含 review/resume owner metadata |
| PR-1b | plan record、resume 分支重排、checkpoint 轻量引用 |
| PR-2 | provenance/resume/token/progress 回归测试 |
| PR-3 | `HandlerOutput` 和 legacy review handler adapter |
| PR-4 | `WorkflowTemplate` registry 和 content hash |
| PR-5 | review 默认 Keel |
| PR-6 | reference 默认 Keel |
| PR-7 | patent 默认 Keel |
| PR-8 | policy preflight / runtime cost guard |
| PR-9 | lab ExperimentCard workflow |
| PR-10~15 | dynamic workflow promotion, template reuse, approval, rollback, recommendation |
| PR-16~20 | recommendation API, metrics API, admin diagnostics, auto-bind gate, observability |
| PR-21~22 | full CI regression gate and GitHub Actions runtime maintenance |

关键不是 PR 数量，而是排序：先安全和测试，再默认切换，再模板和指标。

## 5. 最重要的架构改变

### 5.1 HandlerOutput 成为单一输出契约

所有 handler 输出统一为：

- summary。
- generated files。
- warnings。
- next step。
- tokens in/out。
- model usage。
- output digest。
- metadata。

这让 provenance、billing、generated files、UI 和 metrics 不再依赖每个 runner 的私有结构。

### 5.2 Plan record 成为 resume 的权威上下文

LangGraph checkpoint metadata 只保存轻量引用：

- plan id。
- job id。
- plan record id。
- IR hash。

完整 owner/project/template/IR context 存在平台 plan record 中。这样 resume 可以做 owner 校验，也避免把完整 IR 重复写入 checkpoint metadata。

### 5.3 WorkflowTemplate 让成功经验可沉淀

动态 workflow 或人工编辑后的 workflow 不能直接全局复用。它必须经历：

```text
draft
  -> reviewed
  -> approved
  -> deprecated
```

每个 job 记录 template id/version/content hash，支持模板级 rollback。

### 5.4 Lab-in-loop 被建模为 reviewable card

Lab workflow 不输出可直接执行 SOP，而输出可审查的 Experiment Card：

- purpose。
- hypothesis。
- materials。
- expected results。
- controls。
- decision rules。
- safety/ethics flags。
- evidence links。

这避免系统越权成为实验执行者。

## 6. 测试与 CI

迁移后补齐了 full regression gate：

- backend Postgres/Redis 集成测试。
- `rso-keel` 独立包测试。
- frontend lint/type/build。

CI 不再只跑 Keel 子集，而是覆盖真实 DB 集成路径。它曾立即暴露出 project 未 flush 就创建 TaskJob 外键引用的潜伏问题，证明全量门禁不是摆设。

Keel core 还通过 import boundary 测试，确保不依赖平台代码。

## 7. 生产状态

截至 2026-06-11，RSO 的状态：

- review/reference/patent/lab 默认经 Keel 编排。
- legacy runner 降级为 Keel handler 或 fallback path。
- HumanGate resume ownership-safe。
- generated files、billing、provenance 使用统一契约。
- job 可绑定不可变 WorkflowTemplate version/hash。
- admin diagnostics 和 rollout metrics 已接入。
- GitHub Actions full CI gate 绿色。

## 8. 经验教训

### 8.1 不要先做大重构

迁移成功的原因是先补安全边界和测试，而不是先删除旧代码。

### 8.2 不要把 CI 绿当生产完成

CI 证明代码路径可运行，但生产默认切换仍需要 rollout metrics、fallback 演练和持续观察。

### 8.3 不要让 dynamic workflow 直接成为默认

动态 workflow 必须经过 review、metrics 和 template hardening，才能从一次性执行进入复用。

### 8.4 不要把 HumanGate 做成 UI 状态

HumanGate 必须是 workflow interrupt/resume 的一部分，否则审批和执行会分裂。

### 8.5 不要让 core import platform

Keel 能成为开源候选，前提是 core 保持平台无关。平台适配属于 bridge 层。

## 9. 为什么这个案例重要

很多 agent 框架 demo 能跑通单次任务，但没有经历：

- 多路径 legacy migration。
- owner/resume 安全修复。
- generated files/billing/provenance 统一。
- default backend rollout。
- template-level rollback。
- full DB integration CI。
- production diagnostics。

RSO case study 说明 `rso-keel` 不是抽象概念，而是在真实产品里为 AI workflow 承担生产责任链的架构。
