# Quickstart：15 分钟理解 rso-keel 的最小闭环

日期：2026-06-11

本文展示一个最小 `rso-keel` workflow：构造 `WorkflowIR`，执行 validation 和 gates，编译为当前 RSO 使用的 LangGraph graph，运行 stub handlers，生成 `TemplateSpec`。

当前 `rso-keel` 仍在 RSO monorepo 内，以 editable package 使用。未来开源发布后，安装命令可以替换为 `pip install rso-keel` 或公开包名。

## 1. 准备环境

在包目录运行：

```powershell
git clone https://github.com/yiouyou/rso-keel.git
cd rso-keel
cd rso-keel
uv run python -c "import keel; print(keel.__doc__)"
```

也可以跑包测试：

```powershell
uv run pytest
```

## 2. 最小例子

创建临时文件 `examples/keel_quickstart.py`，或直接在 Python REPL 中运行：

```python
from keel.compiler import compile as compile_workflow
from keel.convergence import DeterministicGate, RulesGate
from keel.ir import IREdge, IRNode, Policies, WorkflowIR, validate
from keel.policy import build_policy_preflight_report
from keel.templates import TemplateSpec


ir = WorkflowIR(
    schema_version="v1",
    objective="Review a vendor policy memo and produce an accountable summary.",
    nodes=[
        IRNode(
            id="read_workspace",
            kind="workspace_read",
            inputs={"artifact_type": "policy_memo"},
            budget={"cost_usd": 0.05},
        ),
        IRNode(
            id="critic",
            kind="independent_critic",
            depends_on=["read_workspace"],
            inputs={"focus": "unsupported claims and missing evidence"},
            budget={"cost_usd": 0.1},
        ),
        IRNode(
            id="write_report",
            kind="report_write",
            depends_on=["critic"],
            inputs={"format": "markdown"},
            budget={"cost_usd": 0.05},
        ),
    ],
    edges=[
        IREdge(from_node="read_workspace", to_node="critic"),
        IREdge(from_node="critic", to_node="write_report"),
    ],
    policies=Policies(
        max_cost_usd=1.0,
        allowed_skills=["workspace_reader", "critic", "report_writer"],
        network_access="none",
        requires_human_approval=False,
        critic_count=1,
    ),
)

validate(ir)

deterministic = DeterministicGate().check(ir)
rules = RulesGate().check(ir)
preflight = build_policy_preflight_report(
    ir,
    deterministic=deterministic,
    rules=rules,
)
assert preflight.passed, preflight.model_dump()


def read_workspace(state):
    return {
        **state,
        "node_outputs": {
            **state.get("node_outputs", {}),
            "read_workspace": {
                "summary": "Loaded policy memo v1.",
                "tokens_in": 0,
                "tokens_out": 0,
            },
        },
    }


def critic(state):
    return {
        **state,
        "node_outputs": {
            **state.get("node_outputs", {}),
            "critic": {
                "summary": "Found one unsupported claim.",
                "warnings": ["missing source for retention policy"],
                "tokens_in": 120,
                "tokens_out": 60,
            },
        },
    }


def write_report(state):
    return {
        **state,
        "node_outputs": {
            **state.get("node_outputs", {}),
            "write_report": {
                "summary": "Generated accountable review report.",
                "generated_files": [{"path": "out/vendor-policy-review.md"}],
                "tokens_in": 80,
                "tokens_out": 160,
            },
        },
    }


graph = compile_workflow(
    ir,
    node_handlers={
        "read_workspace": read_workspace,
        "critic": critic,
        "write_report": write_report,
    },
)

result = graph.invoke({"node_outputs": {}})

template = TemplateSpec(
    template_id="vendor-policy-review",
    version="0.1.0",
    description="Minimal accountable policy review workflow.",
    ir_skeleton=ir.model_dump(),
    tags=["quickstart", "review"],
)

print("WorkflowIR validated")
print("Preflight passed:", preflight.passed)
print("Node outputs:", sorted(result["node_outputs"].keys()))
print("Template hash:", template.content_hash)
```

运行：

```powershell
cd rso-keel
uv run python examples/keel_quickstart.py
```

预期输出类似：

```text
WorkflowIR validated
Preflight passed: True
Node outputs: ['critic', 'read_workspace', 'write_report']
Template hash: <sha256>
```

## 3. 这个例子展示了什么

它展示 `rso-keel` 的最小闭环：

```text
WorkflowIR
  -> validate
  -> DeterministicGate / RulesGate
  -> PolicyPreflightReport
  -> compile to LangGraph
  -> run node handlers
  -> TemplateSpec content_hash
```

即使没有真实 LLM，这个例子也说明 `rso-keel` 的核心价值不在“生成内容”，而在“让 workflow 可校验、可执行、可沉淀”。

## 4. 下一步：加入 HumanGate

如果 workflow 会发布正式结论或触发高风险动作，把 `requires_human_approval=True`，并加入 `human_approval` node。

示意：

```python
IRNode(
    id="human_review",
    kind="human_approval",
    depends_on=["critic"],
    inputs={"approver_role": "reviewer"},
)
```

然后让 `write_report` 依赖 `human_review`。

在生产系统里，HumanGate 需要宿主平台提供：

- approval UI。
- plan record。
- owner/project 校验。
- resume API。
- checkpoint persistence。

## 5. 下一步：接入真实 handler

真实 handler 应该把内部结果转换为 `HandlerOutput`：

```python
from keel.handlers import GeneratedFileRef, HandlerOutput, ModelUsage

output = HandlerOutput(
    summary="Generated accountable review report.",
    generated_files=[
        GeneratedFileRef(path="out/vendor-policy-review.md"),
    ],
    warnings=["missing source for retention policy"],
    next_step="Ask legal reviewer to approve or request revision.",
    tokens_in=200,
    tokens_out=220,
    model_usage=[
        ModelUsage(model="example-model", tokens_in=200, tokens_out=220),
    ],
)
```

宿主平台再负责把这些字段写入 job result、billing、generated files 和 provenance。

## 6. 最小生产化清单

从 quickstart 到生产，至少补齐：

- server-side domain payload -> `WorkflowIR` adapter。
- user/project/source ownership 校验。
- registered handler map。
- persistent checkpointer。
- `PlanProvenance` 持久化。
- `WorkflowTemplate` registry。
- HumanGate resume。
- fallback / rollback。
- metrics。
- tests for validation failure, missing HumanGate, forbidden skill, resume owner, fallback provenance。

不要把 quickstart 的内存 graph 当生产架构。它只展示 `rso-keel` 的核心 contract。
