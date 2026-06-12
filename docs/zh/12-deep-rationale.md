# 为什么要做 rso-keel：模型越强，科研越需要龙骨

日期：2026-06-11

本文是一份战略与架构论证，不是迁移执行计划。公开版只讨论为什么需要 `rso-keel`，不包含内部 PR 顺序、生产配置或部署细节。

调研范围覆盖 2024-2026 年 AI for Science、coding agent、多 Agent research、科研幻觉治理和企业级 agentic R&D 平台的公开论文、产品发布与工程文章。

## 结论先行

RSO 做 rso-keel，不是因为我们认为自己能比大模型公司更会“生成答案”，也不是因为要复制一个端到端 AI Scientist。rso-keel 的核心判断是：

> AI for Science 的瓶颈正在从“模型能不能想到”转向“组织能不能信、复现、审计、回滚、沉淀”。

模型能力越强，单次推理越像黑箱，输出越流畅，组织越容易把“看起来合理”误当成“可以承担科研责任”。科研系统不能只服务 prompt，它必须服务研究责任链：问题从哪里来，证据从哪里来，假设为什么成立，实验为什么值得做，谁确认过，失败如何回滚，成功如何沉淀为可复用流程。

这就是 rso-keel 的位置：不是更大的模型，而是科研工作流的龙骨。它把模型、检索、工具、人工判断、实验建议、产物生成和审计证据装进同一套可追溯、可测试、可回滚、可演进的执行框架。

## 1. 背景：AI for Science 已进入 agentic R&D 平台阶段

过去几年，AI for Science 的主轴已经从单点模型能力，扩展到多 Agent、实验闭环、组织治理和知识积累。

### 1.1 专用科学模型正在证明“模型能力轴”有效

AlphaFold 3 代表的是强专用模型方向。Nature 论文说明它可以预测蛋白质、核酸、小分子、离子和修饰残基等复合体结构，覆盖生命分子相互作用的更大范围；Isomorphic Labs 也把它定位为预测生命分子结构和相互作用的系统。这类工作证明：当问题边界清晰、训练信号和评估方式足够强时，科学专用模型可以产生巨大价值。

但 AlphaFold 3 也说明了另一件事：真正可用于科研生产的系统，不只是模型本身，还包括输入约束、适用边界、验证方式、结果解释和下游实验衔接。模型能力是必要条件，不是组织采用的充分条件。

### 1.2 Agentic discovery 正在从“生成想法”走向“闭环发现”

FutureHouse 的 Robin 以端到端科学发现为目标，Nature 论文把科学发现描述为观察、假设、实验和数据分析的迭代过程，并展示 Robin 自动化假设生成和实验数据分析。公开介绍中，Robin 找到了青光眼药物 ripasudil 可能用于干性 AMD 的新候选方向。这件事的启发不是“模型碰巧猜中了一个药”，而是它把文献、机制、候选假设、实验数据分析和下一轮判断串成了闭环。

Google DeepMind 的 AI Co-Scientist 进一步把“假设空间探索”做成多 Agent 系统。它使用 Generation、Proximity、Reflection、Ranking、Evolution、Meta-review 等 Agent，让假设在生成、辩论、排序和演化中迭代；Google 明确强调它是科研合作者，不替代研究者，用户仍然对输出负责。

Sakana AI 的 AI Scientist-v2 则从线性生成转向 agentic tree search。它把科学想法、实验设计、代码实现、论文写作和评审过程串起来，并报告了 AI 生成论文被 workshop 接收的案例。核心启发是：科研假设不是一次生成 N 个候选再排序，而更像搜索树，需要分支、剪枝、深化、回溯和持久化。

### 1.3 企业级竞品已经把“agentic 科研平台”推到生产叙事

Microsoft Discovery 在 Build 2026 推向 GA，定位是面向科学和工程 R&D 的企业级 agentic AI 平台。微软的公开材料强调：R&D 流程需要机构知识、领域专业、专用工具、实验证据、验证流程和可复现审查；系统设计要保留人类判断中心，帮助专家理解 reasoning path；Discovery Engine 支持从证据到假设、再到执行、分析和下一轮迭代的循环。

这对 RSO 是直接信号：大厂已经不再把 AI for Science 只当模型演示，而是把它包装成企业 R&D 操作系统。RSO 如果只做“更好的生成”，没有优势；如果做的是学术友好、中文场景友好、论文审查/专利/文献/实验建议可追溯的轻量科研龙骨，才有差异化空间。

### 1.4 跨 Agent 知识积累正在成为平台能力

AgentRxiv 的思路很直接：多个 Agent Lab 把自己的发现上传到共享 preprint server，新 Agent 在探索前检索已有发现，避免重复劳动并累积知识。ETH Zurich 的报告显示这种共享机制能带来相对性能提升。

这说明“发现”本身需要平台化记忆。单个任务内的上下文窗口会过期，单个项目内的经验会孤立。RSO 的 project memory、template registry、workflow version 和 provenance，如果扩展为授权的跨项目知识层，就不是附属功能，而是科研平台的核心资产。

### 1.5 Coding agent 的快速进步不能直接外推到科研

Claude 的 dynamic workflows、Anthropic 的 multi-agent research system、SWE-bench、METR time horizon 等进展说明：coding agent 正在快速变强。Anthropic 报告多 Agent research 在内部评估中比单 Agent 高 90.2%，并且 token 使用量解释了大部分性能差异；METR 用“人类专家完成任务所需时长”衡量 AI 在软件任务上的时间 horizon；SWE-bench Verified 用真实 GitHub issue 和单元测试作为评估基准。

这些进展很重要，但不能简单推出“科研也会像 coding 一样被 agent 接管”。原因在下一节。

## 2. 为什么科研与 coding 不同

科研和 coding 都可以拆成任务、上下文、工具调用和产物生成，但它们的验证结构完全不同。

### 2.1 Coding 有廉价、可执行、即时的 oracle

软件任务通常有编译器、类型检查、单元测试、集成测试、lint、容器复现和线上指标。SWE-bench 之所以能成为 coding agent 的关键评估，是因为任务可以在隔离 Docker 环境中运行，并用测试结果判断是否解决。即使测试不完美，它仍然提供了一个廉价、自动化、可重复的反馈回路。

这使 coding agent 可以大胆试错：生成 patch，运行测试，读失败日志，修复，再运行。模型能力提升后，软件系统可以把更多探索交给 Agent，因为 verifier 足够便宜。

### 2.2 科研的 oracle 昂贵、延迟、噪声大，且经常不唯一

科研假设的验证往往依赖实验、临床数据、长期观察、同行评审、统计复现或跨实验室验证。验证周期可能是天、月甚至年；数据可能有批次效应、样本偏差、仪器噪声、发表偏倚；一个实验失败也不必然推翻假设，一个实验成功也不必然证明机制。

因此，科研系统不能像 coding 那样把“测试通过”当成主要闭环。它更需要管理：

- 证据链：每条 claim 对应哪些来源、数据和限制。
- 假设链：从证据到机制，再到可检验预测的推理路径。
- 决策链：谁批准了下一步，为什么值得消耗实验资源。
- 失败链：失败是方法问题、数据问题、假设问题，还是执行问题。

### 2.3 科研的错误成本不是局部 bug，而是知识污染

代码 bug 通常能通过测试、回滚和监控定位到具体版本。科研错误更隐蔽：错误引用、幻觉机制、过度外推、统计误读、重复发表、低质量证据包装成强结论，都会污染后续研究。Nature 已经报道过 AI 生成无效参考文献进入学术出版生态的问题；医学和生命科学领域对 LLM 引文幻觉也有系统性综述。

这意味着科研系统的第一责任不是让模型“说得更像专家”，而是防止不可追溯的专家腔调进入正式知识链。

### 2.4 科研的产物不是答案，而是可承担责任的研究对象

论文审查、专利分析、文献综述、实验建议、药物再定位、机制假设，都不是一次性答案。它们应当是带状态的研究对象：

- 谁创建。
- 用了哪个模型、哪个模板、哪个版本的 workflow。
- 引用了哪些来源。
- 哪些 claim 被支持、反驳或未验证。
- 哪些步骤经过人工确认。
- 哪些产物进入了项目记忆或跨项目知识库。

coding 的核心对象是 patch；科研的核心对象是 claim、evidence、hypothesis、experiment、decision 和 artifact 的组合。

## 3. 为什么模型越强，越需要 Keel

一个常见误解是：等模型足够强，平台层就不重要了。实际情况相反。

### 3.1 模型会吞掉“技巧”，但吞不掉“责任边界”

更强的模型会让 prompt engineering、固定流程、浅层评分规则快速贬值。今天写死的 heuristic，明天可能被模型自己规划得更好。

但以下能力不会因为模型变强而消失：

- 租户隔离和权限。
- 来源可信度和引用可验证。
- workflow 版本和模板不可变性。
- 人工确认点和审批记录。
- 成本、token、模型使用、产物 digest。
- fallback 和回滚。
- 跨任务、跨项目、跨用户的经验沉淀。
- 生产灰度和指标门槛。

这些不是“模型不够聪明时的补丁”，而是科研组织使用 AI 的基础设施。

### 3.2 模型越会规划，越需要可审计的动态 workflow

未来的模型会更擅长自动生成任务内 workflow：自己决定先查什么、问谁、跑哪个工具、比较哪些假设、建议哪些实验。Anthropic 的 dynamic workflows 已经在 coding 和 research 场景中展示了这种方向：模型可以规划工作，调度大量子 Agent，并验证输出。

但科研里不能让动态 workflow 直接变成不可控的黑箱执行。正确形态应该是：

1. 模型在任务内提出 workflow。
2. 系统把 workflow 编译成结构化 IR。
3. validator 检查权限、工具、数据来源、预算、风险和人工确认点。
4. 人类确认高风险步骤。
5. 执行过程完整记录 provenance。
6. 被证明有价值的 workflow 固化为跨任务、跨用户可复用模板。

这就是 Keel 的核心价值：允许模型动态生成流程，同时把动态流程关进可验证、可审计、可回滚的轨道。

### 3.3 假设发现不是运气，而是可复刻的“受约束搜索”

Robin 找到 ripasudil 的启发，不应被理解为“模型运气好”。更准确地说，它复刻了一类高质量科研直觉：

- 在已有文献中寻找被低估的机制连接。
- 把疾病表型、通路、药物靶点和实验可行性连接起来。
- 优先选择安全性、可获得性、机制可解释性较好的候选。
- 用实验或数据分析尽快排除弱假设。

所谓“低垂的果实”通常不是随机出现的，而是来自一个受约束的搜索空间：旧药物、新适应症、已知安全性、可测机制、已有矛盾证据、被不同领域割裂的知识。

Keel 要复刻的不是某一次发现，而是这种搜索结构：

- 明确 problem framing。
- 构建候选空间。
- 给每个候选绑定 evidence 和 missing evidence。
- 用 tree search / tournament / meta-review 竞争假设。
- 把实验成本、可行性和预期信息增益纳入排序。
- 将失败结果沉淀为负证据，避免重复探索。

模型负责扩展搜索和提出连接；Keel 负责让搜索可追溯、可剪枝、可复用。

## 4. Keel 是什么，不是什么

### 4.1 Keel 不是“另一个 AI Scientist”

Keel 不应该竞争“谁能端到端发现新药”。这个方向会被 DeepMind、FutureHouse、Sakana、Microsoft、OpenAI、Anthropic 以及垂直科学模型公司持续推进。RSO 没有必要在通用模型能力上正面对抗。

Keel 的定位是科研工作流 control plane：

- 把研究任务表示为 typed IR。
- 把 IR 编译为可执行 graph。
- 把每个节点的输入、输出、来源、成本、模型和人工决策记录下来。
- 把动态 workflow 变成可审批、可版本化、可复用的 template。
- 把结果接入 RSO 的论文审查、专利分析、参考文献、实验建议和项目记忆。

### 4.2 Keel 不是模型 wrapper

如果只是把多个 LLM API 包成统一调用层，Keel 很快会变成薄而脆的中间件。Keel 真正不可替代的部分是模型外部的结构：

- HandlerOutput 统一契约。
- workflow template registry。
- durable job 和 resume。
- ownership 和 tenant boundary。
- provenance 和 audit trail。
- source registry 和 citation verification。
- metrics 和 rollout guardrail。
- HumanGate / LabGate。

这些能力在模型替换、工具替换、部署环境替换时都应保持稳定。

### 4.3 Keel 不是把科研“完全形式化”

科研的真理判断不能完全形式化。很多关键判断依赖背景知识、实验经验、领域直觉和外部现实。Keel 要形式化的是科研活动的骨架，不是真理本身。

可以形式化的是：

- 任务对象。
- 输入来源。
- claim 和 evidence 的绑定。
- 假设状态。
- 实验建议。
- 审批节点。
- 产物版本。
- 决策记录。
- 回滚与复现路径。

不能承诺形式化的是：

- 机制必然正确。
- 实验一定成功。
- 模型内在 reasoning 被完全证明。
- 引文存在就代表结论可靠。
- 评分高就代表科学价值高。

更准确的目标是 warranted science：系统不能证明结论为真，但可以证明这个结论在当前证据、假设、限制和审批链下是如何被提出、评估和推进的。

## 5. 如果服务形式化科研，应该服务什么

服务形式化科研，不是把科学家变成填表用户，也不是把所有研究压成固定 SOP。它应该把非形式化研究过程中的关键对象显式化。

### 5.1 最小研究对象模型

Keel 应该围绕以下对象建模：

- Problem：研究问题、边界、目标人群/对象、排除范围。
- Source：文献、数据库、专利、实验记录、机构知识库、用户上传材料。
- Claim：可被支持或反驳的具体断言。
- Evidence：支持 claim 的来源片段、数据、图表、统计结果和质量等级。
- Assumption：尚未验证但被 workflow 依赖的前提。
- Hypothesis：由 claim 和 assumption 组合出的可检验解释。
- Experiment：目的、材料、方法、预期结果、判定标准、风险和成本。
- Decision：人工或系统做出的推进、搁置、回滚、固化模板等决定。
- Artifact：论文审查报告、专利分析、文献综述、实验建议书、代码、表格、图。
- WorkflowTemplate：经过确认的可复用研究流程。

这些对象应当有 owner、version、status、provenance、created_by、model_usage、source_hash、content_hash 和 audit event。

### 5.2 Lab-in-loop 应该是结构化实验建议，不是“去做实验”一句话

当系统建议湿实验或干实验时，输出至少应包括：

- 目的：这个实验要区分哪些假设。
- 材料/数据：需要哪些样本、试剂、模型、数据库或计算资源。
- 方法：关键步骤、对照组、统计方法、失败条件。
- 预期结果：不同假设下分别预期看到什么。
- 判定标准：什么结果支持、削弱或推翻假设。
- 风险与限制：伦理、合规、成本、样本量、混杂因素、技术风险。
- 信息增益：为什么这个实验比其他实验更值得先做。
- 人工确认：谁确认可以进入执行。

这类 LabGate 是科研系统区别于普通聊天机器人的关键。它不替代实验室，而是让实验建议变成可审查、可比较、可追踪的研究决策。

### 5.3 从动态 workflow 到固化 workflow

模型能力提升后，任务内 workflow 会越来越多由模型自动生成。Keel 应该支持三层生命周期：

1. Ephemeral workflow：任务内临时生成，用于探索。
2. Reviewed workflow：人工确认后执行，有完整 provenance。
3. Hardened template：多次成功后固化为跨任务、跨用户可复用模板。

固化条件不能只看“用户觉得不错”。应至少包含：

- 成功率。
- 产物打开率或采用率。
- 人工修改率。
- 成本和耗时。
- provenance 完整率。
- 引用验证通过率。
- resume 成功率。
- fallback 使用率。
- 失败样本和已知边界。

这使 RSO 能把“某次 agent 表现好”转化为平台能力，而不是把经验留在聊天记录里。

## 6. 对 RSO 的产品和架构启发

### 6.1 产品差异化：不做大厂 Discovery 的缩小版

Microsoft Discovery 面向企业 R&D，天然会走 Azure、机构知识库、企业合规、多团队治理和大型客户路线。RSO 应该避开直接复制，选择更清晰的切入点：

- 中文学术场景。
- 论文审查、参考文献、专利、项目文档和实验建议。
- 学术团队和中小实验室可承受的部署与定价。
- 可解释、可追溯、可导出的审查报告。
- 对本地文件、项目工作区、用户授权知识库友好。
- 开源或半开放的 workflow/IR 核心，降低信任门槛。

### 6.2 架构原则：模型可换，龙骨不可散

Keel 架构应坚持：

- rso-keel 不 import 平台代码，保持可测试、可移植。
- 平台通过 bridge 调用 Keel，不把业务权限塞进 Keel core。
- 所有 workflow 都有 template/version/hash。
- 所有模型输出进入 HandlerOutput 或更细对象模型，不散落为自由 JSON。
- 所有高风险步骤有 HumanGate 或 LabGate。
- 所有来源进入 Source Registry，不允许无来源强 claim 进入正式报告。
- 所有默认切换走灰度指标和回滚门槛。

### 6.3 近期最值得做的能力

在当前迁移已经把 Keel 作为默认执行路径之后，下一阶段不应继续堆“更聪明的生成”，而应补齐科研系统的责任层：

- rollout metrics UI：让 §13 指标可见，而不是只在文档里。
- provenance explorer：用户能追踪报告中每条结论来自哪个节点、来源和模型。
- source registry：文献、专利、数据库、上传材料统一登记、去重、hash 和可信度标注。
- dynamic workflow approval：模型提出 workflow，人类确认后执行。
- workflow hardening：把高质量动态 workflow 固化为 template。
- LabGate：实验建议卡片化，包含目的、材料、预期结果、判定标准和信息增益。
- cross-project memory：在用户授权下共享发现、负结果和模板，形成 RSO 版 AgentRxiv。
- hypothesis search：从“生成 N 个假设”升级为 tree search / tournament / pruning / deepen。

## 7. 红线

为了避免 RSO 变成不可控的 AI 科研幻觉系统，Keel 需要明确红线：

- 不承诺模型证明了科学真理。
- 不把模型 chain-of-thought 当成可审计证据。
- 不让无来源 claim 进入正式报告。
- 不让动态 workflow 绕过权限、预算、工具白名单和人工确认。
- 不把 coding benchmark 的“测试通过”叙事直接套到科研。
- 不把用户上传材料或项目记忆默认用于跨项目，必须授权。
- 不把实验建议包装成临床、伦理或监管建议。

## 8. 最终判断

rso-keel 的意义不是今天能多生成几段更好的审稿意见，而是给 RSO 一个能随模型能力增长而增值的核心。

如果未来模型弱，Keel 提供 guardrail、结构化工作流和可恢复执行。

如果未来模型强，Keel 提供动态 workflow 的验证轨道、跨任务知识沉淀和科研责任链。

如果未来大厂平台进入市场，Keel 提供 RSO 的差异化：轻量、学术友好、中文友好、文献/论文/专利/实验建议一体化、可追溯、可回滚、可迁移。

因此，rso-keel 不是一次重构，也不是一个插件。它是 RSO 从“AI 工具”走向“科研操作系统”的龙骨。

## 参考资料

- Microsoft Azure Blog, [Announcing Microsoft Discovery general availability and Microsoft Discovery app preview](https://azure.microsoft.com/en-us/blog/announcing-microsoft-discovery-general-availability-and-microsoft-discovery-app-preview/)
- Microsoft, [Microsoft Discovery](https://discovery.microsoft.com/)
- Nature, [Automating scientific discovery with a multi-agent system](https://www.nature.com/articles/s41586-026-10652-y)
- FutureHouse, [Demonstrating end-to-end scientific discovery with Robin, a multi-agent system](https://www.futurehouse.org/research-announcements/demonstrating-end-to-end-scientific-discovery-with-robin-a-multi-agent-system)
- Nature, [The AI co-scientist and the future of scientific discovery](https://www.nature.com/articles/s41586-026-10644-y)
- Google DeepMind, [Co-Scientist: A multi-agent AI partner to accelerate research](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/)
- Sakana AI, [AI Scientist-v2 arXiv paper](https://arxiv.org/abs/2504.08066)
- Sakana AI, [AI-Scientist-v2 GitHub repository](https://github.com/sakanaai/ai-scientist-v2)
- AgentRxiv, [Towards Collaborative Autonomous Research](https://arxiv.org/html/2503.18102v1)
- ETH Zurich Research Collection, [AgentRxiv: Towards Collaborative Autonomous Research](https://www.research-collection.ethz.ch/items/c71863b9-033e-4c1e-8268-729a211227b8)
- Nature, [Accurate structure prediction of biomolecular interactions with AlphaFold 3](https://www.nature.com/articles/s41586-024-07487-w)
- Isomorphic Labs, [AlphaFold 3 predicts the structure and interactions of all of life’s molecules](https://www.isomorphiclabs.com/articles/alphafold-3-predicts-the-structure-and-interactions-of-all-of-lifes-molecules)
- Anthropic Engineering, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- Anthropic, [Introducing Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8)
- SWE-bench, [SWE-bench benchmark](https://www.swebench.com/)
- METR, [Measuring AI Ability to Complete Long Tasks](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)
- METR, [Time horizon dashboard](https://metr.org/time-horizons/)
- Nature, [AI hallucinations enter scientific publishing](https://www.nature.com/articles/d41586-026-00969-z)
- National Academies, [Foundation Models for Scientific Discovery](https://www.nationalacademies.org/projects/DEPS-BMSA-24-03)
- Daedalus, [Knowledge-Centric AI for Scientific Discovery](https://www.amacad.org/publication/daedalus/knowledge-centric-ai-for-scientific-discovery)
- Google Research, [Accelerating scientific discovery with AI-powered empirical software](https://research.google/blog/accelerating-scientific-discovery-with-ai-powered-empirical-software/)
