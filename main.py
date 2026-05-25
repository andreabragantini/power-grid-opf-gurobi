# -*- coding: utf-8 -*-
"""Repository entrypoint for OPF formulations.

The active default formulation is DC OPF, created through the formulation
registry so additional formulations can be added incrementally.
"""

from tabulate import tabulate

from src.formulation_registry import create_model


# Backward-compatible alias used by older scripts.
DCOPF = create_model


def run(formulation_name='dc_opf', build_chart=True):
    """Run an OPF formulation and print standard result tables.

    Args:
        formulation_name: Formulation key, defaulting to dc_opf.
        build_chart: Whether to produce a topology chart after solving.

    Returns:
        The solved model object.
    """
    opf_model = create_model(formulation_name)
    opf_model.optimize()
    opf_model.build_results()

    if build_chart:
        opf_model.build_chart()

    print('##############################')
    print('#####  OPF Formulation Results #####')
    print('##############################')

    print(tabulate(opf_model.results.Pgen, headers='keys', tablefmt='psql'))
    print(tabulate(opf_model.results.WindOPF, headers='keys', tablefmt='psql'))
    print(tabulate(opf_model.results.lineflow_AC_OPF, headers='keys', tablefmt='psql'))
    print(tabulate(opf_model.results.nodeangle, headers='keys', tablefmt='psql'))

    return opf_model


if __name__ == '__main__':
    run()