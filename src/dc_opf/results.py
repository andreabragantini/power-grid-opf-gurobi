"""Result extraction utilities for DC OPF runs."""

import pandas as pd


def build_results(context):
    """Extract optimized values and solver metadata into tabular outputs."""
    generators = context.data.generators
    windfarms = context.data.windfarms
    ac_lines = context.data.AC_lines
    nodes = context.data.nodes

    context.results.Pgen = pd.DataFrame(
        [context.variables.Pgen[g].x for g in generators],
        index=generators,
        columns=['Pgen'],
    )

    context.results.WindOPF = pd.DataFrame(
        [context.variables.WindOPF[w].x for w in windfarms],
        index=windfarms,
        columns=['WindGen'],
    )

    context.results.lineflow_AC_OPF = pd.DataFrame(
        [[context.variables.lineflow_AC_OPF[l].x] for l in ac_lines],
        index=ac_lines,
        columns=['AC_flow'],
    )

    context.results.nodeangle = pd.DataFrame(
        [[context.variables.nodeangle[n].x] for n in nodes],
        index=nodes,
        columns=['Voltage'],
    )

    # Basic run diagnostics useful for reproducibility and benchmark logging.
    context.results.metadata = {
        'status': context.model.Status,
        'objective_value': context.model.ObjVal if context.model.SolCount > 0 else None,
        'num_constraints': context.model.NumConstrs,
        'num_variables': context.model.NumVars,
    }
