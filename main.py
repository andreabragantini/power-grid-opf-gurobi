# -*- coding: utf-8 -*-
"""Repository entrypoint for OPF formulations.

The active default formulation is DC OPF, created through the formulation
registry so additional formulations can be added incrementally.
"""

from src.formulation_registry import create_model


# Backward-compatible alias used by older scripts.
DCOPF = create_model


def run(formulation_name='dc_opf'):
    """Run an OPF formulation and persist simulation artifacts.

    Args:
        formulation_name: Formulation key, defaulting to dc_opf.

    Returns:
        The solved model object with output paths in results.output_paths.
    """
    opf_model = create_model(formulation_name)
    opf_model.optimize()
    opf_model.build_results()
    opf_model.save_outputs()

    return opf_model


if __name__ == '__main__':
    run()