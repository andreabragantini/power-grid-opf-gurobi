"""Dataset loading and harmonization utilities for OPF formulations.

This module converts heterogeneous CSV schemas into a canonical internal
representation used by formulation builders.
"""

import math
import os
from collections import defaultdict

import gurobipy as gb
import pandas as pd

import defaults


def _read_csv_auto(path):
    """Read CSV with automatic delimiter detection (comma/semicolon/tab)."""
    return pd.read_csv(path, sep=None, engine='python')


def _first_existing_column(df, candidates, frame_name, required=True):
    """Return the first column from candidates found in a DataFrame.

    Args:
        df: DataFrame to inspect.
        candidates: Ordered list of acceptable column names.
        frame_name: Human-readable file label for error messages.
        required: Whether to raise if no column is found.

    Returns:
        Matching column name or None when optional and not found.
    """
    for column in candidates:
        if column in df.columns:
            return column
    if required:
        raise ValueError(
            'Missing required column in {0}. Expected one of: {1}'.format(
                frame_name, candidates
            )
        )
    return None


def _read_optional_base_mva():
    """Read BaseMVA from optional other.csv file.

    Returns:
        A float base MVA value. Falls back to defaults.DEFAULT_SBASE.
    """
    if not os.path.exists(defaults.other_file):
        return defaults.DEFAULT_SBASE

    with open(defaults.other_file, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2 and parts[0].lower() == 'basemva':
                return float(parts[1])

    return defaults.DEFAULT_SBASE


def load_network_data(context):
    """Load bus and branch data into canonical network structures.

    The function supports both legacy custom schemas and MATPOWER-style
    exported CSVs by applying column aliases.
    """
    # Re-read environment-driven paths to support multi-case runs in one process.
    defaults.refresh_from_env()

    raw_nodedf = _read_csv_auto(defaults.nodefile)

    node_id_col = _first_existing_column(raw_nodedf, ['ID', 'Bus_Number'], 'buses.csv')
    node_name_col = _first_existing_column(raw_nodedf, ['name', 'Bus_Name'], 'buses.csv', required=False)
    bus_type_col = _first_existing_column(raw_nodedf, ['Bus_Type'], 'buses.csv', required=False)
    p_load_col = _first_existing_column(raw_nodedf, ['load', 'LoadP', 'PD_MW'], 'buses.csv', required=False)
    q_load_col = _first_existing_column(raw_nodedf, ['LoadQ', 'QD_MVar'], 'buses.csv', required=False)
    vmax_col = _first_existing_column(raw_nodedf, ['Vmax'], 'buses.csv', required=False)
    vmin_col = _first_existing_column(raw_nodedf, ['Vmin'], 'buses.csv', required=False)

    nodedf = raw_nodedf.copy()
    nodedf['name'] = nodedf[node_name_col] if node_name_col is not None else nodedf[node_id_col]

    if bus_type_col is None:
        # Standard default: first bus as slack, remaining as PQ.
        nodedf['Bus_Type'] = 1
        if not nodedf.empty:
            nodedf.loc[nodedf.index[0], 'Bus_Type'] = 3

    nodedf['load'] = nodedf[p_load_col] if p_load_col is not None else 0.0
    nodedf['load_q'] = nodedf[q_load_col] if q_load_col is not None else 0.0
    # When a case does not provide explicit voltage limits, use a wide fallback
    # instead of a tight default so the legacy AC LP formulation can remain feasible.
    nodedf['Vmax'] = nodedf[vmax_col] if vmax_col is not None else 2.0
    nodedf['Vmin'] = nodedf[vmin_col] if vmin_col is not None else 0.0

    nodedf = nodedf.rename(columns={node_id_col: 'ID'})
    context.data.nodedf = nodedf.set_index('ID')

    raw_linedf = _read_csv_auto(defaults.linefile)
    from_col = _first_existing_column(raw_linedf, ['fromNode', 'From_Bus'], 'branches.csv')
    to_col = _first_existing_column(raw_linedf, ['toNode', 'To_Bus'], 'branches.csv')
    limit_col = _first_existing_column(raw_linedf, ['limit', 'Alimit', 'RateA_MVA'], 'branches.csv', required=False)
    type_col = _first_existing_column(raw_linedf, ['type'], 'branches.csv', required=False)
    b_col = _first_existing_column(raw_linedf, ['B'], 'branches.csv', required=False)
    g_col = _first_existing_column(raw_linedf, ['G'], 'branches.csv', required=False)
    r_col = _first_existing_column(raw_linedf, ['BR_R_PU'], 'branches.csv', required=False)
    x_col = _first_existing_column(raw_linedf, ['BR_X_PU'], 'branches.csv', required=False)

    linedf = raw_linedf.copy()
    linedf['fromNode'] = linedf[from_col]
    linedf['toNode'] = linedf[to_col]
    linedf['limit'] = linedf[limit_col] if limit_col is not None else gb.GRB.INFINITY
    if type_col is None:
        linedf['type'] = 'AC'

    if b_col is not None:
        linedf['B'] = linedf[b_col]
    elif x_col is not None:
        # For DC OPF we use susceptance approximated as inverse reactance.
        linedf['B'] = linedf[x_col].apply(lambda x: 0.0 if abs(float(x)) < 1e-9 else 1.0 / float(x))
    else:
        raise ValueError('branches.csv requires either B or BR_X_PU column')

    if g_col is not None:
        linedf['G'] = linedf[g_col]
    elif r_col is not None and x_col is not None:
        r_series = pd.to_numeric(linedf[r_col], errors='coerce').fillna(0.0)
        x_series = pd.to_numeric(linedf[x_col], errors='coerce').fillna(0.0)
        denom = (r_series * r_series + x_series * x_series).replace(0.0, pd.NA)
        linedf['G'] = (r_series / denom).fillna(0.0)

        # Use positive susceptance magnitude for the LP linearization terms.
        # This matches the legacy implementation convention used in this repo.
        if b_col is None:
            linedf['B'] = (x_series / denom).fillna(0.0)
    else:
        linedf['G'] = 0.0

    context.data.linedf = linedf.set_index(['fromNode', 'toNode'])

    context.data.nodeorder = context.data.nodedf.index.tolist()
    context.data.lineorder = [tuple(x) for x in context.data.linedf.index]

    context.data.linelimit = context.data.linedf['limit'].to_dict()

    def zero_to_inf(value):
        """Convert zero-ish branch thermal limits to infinity for unconstrained links."""
        return value if value > 0.0001 else gb.GRB.INFINITY

    context.data.linelimit = {k: zero_to_inf(v) for k, v in context.data.linelimit.items()}
    context.data.lineadmittance = context.data.linedf['B'].to_dict()
    context.data.G = context.data.linedf['G'].to_dict()
    context.data.B = context.data.linedf['B'].to_dict()

    context.data.nodes = context.data.nodeorder
    context.data.nodetooutlines = defaultdict(list)
    context.data.nodetoinlines = defaultdict(list)

    for line in context.data.lineorder:
        context.data.nodetooutlines[line[0]].append(line)
        context.data.nodetoinlines[line[1]].append(line)

    slack_candidates = context.data.nodedf[context.data.nodedf['Bus_Type'] == 3].index.tolist()
    context.data.slackbuses = slack_candidates if slack_candidates else [context.data.nodeorder[0]]

    line_types = context.data.linedf['type'].tolist()
    context.data.AC_lines = [line for line, line_type in zip(context.data.lineorder, line_types) if line_type == 'AC']

    context.data.Sbase = _read_optional_base_mva()
    context.data.Aq = math.sqrt(2.0) - 1.0
    context.data.case_name = defaults.CASE_NAME


def load_generator_data(context):
    """Load generator records and build generator-node mappings."""
    raw_gendf = _read_csv_auto(defaults.generatorfile)
    gen_id_col = _first_existing_column(raw_gendf, ['ID'], 'generators.csv', required=False)
    origin_col = _first_existing_column(raw_gendf, ['origin', 'Gen_Bus'], 'generators.csv')
    pmax_col = _first_existing_column(raw_gendf, ['Pmax', 'Pmax_MW'], 'generators.csv')
    pmin_col = _first_existing_column(raw_gendf, ['Pmin', 'Pmin_MW'], 'generators.csv', required=False)
    qmax_col = _first_existing_column(raw_gendf, ['Qmax', 'Qmax_MVar'], 'generators.csv', required=False)
    qmin_col = _first_existing_column(raw_gendf, ['Qmin', 'Qmin_MVar'], 'generators.csv', required=False)
    lincost_col = _first_existing_column(raw_gendf, ['lincost', 'CostCoeff_1'], 'generators.csv', required=False)

    gendf = raw_gendf.copy()
    if gen_id_col is None:
        gendf['ID'] = ['g{0}'.format(i + 1) for i in range(len(gendf))]
        gen_id_col = 'ID'

    gendf['origin'] = gendf[origin_col]
    gendf['capacity'] = gendf[pmax_col]
    gendf['pmin'] = gendf[pmin_col] if pmin_col is not None else 0.0
    gendf['Qmax'] = gendf[qmax_col] if qmax_col is not None else gendf['capacity']
    gendf['Qmin'] = gendf[qmin_col] if qmin_col is not None else -gendf['capacity']
    gendf['lincost'] = gendf[lincost_col] if lincost_col is not None else 0.0

    context.data.generatorinfo = gendf.set_index(gen_id_col)
    context.data.generators = context.data.generatorinfo.index.tolist()

    context.data.Map_N2Gs = defaultdict(list)
    context.data.Map_G2Ns = defaultdict(list)

    for gen, node in context.data.generatorinfo['origin'].items():
        context.data.Map_G2Ns[gen].append(node)
        context.data.Map_N2Gs[node].append(gen)


def load_wind_data(context):
    """Load optional windfarm data and build wind-node mappings."""
    if not os.path.exists(defaults.windfarms_file):
        context.data.windinfo = pd.DataFrame(columns=['origin', 'capacity'])
        context.data.windfarms = []
        context.data.Map_N2Ws = defaultdict(list)
        context.data.Map_W2Ns = defaultdict(list)
        return

    wind_df = _read_csv_auto(defaults.windfarms_file)
    wind_index_col = _first_existing_column(
        wind_df,
        ['ID', 'id', 'name'],
        'windfarms.csv',
        required=False,
    )
    context.data.windinfo = wind_df.set_index(wind_index_col or wind_df.columns[0])
    context.data.windfarms = context.data.windinfo.index.tolist()

    context.data.Map_N2Ws = defaultdict(list)
    context.data.Map_W2Ns = defaultdict(list)

    for wind, node in context.data.windinfo['origin'].items():
        context.data.Map_W2Ns[wind].append(node)
        context.data.Map_N2Ws[node].append(wind)


def load_nodal_demand_data(context):
    """Load nodal demand using bus file fields or legacy load file fallback."""
    scale = defaults.LOAD_SCALER

    if 'load' in context.data.nodedf.columns:
        context.data.load = pd.DataFrame(
            {
                'Load': scale * pd.to_numeric(context.data.nodedf['load'], errors='coerce').fillna(0.0),
                'LoadQ': scale * pd.to_numeric(context.data.nodedf.get('load_q', 0.0), errors='coerce').fillna(0.0),
            },
            index=context.data.nodedf.index,
        )
        return

    if os.path.exists(defaults.load_file):
        context.data.load = _read_csv_auto(defaults.load_file).set_index('Node')
        if 'Load' in context.data.load.columns:
            context.data.load['Load'] = scale * pd.to_numeric(context.data.load['Load'], errors='coerce').fillna(0.0)
        if 'LoadQ' not in context.data.load.columns:
            context.data.load['LoadQ'] = 0.0
        context.data.load['LoadQ'] = scale * pd.to_numeric(context.data.load['LoadQ'], errors='coerce').fillna(0.0)
    else:
        context.data.load = pd.DataFrame({'Load': 0.0, 'LoadQ': 0.0}, index=context.data.nodedf.index)
