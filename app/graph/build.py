from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    compute_hash_node,
    empty_digest_node,
    extract_map_node,
    fetch_messages_node,
    format_node,
    persist_node,
    preprocess_node,
    publish_node,
    reduce_dedupe_node,
    route_empty,
    validate_node,
)
from app.graph.state import DigestState


def build_graph():
    graph = StateGraph(DigestState)

    graph.add_node("fetch_messages", fetch_messages_node)
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("extract_map", extract_map_node)
    graph.add_node("reduce_dedupe", reduce_dedupe_node)
    graph.add_node("validate", validate_node)
    graph.add_node("empty_digest", empty_digest_node)
    graph.add_node("format", format_node)
    graph.add_node("compute_hash", compute_hash_node)
    graph.add_node("publish", publish_node)
    graph.add_node("persist", persist_node)

    graph.set_entry_point("fetch_messages")
    graph.add_conditional_edges(
        "fetch_messages",
        route_empty,
        {"empty": "empty_digest", "non_empty": "preprocess"},
    )

    graph.add_edge("preprocess", "extract_map")
    graph.add_edge("extract_map", "reduce_dedupe")
    graph.add_edge("reduce_dedupe", "validate")
    graph.add_edge("validate", "format")
    graph.add_edge("empty_digest", "format")
    graph.add_edge("format", "compute_hash")
    graph.add_edge("compute_hash", "publish")
    graph.add_edge("publish", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
