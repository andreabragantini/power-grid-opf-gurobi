# -*- coding: utf-8 -*-
"""Legacy constraint orchestration wrapper.

The active implementation lives in src.dc_opf.constraints.
"""

from src.dc_opf.constraints import build_all_constraints


def _build_constraints_OPF(self):
    """Build all DC OPF constraints through the modular implementation."""
    build_all_constraints(self)