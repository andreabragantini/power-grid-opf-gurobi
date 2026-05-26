"""Objective builders for AC LP lossless OPF."""

import gurobipy as gb


def build_objective(context):
    """Minimize linear generation dispatch cost."""
    generators = context.data.generators
    generator_data = context.data.generatorinfo

    context.model.setObjective(
        gb.quicksum(generator_data.lincost[g] * context.variables.p_gen[g] for g in generators),
        gb.GRB.MINIMIZE,
    )
