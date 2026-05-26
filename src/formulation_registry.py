"""Formulation registry and factory for OPF models.

This keeps entrypoint logic formulation-agnostic and makes it easy to add
new OPF variants without rewriting orchestration code.
"""

import os

from src.ac_lp_lossless.model import ACLPLosslessModel
from src.dc_opf.model import DCOPFModel


def create_model(formulation_name=None):
    """Create an OPF model instance by formulation key.

    Args:
        formulation_name: Optional explicit formulation key. When omitted,
            the value is read from OPF_FORMULATION and defaults to dc_opf.

    Returns:
        A model object exposing optimize(), build_results(), and build_chart().

    Raises:
        ValueError: When the formulation key is unknown.
        NotImplementedError: For known but not-yet-implemented formulations.
    """
    formulation = (formulation_name or os.getenv('OPF_FORMULATION', 'dc_opf')).strip().lower()

    if formulation == 'dc_opf':
        return DCOPFModel(formulation_name=formulation)

    if formulation == 'ac_lp_lossless':
        return ACLPLosslessModel(formulation_name=formulation)

    if formulation in {
        'ac_lp_losses_p',
        'ac_lp_losses_pq',
        'fbs_opf',
    }:
        raise NotImplementedError(
            'Formulation {0} is reserved in the architecture but not implemented yet.'.format(
                formulation
            )
        )

    raise ValueError('Unknown formulation: {0}'.format(formulation))
