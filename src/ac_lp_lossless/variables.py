"""Decision-variable builders for AC LP lossless OPF."""

import gurobipy as gb


def build_variables(context):
    """Create primal variables for AC LP lossless formulation."""
    model = context.model
    variables = context.variables

    generators = context.data.generators
    windfarms = context.data.windfarms
    nodes = context.data.nodes

    variables.p_gen = {
        gen: model.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='Pgen({0})'.format(gen))
        for gen in generators
    }
    variables.q_gen = {
        gen: model.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='Qgen({0})'.format(gen))
        for gen in generators
    }
    variables.p_wind = {
        wind: model.addVar(lb=0.0, name='Wgen({0})'.format(wind))
        for wind in windfarms
    }
    variables.q_wind = {
        wind: model.addVar(lb=0.0, name='Wgen_q({0})'.format(wind))
        for wind in windfarms
    }

    variables.v = {
        node: model.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='voltage({0})'.format(node))
        for node in nodes
    }
    variables.theta = {
        node: model.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='nodeangle({0})'.format(node))
        for node in nodes
    }

    variables.p_line = {
        line: model.addVar(
            lb=-gb.GRB.INFINITY,
            ub=gb.GRB.INFINITY,
            name='Active_lineflow({0})'.format(line),
        )
        for line in context.data.AC_lines
    }
    variables.q_line = {
        line: model.addVar(
            lb=-gb.GRB.INFINITY,
            ub=gb.GRB.INFINITY,
            name='Reactive_lineflow({0})'.format(line),
        )
        for line in context.data.AC_lines
    }

    model.update()

    for node in context.data.slackbuses:
        variables.theta[node].lb = 0.0
        variables.theta[node].ub = 0.0
        variables.v[node].lb = 1.0
        variables.v[node].ub = 1.0

    # Backward-compatible aliases used by legacy names.
    variables.Pgen = variables.p_gen
    variables.Qgen = variables.q_gen
    variables.Wgen = variables.p_wind
    variables.Wgen_q = variables.q_wind
    variables.voltage = variables.v
    variables.nodeangle = variables.theta
    variables.flow_p = variables.p_line
    variables.flow_q = variables.q_line

    model.update()
