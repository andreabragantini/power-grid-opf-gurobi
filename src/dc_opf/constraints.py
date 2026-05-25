"""Constraint builders for the DC OPF formulation."""

import math

import gurobipy as gb


def build_power_balance_constraints(context):
    """Enforce nodal active-power balance on every bus."""
    constraints = {}
    var = context.variables

    for node in context.data.nodes:
        constraints[node] = context.model.addConstr(
            gb.quicksum(var.p_wind[w] for w in context.data.Map_N2Ws[node])
            + gb.quicksum(var.p_gen[g] for g in context.data.Map_N2Gs[node])
            == context.data.load.Load[node]
            + gb.quicksum(var.p_line[l] for l in context.data.nodetooutlines[node])
            - gb.quicksum(var.p_line[l] for l in context.data.nodetoinlines[node]),
            name='Power_Balance_OPF({0})'.format(node),
        )

    return constraints


def build_generator_pmax_constraints(context):
    """Apply generator maximum active-power capacity limits."""
    constraints = {}
    variables = context.variables
    generator_data = context.data.generatorinfo

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.p_gen[gen] <= generator_data.capacity[gen],
            name='Pmax_OPF({0})'.format(gen),
        )

    return constraints


def build_generator_pmin_constraints(context):
    """Apply generator minimum active-power limits."""
    constraints = {}
    variables = context.variables

    for gen in context.data.generators:
        constraints[gen] = context.model.addConstr(
            variables.p_gen[gen] >= 0.0,
            name='Pmin_OPF({0})'.format(gen),
        )

    return constraints


def build_wind_capacity_constraints(context):
    """Limit accepted wind production by available wind capacity."""
    constraints = {}
    variables = context.variables
    wind_data = context.data.windinfo

    for wind in context.data.windfarms:
        constraints[wind] = context.model.addConstr(
            variables.p_wind[wind] <= wind_data.capacity[wind],
            name='Wind_Max_OPF({0})'.format(wind),
        )

    return constraints


def build_flow_angle_constraints(context):
    """Link branch active flow to nodal angle differences in DC model."""
    constraints = {}
    variables = context.variables

    for line in context.data.AC_lines:
        from_node, to_node = line
        constraints[line] = context.model.addConstr(
            variables.p_line[line]
            == context.data.Sbase
            * context.data.lineadmittance[line]
            * (variables.theta[from_node] - variables.theta[to_node]),
            name='Line_flow_definition_OPF{0}'.format(line),
        )

    return constraints


def build_flow_limit_constraints(context):
    """Apply upper and lower active-flow limits for each AC branch."""
    variables = context.variables
    upper_constraints = {}
    lower_constraints = {}

    for line in context.data.AC_lines:
        upper_constraints[line] = context.model.addConstr(
            variables.p_line[line] <= context.data.linelimit[line],
            name='Line_flow_upper_limit_AC_OPF{0}'.format(line),
        )
        lower_constraints[line] = context.model.addConstr(
            variables.p_line[line] >= -context.data.linelimit[line],
            name='Line_flow_lower_limit_AC_OPF{0}'.format(line),
        )

    return upper_constraints, lower_constraints


def build_angle_limit_constraints(context):
    """Apply generic angle bounds to all buses for numerical robustness."""
    variables = context.variables
    upper_constraints = {}
    lower_constraints = {}

    for node in context.data.nodes:
        upper_constraints[node] = context.model.addConstr(
            variables.theta[node] <= math.pi,
            name='Angle_lim_upper{0}'.format(node),
        )
        lower_constraints[node] = context.model.addConstr(
            variables.theta[node] >= -math.pi,
            name='Angle_lim_lower{0}'.format(node),
        )

    return lower_constraints, upper_constraints


def build_all_constraints(context):
    """Build and register all DC OPF constraints in a single orchestration call."""
    context.constraints.PowerBalOPF = build_power_balance_constraints(context)
    context.constraints.PmaxOPF = build_generator_pmax_constraints(context)
    context.constraints.PminOPF = build_generator_pmin_constraints(context)
    context.constraints.WindmaxOPF = build_wind_capacity_constraints(context)
    context.constraints.flow_to_angleOPF = build_flow_angle_constraints(context)
    context.constraints.flow_lim_OPF = build_flow_limit_constraints(context)
    context.constraints.angle = build_angle_limit_constraints(context)
