"""Result extraction utilities for DC OPF runs."""

import pandas as pd


STATUS_LABELS = {
    2: 'Converged (Optimal)',
    3: 'Not Converged (Infeasible)',
    4: 'Not Converged (Infeasible or Unbounded)',
    5: 'Not Converged (Unbounded)',
    9: 'Stopped (Time Limit)',
    11: 'Stopped (Interrupted)',
}


def build_results(context):
    """Extract optimized values and solver metadata into tabular outputs."""
    generators = context.data.generators
    windfarms = context.data.windfarms
    ac_lines = context.data.AC_lines
    nodes = context.data.nodes
    has_solution = context.model.SolCount > 0
    status_code = context.model.Status

    total_load_mw = float(context.data.load['Load'].sum()) if hasattr(context.data, 'load') else 0.0
    total_capacity_mw = float(context.data.generatorinfo['capacity'].sum()) if hasattr(context.data, 'generatorinfo') else 0.0
    capacity_margin_mw = total_capacity_mw - total_load_mw

    likely_issue = None
    if status_code == 3 and capacity_margin_mw < 0:
        likely_issue = (
            'Generation capacity shortfall: demand exceeds available generator capacity by '
            '{0:.3f} MW.'.format(abs(capacity_margin_mw))
        )

    def _value_or_nan(var):
        """Return variable value when solution exists, otherwise NaN."""
        return var.X if has_solution else float('nan')

    context.results.p_gen = pd.DataFrame(
        [_value_or_nan(context.variables.p_gen[g]) for g in generators],
        index=generators,
        columns=['p_gen_mw'],
    )

    context.results.p_wind = pd.DataFrame(
        [_value_or_nan(context.variables.p_wind[w]) for w in windfarms],
        index=windfarms,
        columns=['p_wind_mw'],
    )

    context.results.p_line = pd.DataFrame(
        [[_value_or_nan(context.variables.p_line[l])] for l in ac_lines],
        index=ac_lines,
        columns=['p_line_mw'],
    )

    context.results.theta = pd.DataFrame(
        [[_value_or_nan(context.variables.theta[n])] for n in nodes],
        index=nodes,
        columns=['theta_rad'],
    )

    # Backward-compatible aliases used by earlier reporting code.
    context.results.Pgen = context.results.p_gen.rename(columns={'p_gen_mw': 'Pgen'})
    context.results.WindOPF = context.results.p_wind.rename(columns={'p_wind_mw': 'WindGen'})
    context.results.lineflow_AC_OPF = context.results.p_line.rename(columns={'p_line_mw': 'AC_flow'})
    context.results.nodeangle = context.results.theta.rename(columns={'theta_rad': 'Voltage'})

    # Basic run diagnostics useful for reproducibility and benchmark logging.
    context.results.metadata = {
        'status': status_code,
        'status_label': STATUS_LABELS.get(status_code, 'Status {0}'.format(status_code)),
        'converged': status_code == 2,
        'objective_value': context.model.ObjVal if has_solution else None,
        'num_constraints': context.model.NumConstrs,
        'num_variables': context.model.NumVars,
        'has_solution': has_solution,
        'total_load_mw': total_load_mw,
        'total_generation_capacity_mw': total_capacity_mw,
        'capacity_margin_mw': capacity_margin_mw,
        'likely_issue': likely_issue,
    }
