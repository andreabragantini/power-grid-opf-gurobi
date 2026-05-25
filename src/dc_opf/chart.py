"""Network visualization helpers for DC OPF datasets."""

import networkx as nx


def build_network_chart(context):
    """Render a simple topology chart using networkx.

    This utility is intentionally lightweight for quick visual checks.
    """
    graph = nx.Graph()
    graph.add_nodes_from(context.data.nodes)
    graph.add_edges_from(context.data.lineorder)
    nx.draw(graph, with_labels=True)
