"""Interactive network plotting helpers for DC OPF datasets."""

import math
import re

import networkx as nx
import pandas as pd
import plotly.graph_objects as go


def _find_col(df, candidates):
    """Return first existing column name from candidate list."""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _to_float(value):
    """Parse numeric values robustly from strings and numbers."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(' ', '').replace("'", '').replace(',', '.')
    text = re.sub(r'[^0-9\.-]', '', text)

    if text.count('.') > 1:
        parts = text.split('.')
        text = parts[0] + '.' + ''.join(parts[1:])

    try:
        return float(text)
    except ValueError:
        return None


def _to_swiss_compact(value):
    """Parse compact Swiss coordinate strings like 6.759.401.370.109.130.

    The parser interprets these values as CH1903 meters with a 6-digit integer
    part and remaining decimal precision.
    """
    text = str(value).strip()
    if not text:
        return None

    digits = re.sub(r'\D', '', text)
    if len(digits) < 6:
        return None

    return float(digits[:6] + '.' + digits[6:])


def _lv03_to_wgs84(east, north):
    """Convert Swiss LV03 coordinates to WGS84 lon/lat."""
    y_aux = (east - 600000.0) / 1000000.0
    x_aux = (north - 200000.0) / 1000000.0

    lat = (
        16.9023892
        + 3.238272 * x_aux
        - 0.270978 * (y_aux ** 2)
        - 0.002528 * (x_aux ** 2)
        - 0.0447 * (y_aux ** 2) * x_aux
        - 0.0140 * (x_aux ** 3)
    )
    lon = (
        2.6779094
        + 4.728982 * y_aux
        + 0.791484 * y_aux * x_aux
        + 0.1306 * y_aux * (x_aux ** 2)
        - 0.0436 * (y_aux ** 3)
    )

    return (lon * 100.0 / 36.0, lat * 100.0 / 36.0)


def _lv95_to_wgs84(east, north):
    """Convert Swiss LV95 coordinates to WGS84 lon/lat."""
    return _lv03_to_wgs84(east - 2000000.0, north - 1000000.0)


def _normalize_coordinate_pair(raw_x, raw_y):
    """Normalize raw coordinate pairs and detect map-compatibility."""
    x_compact = _to_swiss_compact(raw_x)
    y_compact = _to_swiss_compact(raw_y)
    if x_compact is not None and y_compact is not None:
        if 400000.0 <= x_compact <= 900000.0 and 50000.0 <= y_compact <= 400000.0:
            return _lv03_to_wgs84(x_compact, y_compact), True
        if 2400000.0 <= x_compact <= 2900000.0 and 1050000.0 <= y_compact <= 1350000.0:
            return _lv95_to_wgs84(x_compact, y_compact), True

    x = _to_float(raw_x)
    y = _to_float(raw_y)

    if x is None or y is None:
        return None, False

    if -180.0 <= x <= 180.0 and -90.0 <= y <= 90.0:
        return (x, y), True

    if 2400000.0 <= x <= 2900000.0 and 1050000.0 <= y <= 1350000.0:
        return _lv95_to_wgs84(x, y), True

    if 400000.0 <= x <= 900000.0 and 50000.0 <= y <= 400000.0:
        return _lv03_to_wgs84(x, y), True

    return (x, y), False


def _resolve_coordinates(context, graph):
    """Resolve node coordinates from data when possible, otherwise use layout."""
    node_df = context.data.nodedf.copy()

    x_col = _find_col(node_df, ['x', 'X', 'lon', 'longitude', 'Longitude', 'LON', 'lng', 'gis_x', 'GIS_X'])
    y_col = _find_col(node_df, ['y', 'Y', 'lat', 'latitude', 'Latitude', 'LAT', 'gis_y', 'GIS_Y'])

    if x_col and y_col:
        coordinates = {}
        geo_flags = []
        for node in context.data.nodes:
            normalized, is_geo = _normalize_coordinate_pair(node_df.loc[node, x_col], node_df.loc[node, y_col])
            if normalized is None:
                coordinates = {}
                break
            coordinates[node] = normalized
            geo_flags.append(is_geo)

        if len(coordinates) == len(context.data.nodes):
            return coordinates, all(geo_flags)

    return nx.spring_layout(graph, seed=42), False


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


def _build_edge_hover_trace(context, graph, pos, include_flow=False):
    """Create transparent midpoint markers to show line info on hover."""
    lineflow = context.results.lineflow_AC_OPF['AC_flow'].to_dict() if include_flow else {}

    x_mid = []
    y_mid = []
    hover = []

    for start, end in graph.edges():
        x_mid.append((pos[start][0] + pos[end][0]) / 2.0)
        y_mid.append((pos[start][1] + pos[end][1]) / 2.0)

        flow = lineflow.get((start, end), lineflow.get((end, start)))
        if flow is None or pd.isna(flow):
            hover.append('Line: {0} -> {1}'.format(start, end))
        else:
            hover.append('Line: {0} -> {1}<br>Flow [MW]: {2:.3f}'.format(start, end, flow))

    return go.Scatter(
        x=x_mid,
        y=y_mid,
        mode='markers',
        marker={'size': 8, 'opacity': 0.0},
        hovertext=hover,
        hovertemplate='%{hovertext}<extra></extra>',
        showlegend=False,
    )


def _map_center(pos):
    """Compute a map center from node coordinates."""
    values = list(pos.values())
    lon = sum(x for x, _ in values) / len(values)
    lat = sum(y for _, y in values) / len(values)
    return {'lon': lon, 'lat': lat}


def _edge_trace_to_mapbox(edge_trace):
    """Convert XY line trace into mapbox lon/lat line trace."""
    return go.Scattermapbox(
        lon=edge_trace.x,
        lat=edge_trace.y,
        mode='lines',
        line={'width': 1, 'color': '#9aa0a6'},
        hoverinfo='none',
        showlegend=False,
    )


def _edge_hover_to_mapbox(edge_hover_trace):
    """Convert XY transparent edge-hover trace into mapbox trace."""
    return go.Scattermapbox(
        lon=edge_hover_trace.x,
        lat=edge_hover_trace.y,
        mode='markers',
        marker={'size': 8, 'opacity': 0.0},
        hovertext=edge_hover_trace.hovertext,
        hovertemplate='%{hovertext}<extra></extra>',
        showlegend=False,
    )


def build_network_charts(context, output_dir):
    """Build and save two interactive Plotly network charts."""
    graph = nx.Graph()
    graph.add_nodes_from(context.data.nodes)
    graph.add_edges_from(context.data.lineorder)

    pos, use_geo_map = _resolve_coordinates(context, graph)
    role_map = _build_node_role_map(context)
    edge_trace = _build_edge_trace(graph, pos)
    edge_hover_trace = _build_edge_hover_trace(context, graph, pos, include_flow=False)

    asset_path = output_dir / 'network_assets.html'
    heatmap_path = output_dir / 'network_results_heatmap.html'

    _save_asset_plot(context, graph, pos, role_map, edge_trace, edge_hover_trace, asset_path, use_geo_map)
    _save_heatmap_plot(context, graph, pos, role_map, edge_trace, heatmap_path, use_geo_map)

    return {
        'assets_plot': asset_path,
        'heatmap_plot': heatmap_path,
    }


def _save_asset_plot(context, graph, pos, role_map, edge_trace, edge_hover_trace, output_path, use_geo_map):
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
    show_node_labels = len(context.data.nodes) <= 80

    for role in role_order:
        role_nodes = [node for node in graph.nodes() if role_map[node] == role]
        if not role_nodes:
            continue

        mode = 'markers+text' if show_node_labels else 'markers'
        text_values = [str(node) for node in role_nodes]
        if use_geo_map:
            trace = go.Scattermapbox(
                lon=[pos[node][0] for node in role_nodes],
                lat=[pos[node][1] for node in role_nodes],
                mode=mode,
                text=text_values,
                textposition='top center',
                name=role,
                marker={'size': 8, 'color': color_map[role], 'opacity': 0.95},
                hovertemplate='Node: %{text}<br>Role: ' + role + '<extra></extra>',
            )
        else:
            trace = go.Scatter(
                x=[pos[node][0] for node in role_nodes],
                y=[pos[node][1] for node in role_nodes],
                mode=mode,
                text=text_values,
                textposition='top center',
                name=role,
                marker={'size': 10, 'color': color_map[role], 'line': {'width': 0.5, 'color': '#ffffff'}},
                hovertemplate='Node: %{text}<br>Role: ' + role + '<extra></extra>',
            )
        node_traces.append(trace)

    if use_geo_map:
        fig = go.Figure(data=[_edge_trace_to_mapbox(edge_trace), _edge_hover_to_mapbox(edge_hover_trace)] + node_traces)
        fig.update_layout(
            title='Network Connectivity and Asset Roles',
            showlegend=True,
            hovermode='closest',
            mapbox={'style': 'open-street-map', 'zoom': 9, 'center': _map_center(pos)},
            margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
        )
    else:
        fig = go.Figure(data=[edge_trace, edge_hover_trace] + node_traces)
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


def _save_heatmap_plot(context, graph, pos, role_map, edge_trace, output_path, use_geo_map):
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
    show_node_labels = len(context.data.nodes) <= 80
    node_mode = 'markers+text' if show_node_labels else 'markers'

    if use_geo_map:
        edge_hover_geo = _edge_hover_to_mapbox(_build_edge_hover_trace(context, graph, pos, include_flow=True))
        node_trace = go.Scattermapbox(
            lon=[pos[node][0] for node in node_df['node']],
            lat=[pos[node][1] for node in node_df['node']],
            mode=node_mode,
            text=[str(node) for node in node_df['node']],
            textposition='top center',
            marker={
                'size': 9,
                'color': node_df['angle'],
                'colorscale': 'RdYlBu',
                'reversescale': True,
                'colorbar': {'title': 'Voltage Angle [rad]'},
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
        fig = go.Figure(data=[_edge_trace_to_mapbox(edge_trace), edge_hover_geo, node_trace])
        fig.update_layout(
            title='OPF Network Heatmap (Voltage Angle and Generation Dispatch)',
            showlegend=False,
            hovermode='closest',
            mapbox={'style': 'open-street-map', 'zoom': 9, 'center': _map_center(pos)},
            margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
        )
    else:
        node_trace = go.Scatter(
            x=[pos[node][0] for node in node_df['node']],
            y=[pos[node][1] for node in node_df['node']],
            mode=node_mode,
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

        fig = go.Figure(data=[edge_trace, _build_edge_hover_trace(context, graph, pos, include_flow=True), node_trace])
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
