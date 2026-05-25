"""Decision-variable builders for DC OPF."""

import gurobipy as gb


def build_variables(context):
    """Create all primal variables needed by the DC OPF formulation.

    Args:
        context: Shared model context containing data and model references.
    """
    model = context.model
    variables = context.variables

    generators = context.data.generators
    windfarms = context.data.windfarms
    nodes = context.data.nodes

    # Dispatchable generator active power.
    variables.Pgen = {
        gen: model.addVar(lb=0.0, name='Pgen({0})'.format(gen))
        for gen in generators
    }

    # Non-dispatchable wind active power accepted by OPF.
    variables.WindOPF = {
        wind: model.addVar(lb=0.0, name='WindOPF({0})'.format(wind))
        for wind in windfarms
    }

    # Nodal voltage angles in DC approximation.
    variables.nodeangle = {
        node: model.addVar(
            lb=-gb.GRB.INFINITY,
            ub=gb.GRB.INFINITY,
            name='nodeangle({0})'.format(node),
        )
        for node in nodes
    }

    model.update()

    # Fix all selected slack buses as angular reference.
    for node in context.data.slackbuses:
        variables.nodeangle[node].lb = 0.0
        variables.nodeangle[node].ub = 0.0

    # Active power flow variable per AC branch.
    variables.lineflow_AC_OPF = {
        line: model.addVar(
            lb=-gb.GRB.INFINITY,
            ub=gb.GRB.INFINITY,
            name='lineflow_AC_OPF({0})'.format(line),
        )
        for line in context.data.AC_lines
    }

    model.update()
