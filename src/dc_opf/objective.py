"""Objective builders for DC OPF."""

import gurobipy as gb


def build_objective(context):
    """Set linear generation-cost minimization objective for DC OPF."""
    generators = context.data.generators
    generator_data = context.data.generatorinfo

    context.model.setObjective(
        gb.quicksum(generator_data.lincost[g] * context.variables.Pgen[g] for g in generators),
        gb.GRB.MINIMIZE,
    )
