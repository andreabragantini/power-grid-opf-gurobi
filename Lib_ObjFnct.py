# -*- coding: utf-8 -*-
"""Legacy objective builder wrapper.

The active implementation lives in src.dc_opf.objective.
"""

from src.dc_opf.objective import build_objective as _build_objective


def build_objective_OPF(self):
    """Build DC OPF objective through the modular implementation."""
    _build_objective(self)
        
