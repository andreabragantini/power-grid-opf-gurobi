"""Interactive network plotting helpers for DC OPF datasets."""

import networkx as nx
import pandas as pd
import plotly.graph_objects as go


def _resolve_coordinates(context, graph):
    """Resolve node coordinates from data when possible, otherwise use layout."""
    node_df = context.data.nodedf.copy()

    x_col = _find_col(node_df, ['x', 'X', 'lon', 'longitude', 'Longitude', 'LON', 'lng'])
    y_col = _find_col(node_df, ['y', 'Y', 'lat', 'latitude', 'Latitude', 'LAT'])

    if x_col and y_col:
        return {
            node: (float(node_df.loc[node, x_col]), float(node_df.loc[node, y_col]))
            for node in context.data.nodes
        }

    # Fallback: deterministic spring layout gives an ordered, readable topology.
    return nx.spring_layout(graph, seed=42)


def _find_col(df, candidates):
    """Return first existing column name from candidate list."""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _build_node_role_map(context):
    """Classify each node role to improve visual readability."""
    role_map = {}

    gen_nodes = {node for node, gens in context.data.Map_N2Gs.items() if gens}
    wind_nodes = {node for node, winds in context.data.Map_N2Ws.items() if winds}
    slack_nodes = set(context.data.slackbuses)
    load_nodes = set(context.data.nodedf[context.data.nodedf['load'] > 0].index.tolist())

    for node in context.data.nodes:
        if node in slack_nodes:
            role_map[node] = 'Slack'
        elif node in gen_nodes and node in wind_nodes:
            role_map[node] = 'Gen+Wind'
        elif node in gen_nodes:
            role_map[node] = 'Generator'
        elif node in wind_nodes:
            role_map[node] = 'Wind'
        elif node in load_nodes:
            role_map[node] = 'Load'
        else:
            role_map[node] = 'Transit'

    return role_map


def _build_edge_trace(graph, pos):
    """Create line trace for network edges."""
    x_edge = []
    y_edge = []
    for start, end in graph.edges():
        x_edge.extend([pos[start][0], pos[end][0], None])
        y_edge.extend([pos[start][1], pos[end][1], None])

    return go.Scatter(
        x=x_edge,
        y=y_edge,
        line={'width': 1, 'color': '#9aa0a6'},
        hoverinfo='none',
        mode='lines',
        showlegend=False,
    )


def build_network_charts(context, output_dir):
    """Build and save two interactive Plotly network charts.

    1) Asset/connectivity map with role-based node colors.
    2) OPF result heatmap using node voltage-angle values with generator hover data.

    Args:
        context: Solved model context containing data and results.
        output_dir: Directory where HTML plots are stored.

    Returns:
        Dictionary with generated plot file paths.
    """
    graph = nx.Graph()
    graph.add_nodes_from(context.data.nodes)
    graph.add_edges_from(context.data.lineorder)

    pos = _resolve_coordinates(context, graph)
    role_map = _build_node_role_map(context)
    edge_trace = _build_edge_trace(graph, pos)

    asset_path = output_dir / 'network_assets.html'
    heatmap_path = output_dir / 'network_results_heatmap.html'

    _save_asset_plot(context, graph, pos, role_map, edge_trace, asset_path)
    _save_heatmap_plot(context, graph, pos, role_map, edge_trace, heatmap_path)

    return {
        'assets_plot': asset_path,
        'heatmap_plot': heatmap_path,
    }


def _save_asset_plot(context, graph, pos, role_map, edge_trace, output_path):
    """Create and save the asset/connectivity network plot."""
    color_map = {
        'Slack': '#d62728',
        'Gen+Wind': '#1f77b4',
        'Generator': '#2ca02c',
        'Wind': '#17becf',
        'Load': '#ff7f0e',
        'Transit': '#7f7f7f',
    }

    role_order = ['Slack', 'Gen+Wind', 'Generator', 'Wind', 'Load', 'Transit']
    node_traces = []

    for role in role_order:
        role_nodes = [node for node in graph.nodes() if role_map[node] == role]
        if not role_nodes:
            continue

        node_traces.append(
            go.Scatter(
                x=[pos[node][0] for node in role_nodes],
                y=[pos[node][1] for node in role_nodes],
                mode='markers+text',
                text=[str(node) for node in role_nodes],
                textposition='top center',
                name=role,
                marker={
                    'size': 10,
                    'color': color_map[role],
                    'line': {'width': 0.5, 'color': '#ffffff'},
                },
                hovertemplate='Node: %{text}<br>Role: ' + role + '<extra></extra>',
            )
        )

    fig = go.Figure(data=[edge_trace] + node_traces)
    fig.update_layout(
        title='Network Connectivity and Asset Roles',
        showlegend=True,
        hovermode='closest',
        template='plotly_white',
        xaxis={'visible': False},
        yaxis={'visible': False},
        margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
    )
    fig.write_html(str(output_path), include_plotlyjs='cdn')


def _save_heatmap_plot(context, graph, pos, role_map, edge_trace, output_path):
    """Create and save heatmap-style OPF result plot with enriched hover data."""
    angle_series = context.results.nodeangle['Voltage']

    node_df = pd.DataFrame({'node': context.data.nodes})
    node_df['angle'] = node_df['node'].map(angle_series.to_dict())
    node_df['load_mw'] = node_df['node'].map(context.data.load['Load'].to_dict()).fillna(0.0)

    dispatch = context.results.Pgen['Pgen'].to_dict()
    node_df['gen_mw'] = node_df['node'].apply(
        lambda n: sum(dispatch.get(g, 0.0) for g in context.data.Map_N2Gs.get(n, []))
    )

    node_df['role'] = node_df['node'].map(role_map)

    node_trace = go.Scatter(
        x=[pos[node][0] for node in node_df['node']],
        y=[pos[node][1] for node in node_df['node']],
        mode='markers+text',
        text=[str(node) for node in node_df['node']],
        textposition='top center',
        marker={
            'size': 11,
            'color': node_df['angle'],
            'colorscale': 'RdYlBu',
            'reversescale': True,
            'colorbar': {'title': 'Voltage Angle [rad]'},
            'line': {'width': 0.5, 'color': '#ffffff'},
        },
        customdata=node_df[['role', 'angle', 'gen_mw', 'load_mw']].values,
        hovertemplate=(
            'Node: %{text}<br>'
            'Role: %{customdata[0]}<br>'
            'Voltage angle [rad]: %{customdata[1]:.4f}<br>'
            'Activated generation [MW]: %{customdata[2]:.3f}<br>'
            'Load [MW]: %{customdata[3]:.3f}<extra></extra>'
        ),
        name='Node OPF state',
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title='OPF Network Heatmap (Voltage Angle and Generation Dispatch)',
        showlegend=False,
        hovermode='closest',
        template='plotly_white',
        xaxis={'visible': False},
        yaxis={'visible': False},
        margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
    )
    fig.write_html(str(output_path), include_plotlyjs='cdn')
