# Quickstart

This example builds a minimal `rso-keel` workflow: create `WorkflowIR`, validate it, run gates, compile it to the current RSO LangGraph runtime, and create a `TemplateSpec`.

## Run From the Package Directory

```powershell
git clone https://github.com/yiouyou/rso-keel.git
cd rso-keel
uv run python -c "import keel; print(keel.__doc__)"
```

Run package tests:

```powershell
uv run pytest
```

## Minimal Example

```python
from keel.compiler import compile as compile_workflow
from keel.convergence import DeterministicGate, RulesGate
from keel.ir import IREdge, IRNode, Policies, WorkflowIR, validate
from keel.policy import build_policy_preflight_report
from keel.templates import TemplateSpec

ir = WorkflowIR(
    schema_version="v1",
    objective="Produce an accountable review report.",
    nodes=[
        IRNode(id="read", kind="workspace_read"),
        IRNode(id="critic", kind="independent_critic", depends_on=["read"]),
        IRNode(id="write", kind="report_write", depends_on=["critic"]),
    ],
    edges=[
        IREdge(from_node="read", to_node="critic"),
        IREdge(from_node="critic", to_node="write"),
    ],
    policies=Policies(
        max_cost_usd=1.0,
        allowed_skills=[],
        network_access="none",
        critic_count=1,
    ),
)

validate(ir)
deterministic = DeterministicGate().check(ir)
rules = RulesGate().check(ir)
preflight = build_policy_preflight_report(ir, deterministic=deterministic, rules=rules)
assert preflight.passed, preflight.model_dump()

graph = compile_workflow(ir)
result = graph.invoke({"node_outputs": {}})

template = TemplateSpec(
    template_id="quickstart",
    version="0.1.0",
    ir_skeleton=ir.model_dump(),
)

print("nodes:", sorted(result["node_outputs"].keys()))
print("template hash:", template.content_hash)
```

## What This Shows

```text
WorkflowIR
  -> validate
  -> DeterministicGate / RulesGate
  -> PolicyPreflightReport
  -> compile to runtime graph
  -> run handlers
  -> TemplateSpec content_hash
```

This example does not show a production host integration. A production host must add auth, project ownership, plan records, durable checkpointing, provenance persistence, artifact storage, HumanGate resume, fallback, rollback, and metrics.
