"""Constraint builders for AC LP lossless OPF formulation."""

import math

import gurobipy as gb


def build_active_power_balance_constraints(context):
    """Enforce nodal active-power balance."""
    constraints = {}
    var = context.variables

    for node in context.data.nodes:
        constraints[node] = context.model.addConstr(
            gb.quicksum(var.p_wind[w] for w in context.data.Map_N2Ws[node])
            + gb.quicksum(var.p_gen[g] for g in context.data.Map_N2Gs[node])
            == context.data.load['Load'][node]
            + gb.quicksum(var.p_line[l] for l in context.data.nodetooutlines[node])
            - gb.quicksum(var.p_line[l] for l in context.data.nodetoinlines[node]),
            name='ActivePower_Balance_OPF({0})'.format(node),
        )

    return constraints


def build_reactive_power_balance_constraints(context):
    """Enforce nodal reactive-power balance."""
    constraints = {}
    var = context.variables

    for node in context.data.nodes:
        constraints[node] = context.model.addConstr(
            gb.quicksum(var.q_wind[w] for w in context.data.Map_N2Ws[node])
            + gb.quicksum(var.q_gen[g] for g in context.data.Map_N2Gs[node])
            == context.data.load['LoadQ'][node]
            + gb.quicksum(var.q_line[l] for l in context.data.nodetooutlines[node])
            - gb.quicksum(var.q_line[l] for l in context.data.nodetoinlines[node]),
            name='ReactivePower_Balance_OPF({0})'.format(node),
        )

    return constraints


def build_generator_pmax_constraints(context):
    """Apply generator active-power upper bounds."""
    constraints = {}
    generator_data = context.data.generatorinfo
    variables = context.variables

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.p_gen[gen] <= generator_data.capacity[gen],
            name='Pmax_OPF({0})'.format(gen),
        )

    return constraints


def build_generator_pmin_constraints(context):
    """Apply generator active-power lower bounds."""
    constraints = {}
    generator_data = context.data.generatorinfo
    variables = context.variables

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.p_gen[gen] >= generator_data.pmin[gen],
            name='Pmin_OPF({0})'.format(gen),
        )

    return constraints


def build_generator_qmax_constraints(context):
    """Apply generator reactive-power upper bounds."""
    constraints = {}
    generator_data = context.data.generatorinfo
    variables = context.variables

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.q_gen[gen] <= generator_data.Qmax[gen],
            name='Qmax_OPF({0})'.format(gen),
        )

    return constraints


def build_generator_qmin_constraints(context):
    """Apply generator reactive-power lower bounds."""
    constraints = {}
    generator_data = context.data.generatorinfo
    variables = context.variables

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.q_gen[gen] >= generator_data.Qmin[gen],
            name='Qmin_OPF({0})'.format(gen),
        )

    return constraints


def build_wind_capacity_constraints(context):
    """Limit accepted wind active power by available capacity."""
    constraints = {}
    variables = context.variables
    wind_data = context.data.windinfo

    for wind in context.data.windfarms:
        constraints[wind] = context.model.addConstr(
            variables.p_wind[wind] <= wind_data.capacity[wind],
            name='Wind_Max_OPF({0})'.format(wind),
        )

    return constraints


def build_wind_reactive_constraints(context):
    """Link wind reactive power to active power with fixed power factor."""
    constraints = {}
    variables = context.variables
    fixed_pf = 0.95
    tan_phi = math.tan(math.acos(fixed_pf))

    for wind in context.data.windfarms:
        constraints[wind] = context.model.addConstr(
            variables.q_wind[wind] == tan_phi * variables.p_wind[wind],
            name='Wind_Reactive_def_OPF({0})'.format(wind),
        )

    return constraints


def build_active_flow_definition_constraints(context):
    """Define active line flow from the legacy linearized AC equations."""
    constraints = {}
    variables = context.variables

    for line in context.data.AC_lines:
        from_node, to_node = line
        constraints[line] = context.model.addConstr(
            variables.p_line[line]
            == context.data.Sbase
            * (
                -context.data.B[line] * (variables.theta[from_node] - variables.theta[to_node])
                + context.data.G[line] * (variables.v[from_node] - variables.v[to_node])
            ),
            name='Active_Powerflow_definition_OPF{0}'.format(line),
        )

    return constraints


def build_reactive_flow_definition_constraints(context):
    """Define reactive line flow from the legacy linearized AC equations."""
    constraints = {}
    variables = context.variables

    for line in context.data.AC_lines:
        from_node, to_node = line
        constraints[line] = context.model.addConstr(
            variables.q_line[line]
            == context.data.Sbase
            * (
                -context.data.B[line] * (variables.v[from_node] - variables.v[to_node])
                - context.data.G[line] * (variables.theta[from_node] - variables.theta[to_node])
            ),
            name='Reactive_Powerflow_definition_OPF{0}'.format(line),
        )

    return constraints


def build_octagonal_flow_limit_constraints(context):
    """Apply convex octagonal approximation to apparent flow limits."""
    var = context.variables
    aq = context.data.Aq

    p1_upper = {}
    p1_lower = {}
    p2_upper = {}
    p2_lower = {}
    q1_upper = {}
    q1_lower = {}
    q2_upper = {}
    q2_lower = {}

    for line in context.data.AC_lines:
        p1_upper[line] = context.model.addConstr(
            var.p_line[line] - aq * var.q_line[line] <= context.data.linelimit[line],
            name='Octagonal_flowlimit1_AC_OPF{0}'.format(line),
        )
        p1_lower[line] = context.model.addConstr(
            var.p_line[line] - aq * var.q_line[line] >= -context.data.linelimit[line],
            name='Octagonal_flowlimit2_AC_OPF{0}'.format(line),
        )

        p2_upper[line] = context.model.addConstr(
            var.p_line[line] + aq * var.q_line[line] <= context.data.linelimit[line],
            name='Octagonal_flowlimit3_AC_OPF{0}'.format(line),
        )
        p2_lower[line] = context.model.addConstr(
            var.p_line[line] + aq * var.q_line[line] >= -context.data.linelimit[line],
            name='Octagonal_flowlimit4_AC_OPF{0}'.format(line),
        )

        q1_upper[line] = context.model.addConstr(
            aq * var.p_line[line] - var.q_line[line] <= context.data.linelimit[line],
            name='Octagonal_flowlimit5_AC_OPF{0}'.format(line),
        )
        q1_lower[line] = context.model.addConstr(
            aq * var.p_line[line] - var.q_line[line] >= -context.data.linelimit[line],
            name='Octagonal_flowlimit6_AC_OPF{0}'.format(line),
        )

        q2_upper[line] = context.model.addConstr(
            aq * var.p_line[line] + var.q_line[line] <= context.data.linelimit[line],
            name='Octagonal_flowlimit7_AC_OPF{0}'.format(line),
        )
        q2_lower[line] = context.model.addConstr(
            aq * var.p_line[line] + var.q_line[line] >= -context.data.linelimit[line],
            name='Octagonal_flowlimit8_AC_OPF{0}'.format(line),
        )

    return p1_upper, p1_lower, p2_upper, p2_lower, q1_upper, q1_lower, q2_upper, q2_lower


def build_angle_limit_constraints(context):
    """Apply broad angle bounds for numerical robustness."""
    lower_constraints = {}
    upper_constraints = {}

    for node in context.data.nodes:
        upper_constraints[node] = context.model.addConstr(
            context.variables.theta[node] <= math.pi,
            name='Angle_lim_upper{0}'.format(node),
        )
        lower_constraints[node] = context.model.addConstr(
            context.variables.theta[node] >= -math.pi,
            name='Angle_lim_lower{0}'.format(node),
        )

    return lower_constraints, upper_constraints


def build_voltage_limit_constraints(context):
    """Apply nodal voltage magnitude bounds from bus data."""
    lower_constraints = {}
    upper_constraints = {}
    nodedata = context.data.nodedf

    for node in context.data.nodes:
        upper_constraints[node] = context.model.addConstr(
            context.variables.v[node] <= nodedata['Vmax'][node],
            name='Voltage_lim_upper{0}'.format(node),
        )
        lower_constraints[node] = context.model.addConstr(
            context.variables.v[node] >= nodedata['Vmin'][node],
            name='Voltage_lim_lower{0}'.format(node),
        )

    return lower_constraints, upper_constraints


def build_all_constraints(context):
    """Build and register all AC LP lossless constraints."""
    context.constraints.ActPowerBalOPF = build_active_power_balance_constraints(context)
    context.constraints.ReactPowerBalOPF = build_reactive_power_balance_constraints(context)

    context.constraints.PmaxOPF = build_generator_pmax_constraints(context)
    context.constraints.PminOPF = build_generator_pmin_constraints(context)
    context.constraints.QmaxOPF = build_generator_qmax_constraints(context)
    context.constraints.QminOPF = build_generator_qmin_constraints(context)

    context.constraints.WindmaxOPF = build_wind_capacity_constraints(context)
    context.constraints.WindQ = build_wind_reactive_constraints(context)

    context.constraints.Pflows = build_active_flow_definition_constraints(context)
    context.constraints.Qflows = build_reactive_flow_definition_constraints(context)
    context.constraints.polygonalFlowconstr = build_octagonal_flow_limit_constraints(context)

    context.constraints.voltage = build_voltage_limit_constraints(context)
    context.constraints.angle = build_angle_limit_constraints(context)
