"""WorkflowIR to LangGraph compiler tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from keel.compiler import KeelState, compile
from keel.ir.schema import WorkflowIR


def _ir(**overrides: Any) -> WorkflowIR:
    base: dict[str, Any] = {
        "schema_version": "v1",
        "objective": "Compile workflow",
        "nodes": [{"id": "n1", "kind": "workspace_read"}],
        "edges": [],
        "conditional_edges": [],
        "policies": {
            "max_cost_usd": 10.0,
            "allowed_skills": [],
        },
    }
    base.update(overrides)
    return WorkflowIR.model_validate(base)


def test_single_node_compiles() -> None:
    compiled = compile(_ir())

    assert compiled is not None


def test_linear_chain_compiles() -> None:
    ir = _ir(
        nodes=[
            {"id": "workspace_read", "kind": "workspace_read"},
            {"id": "synthesis", "kind": "synthesis"},
            {"id": "report_write", "kind": "report_write"},
        ],
        edges=[
            {"from_node": "workspace_read", "to_node": "synthesis"},
            {"from_node": "synthesis", "to_node": "report_write"},
        ],
    )

    compiled = compile(ir)

    assert compiled is not None


def test_determinism() -> None:
    ir = _ir(
        nodes=[
            {"id": "a", "kind": "workspace_read"},
            {"id": "b", "kind": "synthesis"},
            {"id": "c", "kind": "report_write"},
        ],
        edges=[
            {"from_node": "a", "to_node": "b"},
            {"from_node": "b", "to_node": "c"},
        ],
    )

    first = compile(ir)
    second = compile(ir)

    assert list(first.get_graph().nodes) == list(second.get_graph().nodes)


def test_all_six_node_kinds() -> None:
    ir = _ir(
        nodes=[
            {"id": "workspace_read", "kind": "workspace_read"},
            {"id": "literature_search", "kind": "literature_search"},
            {"id": "independent_critic", "kind": "independent_critic"},
            {"id": "synthesis", "kind": "synthesis"},
            {"id": "human_approval", "kind": "human_approval"},
            {"id": "report_write", "kind": "report_write"},
        ],
        edges=[
            {"from_node": "workspace_read", "to_node": "literature_search"},
            {"from_node": "literature_search", "to_node": "independent_critic"},
            {"from_node": "independent_critic", "to_node": "synthesis"},
            {"from_node": "synthesis", "to_node": "human_approval"},
            {"from_node": "human_approval", "to_node": "report_write"},
        ],
    )

    compiled = compile(ir)

    assert compiled is not None


def test_custom_handler_is_called() -> None:
    called: list[str] = []

    def handler(state: KeelState) -> KeelState:
        called.append("n1")
        return {
            **state,
            "node_outputs": {
                **state.get("node_outputs", {}),
                "n1": {"status": "handled"},
            },
        }

    compiled = compile(_ir(), node_handlers={"n1": handler})
    result = compiled.invoke({"node_outputs": {}})

    assert called == ["n1"]
    assert result["node_outputs"]["n1"] == {"status": "handled"}


def test_stub_handler_used_when_no_handler() -> None:
    compiled = compile(_ir())

    result = compiled.invoke({"node_outputs": {}})

    assert result["node_outputs"]["n1"] == {"status": "stub"}


def test_conditional_edge_routes_correctly() -> None:
    ir = _ir(
        nodes=[
            {"id": "read", "kind": "workspace_read"},
            {"id": "write", "kind": "report_write"},
        ],
        conditional_edges=[
            {
                "from_node": "read",
                "condition_field": "evidence_level",
                "condition_value": "high",
                "to_node": "write",
            }
        ],
    )
    compiled = compile(ir)

    result = compiled.invoke({"node_outputs": {}, "evidence_level": "high"})

    assert result["node_outputs"]["read"] == {"status": "stub"}
    assert result["node_outputs"]["write"] == {"status": "stub"}


def test_import_boundary_still_passes() -> None:
    import keel.compiler

    compiler_dir = Path(keel.compiler.__file__).parent
    imported_modules: list[str] = []
    for source_path in sorted(compiler_dir.glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

    assert not any(name == "app" or name.startswith("app.") for name in imported_modules)
    assert not any(name == "backend" or name.startswith("backend.") for name in imported_modules)
