"""Compile WorkflowIR DAGs into LangGraph StateGraph objects."""

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from keel.compiler.state import KeelState
from keel.ir.schema import ConditionalEdge, WorkflowIR

NodeHandler = Callable[[KeelState], KeelState]


def compile(
    ir: WorkflowIR,
    node_handlers: dict[str, NodeHandler] | None = None,
    checkpointer: Any = None,
) -> Any:
    """Compile a WorkflowIR into a LangGraph compiled state graph.

    Args:
        ir:            The validated WorkflowIR to compile.
        node_handlers: Optional dict mapping node_id → handler callable.
                       Missing nodes get a stub handler.
        checkpointer:  Optional LangGraph checkpointer for persisted execution.
    """
    if not ir.nodes:
        raise ValueError("WorkflowIR must contain at least one node.")

    handlers = node_handlers or {}
    graph = StateGraph(KeelState)
    node_ids = [node.id for node in ir.nodes]

    for node_id in node_ids:
        graph.add_node(node_id, handlers.get(node_id, _stub_handler(node_id)))

    for edge in ir.edges:
        graph.add_edge(edge.from_node, edge.to_node)

    for edges in _conditional_edges_by_source(ir):
        graph.add_conditional_edges(
            edges[0].from_node,
            _conditional_router(edges),
            _conditional_path_map(edges),
        )

    graph.set_entry_point(_entry_node(node_ids, ir))

    for node_id in _terminal_nodes(node_ids, ir):
        graph.add_edge(node_id, END)

    return graph.compile(checkpointer=checkpointer)


def _stub_handler(node_id: str) -> NodeHandler:
    def handler(state: KeelState) -> KeelState:
        return {
            **state,
            "node_outputs": {
                **state.get("node_outputs", {}),
                node_id: {"status": "stub"},
            },
        }

    return handler


def _conditional_edges_by_source(ir: WorkflowIR) -> list[list[ConditionalEdge]]:
    groups: list[list[ConditionalEdge]] = []
    sources: list[str] = []
    for edge in ir.conditional_edges:
        if edge.from_node not in sources:
            sources.append(edge.from_node)
            groups.append([])
        groups[sources.index(edge.from_node)].append(edge)
    return groups


def _conditional_router(edges: list[ConditionalEdge]) -> Callable[[KeelState], str]:
    def route(state: KeelState) -> str:
        for edge in edges:
            if state.get(edge.condition_field) == edge.condition_value:
                return str(edge.condition_value)
        return "__default__"

    return route


def _conditional_path_map(edges: list[ConditionalEdge]) -> dict[str, str]:
    path_map: dict[str, str] = {}
    for edge in edges:
        path_map[str(edge.condition_value)] = edge.to_node
    path_map["__default__"] = END
    return path_map


def _entry_node(node_ids: list[str], ir: WorkflowIR) -> str:
    incoming = _incoming_nodes(ir)
    for node_id in node_ids:
        if node_id not in incoming:
            return node_id
    return node_ids[0]


def _incoming_nodes(ir: WorkflowIR) -> list[str]:
    incoming: list[str] = []
    for edge in ir.edges:
        if edge.to_node not in incoming:
            incoming.append(edge.to_node)
    for edge in ir.conditional_edges:
        if edge.to_node not in incoming:
            incoming.append(edge.to_node)
    return incoming


def _terminal_nodes(node_ids: list[str], ir: WorkflowIR) -> list[str]:
    outgoing = _outgoing_nodes(ir)
    return [node_id for node_id in node_ids if node_id not in outgoing]


def _outgoing_nodes(ir: WorkflowIR) -> list[str]:
    outgoing: list[str] = []
    for edge in ir.edges:
        if edge.from_node not in outgoing:
            outgoing.append(edge.from_node)
    for edge in ir.conditional_edges:
        if edge.from_node not in outgoing:
            outgoing.append(edge.from_node)
    return outgoing
